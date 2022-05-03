from pydantic import BaseModel, validator, parse_obj_as
import json
from typing import List
from pathlib import Path

from lib.mixto import MixtoConfig, MixtoEntry


def validate_custom_json(config: MixtoConfig, path: str) -> List[MixtoEntry]:
    with Path(path).resolve().open() as f:
        data = json.loads(f.read())

    es = parse_obj_as(List[MixtoEntry], data)
    entries: List[MixtoEntry] = []
    for e in es:
        if e.category.lower() in config.categories:
            entries.append({'title': e.title, 'category': e.category.lower()})
        else:
            entries.append(MixtoEntry(title=e.title, category="other").dict())
    return entries
