from argparse import ArgumentParser
from json import loads
from pathlib import Path
from os import getenv
from pydantic import ValidationError
from model.validator import Workspace


def argument_parser():
    parser = ArgumentParser(description="Validate a workspace before importing")
    parser.add_argument("json", help="JSON file to validate", type=str, nargs=1)
    # TODO
    return parser


if __name__ == "__main__":
    if getenv('DEV'):
        # only for local dev
        obj = loads(Path('./temp/valid.json').absolute().read_text())
    else:
        parser = argument_parser()
        args = parser.parse_args()
        path = Path(args.json[0]).absolute()
        obj = loads(path.read_text())
    Workspace(**obj)
    try:
        Workspace(**obj)
        print("Workspace is valid")
    except ValidationError as err:
        print(err)
        exit(1)