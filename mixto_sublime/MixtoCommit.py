# Mixto lite lib for python3

from typing import List
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
        self.workspace = None
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
                    self.workspace = j["workspace"]
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
            headers={
                "x-api-key": self.api_key,
                "user-agent": "mixto-sublime",
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
            "/api/entry/{}/{}/commit".format(self.workspace, e_id),
            {"data": data, "type": self.commit_type, "title": title},
        )
        return r

    def GetWorkspaces(self) -> dict:
        """Get all workspaces information and stats

        Returns:
            dict: Array of workspace items
        """
        return self.MakeRequest("GET", "/api/workspace")

    def GetEntryIDs(self, get_all: bool = False) -> List[str]:
        """Get all entry ids filtered by the current workspace

        Returns:
            List[str]: List of entry ids
        """
        # get all entries
        entries = self.MakeRequest(
            "GET",
            "/api/misc/workspaces/{}".format(self.workspace),
            None,
        )
        # filter workspaces by current workspace
        # modified for sublime
        if get_all:
            return entries
        return [{"entry_id": x["entry_id"], "title": x["title"]} for x in entries]


# Sublime plugin code
# https://www.sublimetext.com/docs/api_reference.html#

import sublime
import sublime_plugin

mixto = MixtoLite()


def commit(self, entry, selected=False):
    confirm = sublime.ok_cancel_dialog(
        f"Commit {'selection' if selected else 'editor'} to '{entry['title']}' in '{mixto.workspace}' workspace?"
    )
    if confirm:
        mixto.AddCommit(self.text, entry["entry_id"], f"(sublime) {self.file_name}")


def get_file_name(self):
    file = self.view.file_name()
    return str(Path(file).name) if file else "Untitled"


class MixtoCommitCommand(sublime_plugin.TextCommand):
    """
    Commit current editor to Mixto
    """
    def __init__(self, window) -> None:
        super().__init__(window)

        self.selected_entry = {}
        self.text = ""
        self.file_name = ""

    def is_enabled(self):
        return True

    def run(self, edit):
        self.entries = mixto.GetEntryIDs()
        self.text = self.view.substr(sublime.Region(0, self.view.size()))
        self.file_name = get_file_name(self)
        if not self.text:
            return

        self.view.window().show_quick_panel(
            [x["title"] for x in self.entries], on_select=self._entry_selector_cb
        )

    def _entry_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        commit(self, self.entries[index])


class MixtoCommitSelectionCommand(sublime_plugin.TextCommand):
    """
    Commit current selection to Mixto. The filename will include the line numbers
    """
    def __init__(self, window) -> None:
        super().__init__(window)

        self.selected_entry = {}
        self.text = ""
        self.file_name = ""

    def is_enabled(self):
        return True

    def run(self, edit):
        self.entries = mixto.GetEntryIDs()

        sel = self.view.sel()[0]
        self.text = self.view.substr(sel)

        self.file_name = get_file_name(self)
        if not self.text:
            return

        self.file_name = (
            self.file_name
            + f" ({self.view.rowcol(sel.begin())[0] + 1}:{self.view.rowcol(sel.end())[0] + 1})"
        )

        self.view.window().show_quick_panel(
            [x["title"] for x in self.entries], on_select=self._entry_selector_cb
        )

    def _entry_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        commit(self, self.entries[index], True)


class MixtoGetCommitCommand(sublime_plugin.TextCommand):
    """
    Open a valid commit in a new tab
    """
    def __init__(self, window) -> None:
        super().__init__(window)
        self._edit = None

        self._valid_commit_types = {
            "dump": None,
            "script": None,
            "tool": None,
            "stdout": None,
        }
        self.selected_entry = {}

    def is_enabled(self):
        return True

    def run(self, edit):
        self._edit = edit
        self.entries = mixto.GetEntryIDs(get_all=True)

        self.view.window().show_quick_panel(
            [x["title"] for x in self.entries],
            on_select=self._entry_selector_cb,
        )

    def _entry_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        self.selected_entry = self.entries[index]
        self.selected_entry["commits"] = list(
            filter(
                lambda x: x["type"] in self._valid_commit_types,
                self.selected_entry["commits"],
            )
        )

        self.view.window().show_quick_panel(
            [
                x["title"]
                for x in self.selected_entry["commits"]
                if x["type"] in self._valid_commit_types
            ],
            on_select=self._commit_selector_cb,
        )

    def _commit_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        commit_id = self.selected_entry["commits"][index]["commit_id"]
        entry_id = self.selected_entry["entry_id"]

        commit_data = mixto.MakeRequest(
            "GET", f"/api/entry/{mixto.workspace}/{entry_id}/commit/{commit_id}"
        )

        if "data" not in commit_data:
            return

        v = self.view.window().new_file()
        v.run_command("append", {"characters": commit_data["data"]})
