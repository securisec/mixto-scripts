from typing import List
from urllib.parse import urljoin
from pydantic import BaseModel
from .mixto import MixtoConfig, MixtoEntry
from .r_types import default_headers, GetAndProcessChallenges, validate_dict
import requests


class PicoCallengeCategory(BaseModel):
    name: str


class PicoChallenge(BaseModel):
    name: str
    category: PicoCallengeCategory


class PicoResponse(BaseModel):
    results: List[PicoChallenge]


class PicoCTF(GetAndProcessChallenges):
    host: str = ""
    config: MixtoConfig = None

    def __init__(self, host: str, config: MixtoConfig) -> None:
        super().__init__()
        self.host = host
        self.cookies = None
        self.config = config
        self.event_id = None

        get_cookies = self.get_auth()
        cookies = {
            "csrftoken": get_cookies["csrftoken"],
            "sessionid": get_cookies["sessionid"],
        }
        # convert cookie to a string to pass in headers
        cookies_to_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        default_headers["cookie"] = cookies_to_header

        self.event_id = get_cookies["original_event"]

    def get_auth(self) -> dict:
        c = {}
        c["sessionid"] = input("Value for sessionid cookie: ")
        c["csrftoken"] = input("Value for csrftoken cookie: ")
        c["original_event"] = input("Original event ID from URL: ")
        validate_dict(c)
        return c

    def get_challenges(self) -> List[PicoChallenge]:
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
                    {
                        "title": challenge.name,
                        "category": challenge.category.name.lower(),
                    }
                )
            else:
                hold.append({"title": challenge.name, "category": "other"})
        return hold
