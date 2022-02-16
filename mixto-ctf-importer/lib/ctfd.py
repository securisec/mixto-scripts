from typing import List
from urllib.parse import urljoin
from pydantic import BaseModel
from .r_types import MixtoConfig, default_headers, MixtoEntry, GetAndProcessChallenges
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

    def __init__(self, host: str, cookies: dict, config: MixtoConfig) -> None:
        super().__init__()
        self.host = host
        self.cookies = cookies
        self.config = config

    def validate_cookie(self) -> bool:
        return self.cookies.get("session") is not None

    def get_challenges(self) -> List[CTFdChallenge]:
        if not self.validate_cookie():
            raise Exception("session cookie is not provided")
        url = urljoin(self.host, "/api/v1/challenges")
        try:
            r = requests.get(url, cookies=self.cookies, headers=default_headers)
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
