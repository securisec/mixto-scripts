from typing import List
from urllib.parse import urljoin
from pydantic import BaseModel
from .mixto import MixtoConfig, MixtoEntry
from .r_types import default_headers, GetAndProcessChallenges, validate_dict
import requests


HTBCategories = {
    21: "network",
    20: "cloud",
    18: "network",
    17: "network",
    16: "other",
    15: "hardware",
    14: "other",
    13: "osint",
    12: "android",
    11: "scripting",
    10: "pcap",
    9: "other",
    8: "misc",
    7: "forensics",
    6: "stego",
    5: "reversing",
    4: "crypto",
    3: "pwn",
    2: "web",
    1: "network",
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

        info = self.get_auth()
        default_headers["Authorization"] = f"Bearer {info['token']}"

        self.event_id = info["event_id"]

    def get_auth(self) -> dict:
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
