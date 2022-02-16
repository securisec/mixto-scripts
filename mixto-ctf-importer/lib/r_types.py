from typing import Any, List
from pydantic import BaseModel
from abc import ABC, abstractmethod

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"

default_headers = {"User-Agent": USER_AGENT}


class MixtoConfig(BaseModel):
    api_key: str
    categories: List[str]
    host: str
    workspace: str


class MixtoEntry(BaseModel):
    title: str
    category: str


class GetAndProcessChallenges(ABC):
    """
    Abstract class for getting and processing challenges.
    Should be used to implement various ctf platforms.
    """

    @abstractmethod
    def validate_cookie(self) -> bool:
        """Ensure valid cookies are provided."""
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
