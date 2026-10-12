from __future__ import annotations

import argparse
import json
import uuid

from legal_notify.infrai_realtime import InfraiRealtime


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a private legal-user channel and subscriber token")
    parser.add_argument("user_id")
    args = parser.parse_args()
    channel = f"legal-user-{args.user_id}"
    request_id = str(uuid.uuid4())
    client = InfraiRealtime()
    try:
        created = client.create_channel(channel, request_id)
        token = client.issue_token(args.user_id, channel, request_id)
        print(json.dumps({"channel": channel, "created": created, "subscriber": token}, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

