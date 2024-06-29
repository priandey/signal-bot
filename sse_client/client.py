import json
import logging
import time
import requests


def read_sse(sse_url, server_endpoint):
    with requests.Session() as session:
        response = session.get(sse_url, stream=True)
        response.encoding = 'utf-8'

        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    event_data = json.loads(line.lstrip("data:"))
                    requests.post(server_endpoint, json=event_data)
                except json.JSONDecodeError:
                    logging.debug(f"Failed to decode JSON: {line}")


if __name__ == "__main__":
    time.sleep(2)
    logging.warning("Waking up the client")
    sse_url = 'http://signal-cli:7583/api/v1/events'
    server_endpoint = 'http://web:8000/poke/'
    read_sse(sse_url, server_endpoint)
