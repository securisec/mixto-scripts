"""
This script allows calling the CTFd API and automatically creating valid 
Mixto entries.
"""
import json
import argparse
from typing import List
from urllib.parse import urljoin
from pathlib import Path
import requests

from r_types import CTFdChallenge, CTFdResponse, MixtoConfig


def show_error(message: str):
    """
    Prints an error message and exits the program.
    """
    raise Exception(message)


def read_mixto_conf() -> MixtoConfig:
    """
    Reads the ~/.mixto.json file and returns a dictionary with the configuration.
    """
    config_path = Path.home() / ".mixto.json"
    if not config_path.exists():
        show_error("The configuration file does not exist.")
    with config_path.open() as config_file:
        return MixtoConfig(**json.load(config_file))


def parse_args():
    """
    Parses the command line arguments.
    """
    args = argparse.ArgumentParser()
    args.add_argument(
        "--host",
        help="The hostname of the CTFd instance. Do not include /api/v1",
        required=True,
    )
    args.add_argument(
        "--session",
        help="A valid session cookie value from the CTFd instance",
        required=True,
    )
    return args.parse_args()


def get_challenges(ctfd_url: str, session: str) -> List[CTFdChallenge]:
    """
    Returns all challenges from the CTFd instance.
    """
    url = urljoin(ctfd_url, "/api/v1/challenges")
    try:
        r = requests.get(url, cookies={"session": session})
        return CTFdResponse(**r.json()).data
    except Exception as e:
        show_error(f"Failed to get challenges: {e}")


def create_entries(challenges: List[CTFdChallenge]) -> List[dict]:
    """
    Adds all challenges to the Mixto database.
    """
    mixto_conf = read_mixto_conf()
    hold: List[dict] = []
    for challenge in challenges:
        if challenge.category in mixto_conf.categories:
            hold.append({"title": challenge.name, "category": challenge.category})
        else:
            hold.append({"title": challenge.name, "category": "other"})
    url = urljoin(mixto_conf.host, f"/api/entry/{mixto_conf.workspace}")
    try:
        r = requests.put(url, json=hold, headers={"x-api-key": mixto_conf.api_key})
        if r.status_code != 200:
            show_error(f"Failed to add entries: {r.status_code}")
        return [{e["entry_id"]: e["title"]} for e in r.json()]
    except Exception as e:
        show_error(f"Error when adding entries: {r.status_code}")


if __name__ == "__main__":
    args = parse_args()
    if Path(".entriesAdded").exists():
        show_error("The entries have already been added.")
    challenges = get_challenges(args.host, args.session)
    created = create_entries(challenges)
    print(f"Created {len(challenges)} entries")
    Path(".entriesAdded").write_text(json.dumps(created, indent=4))
