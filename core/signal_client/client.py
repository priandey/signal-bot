from datetime import datetime, timezone
import logging
from typing import Any, Collection, Dict, List
from django.utils import timezone
from django.db.transaction import atomic
import requests
from django.conf import settings

from core.models.signal_group import SignalGroup
from core.models.signal_message import SignalMessage
from core.models.signal_user import SignalUser

logger = logging.getLogger("SignalClient")


class SignalClient:
    def __init__(self, signal_user: SignalUser):
        self.url: str = settings.SIGNAL_URL.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        accounts_request = requests.get(
            self.url,
            timeout=settings.REQUESTS_TIMEOUT_SECONDS,
        )
        accounts_request.raise_for_status()

        if signal_user.source_number not in accounts_request.json():
            raise ValueError("Provided user is not registered in the signal client")

        if not signal_user.is_registered:
            signal_user.is_registered = True
            signal_user.save(update_fields=["can_send_message"])

        self.user = signal_user

    def receive_messages(self) -> Collection[SignalMessage]:
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
                            target_user_id=envelope["source_number"],
                            source_user=self.user,
                            text_context=message["message"],
                            raw_content=item,
                            received_at=datetime.fromtimestamp(message["timestamp"], timezone.utc),
                            is_incoming=True,
                        )
                    )

                    user_infos.setdefault(
                        envelope["source_number"],
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
        request_payload = {
            "message": message,
            "recipients": [
                recipient.source_number
                if isinstance(recipient, SignalUser)
                else recipient.signal_id
                for recipient in recipients
            ],
            "text_mode": "styled",
            "number": self.user.source_number,
        }

        response = requests.post(
            url=self.url + "/v2/send/",
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
                    text_context=message,
                    raw_content=request_payload,
                    received_at=datetime.now(tz=timezone.utc),
                    is_incoming=False,
                )
                for recipient in recipients
            ]
        )
