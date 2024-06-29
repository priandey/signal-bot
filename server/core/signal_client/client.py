import logging
from datetime import datetime
import re
from uuid import uuid4
from typing import Any, Collection, Dict, List, Optional, Tuple

import requests
from django.conf import settings
from django.db.transaction import atomic
from django.utils import timezone

from core.models.signal_group import SignalGroup
from core.models.signal_message import SignalMessage
from core.models.signal_user import SignalUser
from core.signal_client.utils import utf16_len

logger = logging.getLogger("SignalClient")

STYLE_CHAR = {
    "*": "ITALIC",
    "#": "BOLD",
    "~": "STRIKETHROUGH",
    "|": "SPOILER",
    "_": "MONOSPACE",
}


class SignalClient:
    def __init__(self, signal_user: SignalUser):
        self.url: str = settings.SIGNAL_URL.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        accounts_request = requests.post(
            self.url + "/api/v1/rpc",
            timeout=settings.REQUESTS_TIMEOUT_SECONDS,
            json={
                "jsonrpc": "2.0",
                "method": "listAccounts",
                "id": str(uuid4())
            }
        )
        accounts_request.raise_for_status()
        remote_registered_accounts = [
            account["number"]
            for account in accounts_request.json()["result"]
        ]
        if signal_user.source_number not in remote_registered_accounts:
            raise ValueError("Provided user is not registered in the signal client")

        if not signal_user.is_registered:
            signal_user.is_registered = True
            signal_user.save(update_fields=["can_send_message"])

        self.user = signal_user

    def receive_messages(self) -> Collection[SignalMessage]:
        raise NotImplementedError("")
        response = requests.get(
            self.url + "/v1/receive/" + self.user.source_number,
            params={
                "send_read_receipts": "false",
            },
            timeout=settings.REQUESTS_TIMEOUT_SECONDS,
            headers=self.headers,
        )
        response.raise_for_status()

        respons_data: List[Dict[str, Any]] = response.json()
        user_infos: Dict[str, Dict[str, Any]] = dict()

        if len(respons_data) > 0:
            with atomic():
                messages_to_create: List[SignalMessage] = []
                for item in respons_data:
                    envelope = item.get("envelope")
                    if envelope is None or "dataMessage" not in envelope.keys():
                        logger.info(
                            "Received a non-data message",
                            extra=item,
                        )
                        continue
                    message: Dict[str, Any] = envelope["dataMessage"]
                    messages_to_create.append(
                        SignalMessage(
                            target_group_id=message.get("groupInfo", {}).get("groupId"),
                            target_user_id=self.user,
                            source_user=envelope["sourceNumber"],
                            text_content=message["message"],
                            raw_content=item,
                            received_at=datetime.fromtimestamp(message["timestamp"] / 1000, timezone.utc),
                            is_incoming=True,
                        )
                    )

                    user_infos.setdefault(
                        envelope["sourceNumber"],
                        {
                            "source_name": envelope["sourceName"],
                            "display_name": envelope["sourceName"],
                            "is_registered": False,
                        }
                    )

                signal_users_numbers = set(
                    SignalUser.objects.filter(
                        source_number__in=user_infos.keys(),
                    ).values_list(
                        "source_number",
                        flat=True,
                    )
                )
                user_numbers_to_create = set(user_infos.keys()).difference(signal_users_numbers)

                if len(user_numbers_to_create) > 0:
                    users_to_create: List[SignalUser] = []
                    for user_number in user_numbers_to_create:
                        users_to_create.append(
                            SignalUser(
                                source_number=user_number,
                                **user_infos[user_number]
                            )
                        )

                    SignalUser.objects.bulk_create(users_to_create)

                return SignalMessage.objects.bulk_create(messages_to_create)
        return []

    def send_message(self, message: str, recipients: List[SignalUser | SignalGroup]) -> Collection[SignalMessage]:
        message_content, message_styles = SignalClient.parse_message_style(message)
        for recipient in recipients:
            recipient_id = recipient.source_number if isinstance(recipient, SignalUser) else recipient.signal_id
            request_payload = {
                "jsonrpc": "2.0",
                "method": "send",
                "params": {
                    "message": message_content,
                    "text-style": message_styles,
                    "recipient": [recipient_id],
                    "account": self.user.source_number,
                },
                "id": str(uuid4()),
            }

            response = requests.post(
                url=self.url + "/api/v1/rpc",
                timeout=settings.REQUESTS_TIMEOUT_SECONDS,
                json=request_payload,
            )
            response.raise_for_status()

        return SignalMessage.objects.bulk_create(
            [
                SignalMessage(
                    target_group=recipient if isinstance(recipient, SignalGroup) else None,
                    target_user=recipient if isinstance(recipient, SignalUser) else None,
                    source_user=self.user,
                    text_content=message,
                    raw_content=request_payload,
                    received_at=datetime.now(tz=timezone.utc),
                    is_incoming=False,
                )
                for recipient in recipients
            ]
        )

    @staticmethod
    def parse_message_style(message):
        pattern = r'(\*[^*]+\*|#[^#]+#|~[^~]+~|\|[^\|]+\||_[^_]+\_)'
        matches = re.findall(pattern, message)
        style_to_content_tuples = []
        last_end = 0
        for match in matches:
            start = message.find(match, last_end)
            end = start + len(match)

            if start > last_end:
                style_to_content_tuples.append(("PLAIN", message[last_end:start]))

            style_char = match[0]
            style = STYLE_CHAR[style_char]

            style_to_content_tuples.append((style, match[1:-1]))  # Remove the style characters
            last_end = end

        if last_end < len(message):
            style_to_content_tuples.append(("PLAIN", message[last_end:]))

        style_directives: List[str] = []
        text_content = ""
        current_index = 0
        for style, content in style_to_content_tuples:
            if style != "PLAIN":
                style_directives.append(
                    f"{current_index}:{utf16_len(content)}:{style}"
                )

            current_index += utf16_len(content)
            text_content = text_content + content

        return (
            text_content,
            style_directives
        )
