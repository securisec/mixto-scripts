from typing import List
from urllib.parse import urljoin
from pydantic import BaseModel
from .mixto import MixtoConfig, MixtoEntry
from .r_types import default_headers, GetAndProcessChallenges, validate_dict
import requests


HTBCategories = {
    16: "other",
    15: "hardware",
    13: "osint",
    2: "web",
    7: "forensics",
    8: "misc",
    4: "crypto",
    3: "pwn",
    5: "reversing",
}


class HTBChallenge(BaseModel):
    name: str
    challenge_category_id: int


class HTBResponse(BaseModel):
    challenges: List[HTBChallenge]


class HtbCTF(GetAndProcessChallenges):
    host: str = ""
    config: MixtoConfig = None

    def __init__(self, host: str, config: MixtoConfig) -> None:
        super().__init__()
        self.host = host
        self.config = config
        self.event_id = None

        info = self.get_cookies()
        default_headers["Authorization"] = f"Bearer {info['token']}"

        self.event_id = info["event_id"]

    def get_cookies(self) -> dict:
        c = {}
        c["event_id"] = input("Event ID: ")
        c["token"] = input("Bearer Token: ")
        validate_dict(c)
        return c

    def get_challenges(self) -> List[HTBChallenge]:
        url = urljoin(self.host, f"/api/ctf/{self.event_id}")
        try:
            r = requests.get(
                url,
                headers=default_headers,
            )
            if r.status_code >= 400:
                print(f"\nFailed to get challenges: {r.text} {r.status_code}")
                exit(1)
            return HTBResponse(**r.json()).challenges
        except Exception as e:
            raise Exception(f"Failed to get challenges: {e}")

    def process_challenges_to_entries(self) -> List[MixtoEntry]:
        hold = []
        challenges = self.get_challenges()
        for challenge in challenges:
            hold.append(
                {
                    "title": challenge.name,
                    "category": HTBCategories[challenge.challenge_category_id],
                }
            )
        return hold
