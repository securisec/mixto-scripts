from typing import Any, List
from abc import ABC, abstractmethod
from .mixto import MixtoEntry

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"

default_headers = {"User-Agent": USER_AGENT}


class GetAndProcessChallenges(ABC):
    """
    Abstract class for getting and processing challenges.
    Should be used to implement various ctf platforms.
    """

    @abstractmethod
    def get_auth(self) -> dict:
        """
        Get cookies for the session.
        """
        pass

    @abstractmethod
    def get_challenges(self) -> Any:
        """
        Request challenges from the ctf platform and return them
        """
        pass

    @abstractmethod
    def process_challenges_to_entries(self) -> List[MixtoEntry]:
        """
        Process an array of challenges as an array of Mixto entries.
        """
        pass


def validate_dict(d: dict) -> None:
    """Validate a dictionary to make sure it has all the required keys."""
    for k, v in d.items():
        if not v:
            raise Exception(f"{k} is not provided")
