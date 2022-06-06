from typing import List
from urllib.parse import urljoin
from pydantic import BaseModel
from .mixto import MixtoConfig, MixtoEntry
from .r_types import default_headers, GetAndProcessChallenges, validate_dict
import requests


class RctfChallenge(BaseModel):
    name: str
    category: str


class RctfResponse(BaseModel):
    data: List[RctfChallenge]


class RCTF(GetAndProcessChallenges):
    host: str = ""
    config: MixtoConfig = None

    def __init__(self, host: str, config: MixtoConfig) -> None:
        super().__init__()
        self.host = host
        self.config = config

        info = self.get_auth()
        default_headers["Authorization"] = f"Bearer {info['token']}"

    def get_auth(self) -> dict:
        c = {}
        c["token"] = input("Bearer Token: ")
        validate_dict(c)
        return c

    def get_challenges(self) -> List[RctfChallenge]:
        url = urljoin(self.host, f"/api/v1/challs")
        try:
            r = requests.get(
                url,
                headers=default_headers,
            )
            if r.status_code >= 400:
                print(f"\nFailed to get challenges: {r.text} {r.status_code}")
                exit(1)
            return RctfResponse(**r.json()).data
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
