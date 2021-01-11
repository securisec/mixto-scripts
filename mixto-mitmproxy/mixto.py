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
    def __init__(self, host: str = None, api_key: str = None) -> None:
        super().__init__()
        self.host = host
        self.api_key = api_key
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
        req = Request(
            method=method.upper(),
            url=url + q,
            data=json.dumps(body).encode(),
            headers={"x-api-key": self.api_key, "user-agent": "mixto-lite-py",},
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

    def AddCommit(self, data: str, entry_id: str = None, title: str = ""):
        """Add/commit data to an entry. This is the primary functionality of 
        an integration

        Args:
            data (str): Data to add
            entry_id (str, optional): Entry ID. Will use MIXTO_ENTRY_ID as primary. Defaults to None.
            title (str, optional): Title for commit. Defaults to "Untitled".

        Raises:
            MissingRequired: If entry id is missing

        Returns:
            dict: Commit added response
        """
        if MIXTO_ENTRY_ID is None and entry_id is None:
            raise MissingRequired("Entry id is missing")

        e_id = MIXTO_ENTRY_ID if MIXTO_ENTRY_ID else entry_id
        r = self.MakeRequest(
            "POST",
            "/api/entry/{}/commit".format(e_id),
            {"data": data, "type": self.commit_type, "title": title},
        )
        return r

    def GetWorkspaces(self):
        """Get all workspaces, entries and commits in a compact format. 
        Helpful when trying to populate entry ID and commit ID's or 
        filter by workspace

        Returns:
            List[dict]: Array of workspace items
        """
        return self.MakeRequest(
            "GET", "/api/misc/workspaces", None, {"all": "true"}, True
        )
