# ctftime-solutions

Easily add the first found solution posted to ctftime for an entry. It is not really smart and does simple title comparisons to find matching entries. `mixto.db` is used for data persistance to avoid adding duplicate writeups.

## Usage
```
usage: main.py [-h] --event EVENT [--dry-run]

options:
  -h, --help            show this help message and exit
  --event EVENT, -e EVENT
                        Event id
  --dry-run             Dry run. Dont add any commits
  --stats               See stats for current workspace
```

- It will look for the following environment variables:
  - MIXTO_HOST
  - MIXTO_API_KEY
- If either the `MIXTO_HOST` or `MIXTO_API_KEY` is not set, then it will look for these values in the `~/.mixto.json` file.
