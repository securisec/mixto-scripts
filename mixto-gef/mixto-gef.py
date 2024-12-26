import gdb
import re

__AUTHOR__ = "securisec"
__VERSION__ = 1.0

# Mixto lite lib for python3

from typing import Dict, List, Union, Any
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urljoin
from urllib.error import HTTPError
from pathlib import Path
from os import getenv
import json

MIXTO_ENTRY_ID = getenv("MIXTO_ENTRY_ID")
MIXTO_HOST = getenv("MIXTO_HOST")
MIXTO_API_KEY = getenv("MIXTO_API_KEY")


class MissingRequired(Exception):
    """Missing params"""

    pass


class BadResponse(Exception):
    """Bad response from Mixto API"""

    pass


class MixtoLite:
    def __init__(
        self, host: Union[None, str] = None, api_key: Union[None, str] = None
    ) -> None:
        super().__init__()
        self.host = host
        self.api_key = api_key
        self.workspace_id = None
        self.status = 0
        self.commit_type = "tool"

        # if envars are set, always use those values
        if MIXTO_HOST is not None and self.host is None:
            self.host = MIXTO_HOST
        if MIXTO_API_KEY is not None and self.api_key is None:
            self.api_key = MIXTO_API_KEY

        # if host or apikey is not available, read config file
        if self.host == None or self.api_key == None:
            try:
                conf_path = str(Path().home() / ".mixto.json")
                with open(conf_path) as f:
                    j = json.loads(f.read())
                    self.host = j["host"]
                    self.api_key = j["api_key"]
                    self.workspace_id = j["workspace_id"]
            except:
                print("Cannot read mixto config file")
                raise

    def MakeRequest(
        self,
        method: str,
        uri: str,
        body: dict = {},
        query: dict = {},
        isJSON: bool = True,
    ):
        """Generic method helpful in extending this lib for other Mixto
        API calls. Refer to Mixto docs for all available API endpoints.

        Args:
            method (str): Request method
            uri (str): Mixto URI.
            body (dict, optional): Body. Defaults to {}.
            query (dict, optional): Query params. Defaults to {}.
            isJSON (bool, optional): If the response is of type JSON. Defaults to True.

        Raises:
            BadResponse: [description]
            BadResponse: [description]

        Returns:
            [type]: [description]
        """
        url = urljoin(str(self.host), uri)
        q = ""
        if query:
            q = "?" + urlencode(query)

        if self.api_key is None:
            raise AttributeError("api_key not found")

        req = Request(
            method=method.upper(),
            url=url + q,
            data=json.dumps(body).encode(),
            headers={
                "x-api-key": self.api_key,
                "user-agent": "mixto-lite-py",
            },
        )
        if body:
            req.add_header("Content-Type", "application/json")
        try:
            res = urlopen(req)
            body = res.read().decode()
            self.status = res.getcode()
            if self.status > 300:
                raise BadResponse(self.status, res)
            if isJSON:
                return json.loads(str(body))
            else:
                return body
        except HTTPError as e:
            raise BadResponse(e.code, e.read())

    def AddCommit(self, data: str, entry_id: str, title: str = "", optional: dict = {}):
        """Add/commit data to an entry. This is the primary functionality of
        an integration

        Args:
            data (str): Data to add
            entry_id (str, optional): Entry ID. Will use MIXTO_ENTRY_ID as primary. Defaults to None.
            title (str, optional): Title for commit. Defaults to "Untitled".
            optional (dict, optional): Optional dict to add to request body.

        Raises:
            MissingRequired: If entry id is missing

        Returns:
            dict: Commit added response
        """
        if MIXTO_ENTRY_ID is None and entry_id is None:
            raise MissingRequired("Entry id is missing")

        e_id = MIXTO_ENTRY_ID if MIXTO_ENTRY_ID else entry_id
        body = {
            "data": data,
            "workspace_id": self.workspace_id,
            "entry_id": e_id,
            "commit_type": self.commit_type,
            "title": title,
        }

        if len(optional) > 0:
            body = body | optional

        r = self.MakeRequest(
            "POST",
            "/api/v1/commit",
            body,
        )
        return r

    def GetWorkspaces(self) -> List[Dict[str, str]]:
        """Get all workspaces information and stats

        Returns:
            List[Dict[str, str]]: Array of workspace items
        """
        return self.MakeRequest("GET", "/api/v1/workspace")["data"]

    def GetEntryIDs(self, include_commits: bool = False) -> List[Dict[str, str]]:
        """Get all entry ids filtered by the current workspace

        Returns:
            List[Dict[str, str]]: List of entry ids
        """
        # get all entries
        entries = self.MakeRequest(
            "POST",
            "/api/v1/workspace",
            {"workspace_id": self.workspace_id, "include_commits": include_commits},
        )["data"]["entries"]
        # filter workspaces by current workspace
        return entries

    def GetCommitData(self, commit_id: str) -> str:
        """Get data for a commit by commit_id

        Args:
            commit_id (str): A valid commit_id

        Raises:
            ValueError: If no commit data is found

        Returns:
            dict: Commit added response
        """
        query = """query q($commit_id: uuid = "") {
            commit: mixto_commits_by_pk(commit_id: $commit_id) {
                data
            }
        }"""

        commit_data = self.MakeRequest(
            "POST",
            "/api/v1/gql",
            {"query": query, "variables": {"commit_id": commit_id}},
        )

        if "data" not in commit_data:
            raise ValueError("commit data not found")
        elif "commit" not in commit_data["data"]:
            raise ValueError("commit data not found")
        elif "data" not in commit_data["data"]["commit"]:
            raise ValueError("commit data not found")

        return commit_data["data"]["commit_id"]["data"]

    def GraphQL(
        self, query: str, variables: Union[Dict[str, Any], None] = None
    ) -> Dict[str, Any]:
        """Make a graphql request

        Args:
            query (str): GQL query string
            variables (Union[Dict[str, Any], None], optional): GQL variables. Defaults to None.

        Raises:
            ValueError: If the data key is not found in the response

        Returns:
            Dict[str, Any]: GQL response
        """
        body: Dict[str, Any] = {"query": query}
        if variables is not None:
            body["variables"] = variables
        resp = self.MakeRequest("POST", "/api/v1/gql", body=body)

        if "data" not in resp:
            raise ValueError(resp)

        return resp["data"]


