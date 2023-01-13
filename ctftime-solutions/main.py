import re
import argparse
from typing import Any, Dict, List, Union, cast
import requests
from parsel import Selector
from mixto import MixtoLite

CTFTIME_URL = "https://ctftime.org"


class CtftimeWriteup(MixtoLite):
    """Main class that inherits and initializes MixtoLite class

    Args:
        MixtoLite (MixtoLite): MixtoLite sdk
    """

    def __init__(self, event_id: str):
        """Initialize with ctftime event id

        Args:
            event_id (str): ctftime event id
        """
        super().__init__()
        self.commit_type = "url"
        self.event_id = event_id
        self.request_headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }

    def make_request(self, url: str) -> requests.Response:
        """Make a ctftime request

        Args:
            url (str): url to make the request

        Returns:
            requests.Response: requests.Response object
        """
        return requests.get(url, headers=self.request_headers)

    def validate(self, id: str):
        """Validate that the id only includes numbers

        Args:
            id (str): the id to validate

        Raises:
            ValueError: Raises error when id is not only numbers
        """
        if not bool(re.search(r"^\d+$", id)):
            raise ValueError("Not a valid id format. Should be only digits")

    def parse_html(
        self, data: str, xpath: str, all: bool = True
    ) -> Union[List[Any], str, None]:
        """Parses html using parsel

        Args:
            data (str): Data to parse
            xpath (str): Xpath expression to parse with
            all (bool, optional): Return all or single result. Defaults to True.

        Returns:
            Union[List[Any], str, None]: _description_
        """
        s = Selector(data).xpath(xpath)
        if all:
            return s.getall()
        return s.get()

    def ctftime_get_event(self, event_id: str) -> Dict[str, str]:
        """Get ctftime event and all related tasks. This will only return
        tasks which has writeups

        Args:
            event_id (str): Event id

        Returns:
            Dict[str, str]: Dict where task id is the key, and the task name is the value
        """
        self.validate(event_id)
        url = f"{CTFTIME_URL}/event/{event_id}/tasks/"
        res = self.make_request(url)
        trs = self.parse_html(res.text, "//tr")
        tasks = [self.parse_html(x, "//a/text() | //a/@href") for x in cast(list, trs)]
        return {t[1].lower(): t[0] for t in tasks if t is not None and len(t) == 4}

    def ctftime_get_task(self, task_path: str):
        """Get the url for a single write for a task

        Args:
            task_path (str): Task path

        Returns:
            str: writeup path
        """
        url = f"{CTFTIME_URL}/{task_path}"
        res = self.make_request(url)
        writeups = self.parse_html(res.text, "//td/a/@href", False)
        return writeups

    def ctftime_get_writeup(self, writeup_path: str):
        """Get the original writeup url for a writeup

        Args:
            writeup_path (str): writeup path obtained from tasks

        Returns:
            str: original writeup url
        """
        url = f"{CTFTIME_URL}{writeup_path}"
        res = self.make_request(url)
        writeup = self.parse_html(res.text, "//div[@class = 'well']/a/@href", False)
        return writeup

    def match_mixto_entries(self) -> Dict[str, Dict[str, str]]:
        """Get entries from mixto and check against ctftime writeups for overlap.
        This method does rely that the ctftime task name is equal to the entry name
        in mixto

        Returns:
            Dict[str, Dict[str, str]]: Dict where key is the mixto entry id and value is a
            dict containing title and writup link.
        """
        hold = {}
        entries = self.GetEntryIDs()
        events = self.ctftime_get_event(self.event_id)

        for e in entries:
            m = events.get(e["title"].lower())
            if m:
                hold[e["entry_id"]] = {"writeup": m, "title": e["title"]}
        return hold


if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("--event", "-e", help="Event id", required=True, type=int)
    parse.add_argument(
        "--dry-run",
        help="Dry run. Dont add any commits",
        default=False,
        action="store_true",
    )
    args = parse.parse_args()

    c = CtftimeWriteup(str(args.event))

    for entry_id, task in c.match_mixto_entries().items():
        task_id = c.ctftime_get_task(task["writeup"])
        writeup = cast(str, c.ctftime_get_writeup(cast(str, task_id)))
        # if dry run, dont add any commits
        if args.dry_run:
            print(entry_id, task)

        elif writeup and not args.dry_run:
            res = c.AddCommit(
                entry_id=entry_id, data=writeup, optional={"documentation": True}
            )
            task["commit_id"] = res["commit_id"]
            print(task)
