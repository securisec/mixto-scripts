#!/bin/sh

# Set mixto host
MIXTO_HOST="http://localhost:5000"
# Set entry id or pass as flag
MIXTO_ENTRY_ID=""
# Workspace
MIXTO_WORKSPACE=""

# Mixto BASH

# colors
# Reset
Off='\e[0m'       # Text Reset

# Regular Colors
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green
Yellow='\033[0;33m'       # Yellow
Cyan='\e[1;36m'         # Cyan

MIXTO_OUTPUT=""

if [ -z $MIXTO_HOST ]; then
    printf '%bHost cannot be empty%b' "$Red" "$Off"
    exit 1
fi

show_help() {
  printf '%bMixto bash\n%b' "$Cyan" "$Off"
  printf '\t-e\t\tEntry ID if not set [Optional]\n'
  printf '\t-w\t\tWorkspace if not set [Optional]\n'
  printf '\t-t\t\tTitle of the entry [Optional]\n'
  printf '\t-h\t\tShow help\n'
  printf '\nUsage: some command | ./mixto.sh [optional args]\n'
  exit 0
}

# command line options
while getopts ":e:t:h" opt; do
  case $opt in
    e)
      entry_id="$OPTARG" >&2
      ;;
    w)
      workspace="$OPTARG" >&2
      ;;
    t)
      MIXTO_TITLE="$OPTARG" >&2
      ;;
    h)
      show_help
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND-1))

# set mixto entry id if passed as a flag
if [ -n "$entry_id" ]; then
    MIXTO_ENTRY_ID=$entry_id
fi
# set mixto workspace if passed as a flag
if [ -n "$workspace" ]; then
    MIXTO_WORKSPACE=$workspace
fi

if [ -z "$MIXTO_ENTRY_ID" ]; then
    echo '%bEntry id cannot be empty%b' "$Red" "$Off"
    exit 1
fi
if [ -z "$MIXTO_WORKSPACE" ]; then
    echo '%bWorkspace cannot be empty%b' "$Red" "$Off"
    exit 1
fi

# Read output of pipe
while IFS= read -r inp; do
    MIXTO_OUTPUT="${MIXTO_OUTPUT:+${MIXTO_OUTPUT}}${inp}\n"
done

payload='{"type": "stdout", "data": "'"$MIXTO_OUTPUT"'", "title": "'"$MIXTO_TITLE"'"}'

# Get api key securely
printf '%bMixto API Key: %b' "$Cyan" "$Off"
read -r MIXTO_API_KEY < /dev/tty
printf "\n"

# if curl command is not found, use wget
if command -v curl > /dev/null; then
  HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST \
      "$MIXTO_HOST"'/api/entry/'"$MIXTO_WORKSPACE"'/'"$MIXTO_ENTRY_ID"'/commit' \
      -H 'Accept: */*' \
      -H 'Content-Type: application/json;charset=utf-8' \
      -H 'x-api-key: '"$MIXTO_API_KEY" \
      -d "$payload"
    )
  HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
  if [ ! "$HTTP_STATUS" -eq 200  ]; then
      printf "Error [HTTP status: %b""$HTTP_STATUS""]" "$Yellow" "$Off"
      exit 1
  else
      printf '%bSent!%b\n' "$Green" "$Off"
  fi
elif command -v wget > /dev/null; then
  if wget -q --header="Content-Type: application/json;charset=utf-8" --header='x-api-key: '"$MIXTO_API_KEY" --post-data "$payload" "$MIXTO_HOST"'/api/entry/'"$MIXTO_WORKSPACE"'/'"$MIXTO_ENTRY_ID"'/commit' > /dev/null; then
    printf '%bSent!%b\n' "$Green" "$Off"
  else
    printf '%bCould not send!%b\n' "$Red" "$Off"
  fi
else
  printf '%bCurl or wget commands not found!%b\n' "$Red" "$Off"
fi