mixto = MixtoLite()


@register
class NewCommand(GenericCommand):
    """Mixto GEF (with improved context approximation)."""

    _cmdline_ = "mixto"
    _syntax_ = f"{_cmdline_} <entry_id>"
    _examples_ = [
        f"{_cmdline_} <entry_id>",
    ]

    @only_if_gdb_running
    def do_invoke(self, argv, *args, **kwargs):
        if len(argv) < 1:
            self.usage()
            return

        mixto_entry_id = argv[0]
        try:
            output = ""

            # Registers
            output += "Registers:\n"
            regs = gdb.execute("info registers", to_string=True)
            output += re.sub(r"\x1b\[([0-9,;]*[mH])", "", regs)

            # Stack (Corrected Addresses and Formatting)
            output += "\nStack:\n"
            sp = int(gdb.parse_and_eval("$sp"))
            ptrsize = gef.arch.ptrsize

            for i in range(16):
                addr = sp + (i * ptrsize)
                try:
                    val = (
                        gdb.execute(f"x/1xg {addr}", to_string=True)
                        .split(":")[1]
                        .strip()
                    )
                    val_int = int(val, 16)
                    output += f"0x{addr:016x}│+0x{i*ptrsize:04x}: {val}"
                    try:
                        string_output = gdb.execute(f"x/s {val_int}", to_string=True)
                        match = re.search(r'"(.*?)"', string_output)
                        if match:
                            string_val = match.group(1)
                            output += f' → "{string_val}"'
                        else:
                            try:
                                # Try to resolve as a symbol
                                symbol = gdb.execute(
                                    f"info symbol {val_int}", to_string=True
                                )
                                output += f" → {symbol.strip()}"
                            except gdb.error:
                                pass  # No string or symbol
                    except ValueError:
                        pass  # Not a valid address
                    except gdb.error:
                        pass  # gdb error
                    output += "\n"

                except gdb.error:
                    output += f"0x{addr:016x}: Could not read memory\n"

            # Code (Improved - Corrected Address Calculation)
            output += "\nCode:\n"
            pc = int(gdb.parse_and_eval("$pc"))  # Convert to integer
            ptrsize = gef.arch.ptrsize
            prev_instructions_address = pc - (2 * ptrsize)

            # Ensure we don't go below 0
            if prev_instructions_address < 0:
                prev_instructions_address = 0

            code = gdb.execute(f"x/11i {prev_instructions_address}", to_string=True)
            output += re.sub(r"\x1b\[([0-9,;]*[mH])", "", code)

            # Backtrace
            output += "\nBacktrace:\n"
            bt = gdb.execute("bt", to_string=True)
            output += re.sub(r"\x1b\[([0-9,;]*[mH])", "", bt)

            mixto.AddCommit(output, mixto_entry_id, title="GEF output")
            print(f"✅ Sent data to mixto {mixto_entry_id}")

        except gdb.error as e:
            print(f"Error executing a GDB command: {e}")
        except Exception as e:
            print(f"Error writing to /tmp/a.out: {e}")
