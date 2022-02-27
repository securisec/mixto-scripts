from typing import List
from urllib.parse import urljoin
from pydantic import BaseModel

from .mixto import MixtoConfig, MixtoEntry
from .r_types import (
    default_headers,
    GetAndProcessChallenges,
    validate_dict,
)
import requests


class CTFdChallenge(BaseModel):
    name: str
    category: str


class CTFdResponse(BaseModel):
    success: bool
    data: List[CTFdChallenge]


class CTFd(GetAndProcessChallenges):
    cookies: dict = {}
    host: str = ""
    config: MixtoConfig = None

    def __init__(self, host: str, config: MixtoConfig) -> None:
        super().__init__()
        self.host = host
        self.config = config

    def get_cookies(self) -> dict:
        c = {}
        c["session"] = input("Value for session cookie: ")
        validate_dict(c)
        return c

    def get_challenges(self) -> List[CTFdChallenge]:
        session_cookie = self.get_cookies()["session"]
        cookies = {"session": session_cookie}
        url = urljoin(self.host, "/api/v1/challenges")
        try:
            r = requests.get(url, cookies=cookies, headers=default_headers)
            if r.status_code >= 400:
                raise Exception(f"{r.status_code} {r.reason}")
            return CTFdResponse(**r.json()).data
        except Exception as e:
            raise Exception(f"Failed to get challenges: {e}")

    def process_challenges_to_entries(self) -> List[MixtoEntry]:
        hold = []
        challenges = self.get_challenges()
        for challenge in challenges:
            if challenge.category in self.config.categories:
                hold.append({"title": challenge.name, "category": challenge.category})
            else:
                hold.append({"title": challenge.name, "category": "other"})
        return hold
