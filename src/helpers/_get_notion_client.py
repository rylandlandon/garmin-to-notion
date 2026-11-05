import os
import time
from dataclasses import dataclass

from notion_client import APIErrorCode, APIResponseError, Client

MAX_RATE_LIMIT_RETRIES = 8


class RateLimitRetryingClient(Client):
    """Notion client that waits and retries when Notion's rate limit is hit."""

    def request(self, *args, **kwargs):
        for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
            try:
                return super().request(*args, **kwargs)
            except APIResponseError as error:
                if error.code != APIErrorCode.RateLimited or attempt == MAX_RATE_LIMIT_RETRIES:
                    raise
                retry_after = error.headers.get("retry-after")
                time.sleep(float(retry_after) if retry_after else min(2 ** attempt, 30))


@dataclass(frozen=True)
class NotionDatabases:
    activities: str
    personal_records: str
    sleep: str
    daily_steps: str


def get_notion_client() -> tuple[Client, NotionDatabases]:
    print("Initializing Notion client...")

    notion_databases = NotionDatabases(
        activities=os.getenv("NOTION_DB_ID"),
        personal_records=os.getenv("NOTION_PR_DB_ID"),
        sleep=os.getenv("NOTION_SLEEP_DB_ID"),
        daily_steps=os.getenv("NOTION_STEPS_DB_ID"),
    )

    notion_token = os.getenv("NOTION_TOKEN")
    notion_client = RateLimitRetryingClient(auth=notion_token)

    print("Notion client initialized.")

    return notion_client, notion_databases