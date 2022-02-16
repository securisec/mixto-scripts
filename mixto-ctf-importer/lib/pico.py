from typing import List
from urllib.parse import urljoin
from pydantic import BaseModel
from .r_types import MixtoConfig, default_headers, MixtoEntry, GetAndProcessChallenges
import requests


class PicoCallengeCategory(BaseModel):
    name: str


class PicoChallenge(BaseModel):
    name: str
    category: PicoCallengeCategory


class PicoResponse(BaseModel):
    results: List[PicoChallenge]


class PicoCTF(GetAndProcessChallenges):
    cookies: dict = {}
    host: str = ""
    config: MixtoConfig = None

    def __init__(
        self, host: str, cookies: dict, event_id: int, config: MixtoConfig
    ) -> None:
        super().__init__()
        self.host = host
        self.cookies = cookies
        self.config = config
        self.event_id = event_id

        if event_id is None:
            raise Exception("event_id is required")

        # convert cookie to a string to pass in headers
        cookies_to_header = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
        default_headers["cookie"] = cookies_to_header

    def validate_cookie(self) -> bool:
        return (
            self.cookies.get("csrftoken") is not None
            and self.cookies.get("sessionid") is not None
        )

    def get_challenges(self) -> List[PicoChallenge]:
        if not self.validate_cookie():
            raise Exception("session cookie is not provided")
        url = urljoin(self.host, "/api/challenges/")
        try:
            r = requests.get(
                url,
                headers=default_headers,
                params={"original_event": self.event_id, "page_size": 100},
            )
            if r.status_code >= 400:
                print(f"\nFailed to get challenges: {r.text} {r.status_code}")
                exit(1)
            return PicoResponse(**r.json()).results
        except Exception as e:
            raise Exception(f"Failed to get challenges: {e}")

    def process_challenges_to_entries(self) -> List[MixtoEntry]:
        hold = []
        challenges = self.get_challenges()
        for challenge in challenges:
            if challenge.category.name.lower() in self.config.categories:
                hold.append(
                    {"title": challenge.name, "category": challenge.category.name.lower()}
                )
            else:
                hold.append({"title": challenge.name, "category": "other"})
        return hold
