# type: ignore
# Mixto lite lib for python3

from typing import List, Dict, Any, Union, cast
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
        self.workspace_id = None
        self.status = 0
        self.commit_type = "script"

        # if envars are set, always use those values
        if MIXTO_HOST is not None and self.host is None:
            self.host = MIXTO_HOST
        if MIXTO_API_KEY is not None and self.api_key is None:
            self.api_key = MIXTO_API_KEY

        # if host or apikey is not available, read config file
        if self.host == None or self.api_key == None:
            self.read_config()
            
    def read_config(self):
        try:
            conf_path = str(Path().home() / ".mixto.json")
            with open(conf_path) as f:
                j = json.loads(f.read())
                self.host = j["host"]
                self.api_key = j["api_key"]
                self.workspace_id = j["workspace_id"]
        except:
            ValueError("Cannot read mixto config file")

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
                sublime.status_message(f"Bad response code: {self.status}")
                raise BadResponse(self.status, res)
            if isJSON:
                return json.loads(str(body))
            else:
                return body
        except HTTPError as e:
            raise BadResponse(e.code, e.read())

    def AddCommit(
        self, data: str, entry_id: str = None, title: str = "", syntax: str = ""
    ):
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
            "/api/v1/commit",
            {
                "data": data,
                "commit_type": self.commit_type,
                "title": title,
                "entry_id": e_id,
                "workspace_id": self.workspace_id,
                "meta": {"syntax": syntax},
            },
        )
        return r

    def GetEntryIDs(self, include_commits: bool = False, reload_config=True) -> List[str]:
        """Get all entry ids filtered by the current workspace

        Returns:
            List[str]: List of entry ids
            include_commits[bool]: Include commits for all entries. Defaults to False
        """
        if reload_config:
            self.read_config()
        # get all entries
        resp = self.MakeRequest(
            "POST",
            "/api/v1/workspace",
            {"workspace_id": self.workspace_id, "include_commits": include_commits},
        )
        return resp["data"]["entries"]

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

    def GetNotes(self, entry_id: str):
        query = """
        query q($entry_id: String!) {
            notes: mixto_notes(where: { entry_id: { _eq: $entry_id } }, order_by: {updated_at: desc}) {
                note_id
                data
            }
        }
        """
        variables = {"entry_id": entry_id}
        return self.GraphQL(query, variables)["notes"]

    def UpdateNote(self, note_id: str, data: str):
        if not note_id or not data:
            raise ValueError("note_id or data cannot be blank")

        query = """
        mutation n($note_id: uuid = "", $data: String = "") {
            update_mixto_notes_by_pk(
                pk_columns: { note_id: $note_id }
                _set: { data: $data }
            ) {
                note_id
            }
        }
        """
        variables = {"note_id": note_id, "data": data}

        self.GraphQL(query, variables)
        sublime.status_message("Note updated")


# Sublime plugin code
# https://www.sublimetext.com/docs/api_reference.html#

import sublime
import sublime_plugin

ENABLE_OUTPUT_CAPTURE = True

mixto = MixtoLite()


def commit(self, entry, selected=False):
    output_window = self.view.window().find_output_panel('exec')
    if ENABLE_OUTPUT_CAPTURE and output_window:
        include_output = sublime.ok_cancel_dialog(
            f"Include output?"
        )
        if include_output:
            if output_window:
                self.text += "\n\nOutput:\n" + output_window.substr(sublime.Region(0, output_window.size()))
                
    confirm = sublime.ok_cancel_dialog(
        f"Commit {'selection' if selected else 'editor'} to '{entry['title']}' in '{mixto.workspace_id}' workspace?"
    )
    entryId = entry["entry_id"]
    # set base tag from syntax
    tags_objects = [
        {"text": self.syntax, "entry_id": entryId, "workspace_id": mixto.workspace_id}
    ]
    # get all other tags
    for t in self.tags.split(","):
        if len(t) > 2:
            tags_objects.append(
                {
                    "text": t.strip(),
                    "entry_id": entryId,
                    "workspace_id": mixto.workspace_id,
                }
            )

    mutation = """mutation m(
        $workspace_id: uuid!
        $entry_id: String!
        $tags: [typemixto_tags_commit_insert_input!] = {}
        $meta: json = ""
        $commit_type: String!
        $data: String!
        $title: String!
    ) {
        insert_mixto_commits_one(
            object: {
                workspace_id: $workspace_id
                commit_type: $commit_type
                entry_id: $entry_id
                data: $data
                title: $title
                tags_commits: { data: $tags }
                meta: $meta
            }
        ) {
            commit_id
        }
    }"""

    variables = {
        "workspace_id": mixto.workspace_id,
        "entry_id": entryId,
        "tags": tags_objects,
        "commit_type": mixto.commit_type,
        "meta": {"syntax": self.syntax if self.syntax else "text"},
        "data": self.text,
        "title": f"(sublime) {self.file_name}",
    }

    if confirm:
        mixto.GraphQL(mutation, variables)


class _FilenameInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, fileNameFromInput):
        self.fileNameFromInput = fileNameFromInput

    def name(self):
        return "fileNameFromInput"

    def initial_text(self):
        return self.fileNameFromInput


class _TagsInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, tagsFromInput):
        self.tagsFromInput = tagsFromInput

    def name(self):
        return "tagsFromInput"

    def initial_text(self):
        return self.tagsFromInput


class MixtoCommitCommand(sublime_plugin.TextCommand):
    """
    Commit current editor to Mixto
    """

    def __init__(self, window) -> None:
        super().__init__(window)

        self.selected_entry = {}
        self.text = ""
        self.syntax = ""

        file = self.view.file_name()
        self.file_name = str(Path(file).name) if file else "Untitled"
        self.tags = ""
        self._arg_position = 0

    def is_enabled(self):
        return True

    def input(self, args):
        # get multiple args from user
        if not args.get("fileNameFromInput"):
            return _FilenameInputHandler(self.file_name)
        if not args.get("tagsFromInput"):
            # used to track which arg a user is providing. this way the input description can be changed
            self._arg_position = 1
            return _TagsInputHandler(self.tags)

    def input_description(self):
        if self._arg_position == 1:
            return "Tags"
        return "File name"

    def run(self, edit, fileNameFromInput, tagsFromInput):
        self.file_name = fileNameFromInput
        self.tags = tagsFromInput
        self.entries = mixto.GetEntryIDs()
        self.text = self.view.substr(sublime.Region(0, self.view.size()))
        self.syntax = self.view.syntax().name.lower()
        if not self.text:
            return

        self.view.window().show_quick_panel(
            [x["title"] for x in self.entries], on_select=self._entry_selector_cb
        )

    def _entry_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        commit(self, self.entries[index])
        sublime.status_message("Commit added")


class MixtoAddNoteCommand(sublime_plugin.TextCommand):
    """
    Commit current editor to as a note in Mixto
    """

    def __init__(self, window) -> None:
        super().__init__(window)

        self.selected_entry = {}
        self.text = ""

    def is_enabled(self):
        return True

    def run(self, edit):
        self.entries = mixto.GetEntryIDs()
        self.text = self.view.substr(sublime.Region(0, self.view.size()))
        if not self.text:
            return

        self.view.window().show_quick_panel(
            [x["title"] for x in self.entries], on_select=self._entry_selector_cb
        )

    def _entry_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        entry = self.entries[index]
        confirm = sublime.ok_cancel_dialog(
            f"Add note to '{entry['title']}' in '{mixto.workspace_id}' workspace?"
        )
        if confirm:
            entry_id = entry["entry_id"]
            query = """mutation n(
                $entry_id: String = ""
                $workspace_id: uuid = ""
                $data: String = ""
            ) {
                insert_mixto_notes_one(
                    object: { entry_id: $entry_id, workspace_id: $workspace_id, data: $data }
                ) {
                    note_id
                }
            }
            """
            variables = {
                "entry_id": entry_id,
                "workspace_id": mixto.workspace_id,
                "data": self.text,
            }

            mixto.GraphQL(query, variables)
            sublime.status_message("Note added")


class MixtoCommitSelectionCommand(sublime_plugin.TextCommand):
    """
    Commit current selection to Mixto. The filename will include the line numbers
    """

    def __init__(self, window) -> None:
        super().__init__(window)

        self.selected_entry = {}
        self.text = ""
        self.syntax = ""
        _file = self.view.file_name()
        self.file_name = str(Path(_file).name) if _file else "Untitled"
        self.tags = ""
        self._arg_position = 0

    def is_enabled(self):
        return True

    def input(self, args):
        if not args.get("fileNameFromInput"):
            return _FilenameInputHandler(self.file_name)
        if not args.get("tagsFromInput"):
            self._arg_position = 1
            return _TagsInputHandler(self.tags)

    def input_description(self):
        if self._arg_position == 1:
            return "Tags"
        return "File name"

    def run(self, edit, fileNameFromInput, tagsFromInput):
        self.file_name = fileNameFromInput
        self.tags = tagsFromInput
        self.entries = mixto.GetEntryIDs()
        self.syntax = self.view.syntax().name.lower()

        sel = self.view.sel()[0]
        self.text = self.view.substr(sel)

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
        self.selected_entry = {}

        self._valid_commit_types = {
            "dump": None,
            "script": None,
            "tool": None,
            "stdout": None,
        }

    def is_enabled(self):
        return True

    def run(self, edit):
        self._edit = edit
        self.entries = mixto.GetEntryIDs(include_commits=True)

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
                lambda x: x["commit_type"] in self._valid_commit_types,
                self.selected_entry["commits"],
            )
        )

        self.view.window().show_quick_panel(
            [
                x["title"]
                for x in self.selected_entry["commits"]
                if x["commit_type"] in self._valid_commit_types
            ],
            on_select=self._commit_selector_cb,
        )

    def _commit_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        commit_id = self.selected_entry["commits"][index]["commit_id"]

        query = """query q($commit_id: uuid = "") {
            commit: mixto_commits_by_pk(commit_id: $commit_id) {
                data
            }
        }"""

        commit_data = mixto.MakeRequest(
            "POST",
            "/api/v1/gql",
            {"query": query, "variables": {"commit_id": commit_id}},
        )

        if "data" not in commit_data:
            return
        elif "commit" not in commit_data["data"]:
            return
        elif "data" not in commit_data["data"]["commit"]:
            return

        v = self.view.window().new_file()
        v.run_command("append", {"characters": commit_data["data"]["commit"]["data"]})


class MixtoUpdateNoteCommand(sublime_plugin.TextCommand):
    """
    Update an existing note
    """

    def __init__(self, window) -> None:
        super().__init__(window)
        self._edit = None
        self.selected_entry = {}

    def is_enabled(self):
        return True

    def run(self, edit):
        self._edit = edit
        self.entries = mixto.GetEntryIDs(include_commits=False)
        self.notes = []

        self.view.window().show_quick_panel(
            [x["title"] for x in self.entries],
            on_select=self._entry_selector_cb,
        )

    def _entry_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        self.selected_entry = self.entries[index]

        self.notes = mixto.GetNotes((self.selected_entry["entry_id"]))

        self.view.window().show_quick_panel(
            [x["data"][:30] for x in self.notes],
            on_select=self._note_selector_cb,
        )

    def _note_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        data = self.view.substr(sublime.Region(0, self.view.size()))
        note_id = self.notes[index]["note_id"]

        mixto.UpdateNote(note_id, data)


class MixtoGetNoteCommand(sublime_plugin.TextCommand):
    """
    Get an existing note
    """

    def __init__(self, window) -> None:
        super().__init__(window)
        self._edit = None
        self.selected_entry = {}

    def is_enabled(self):
        return True

    def run(self, edit):
        self._edit = edit
        self.entries = mixto.GetEntryIDs(include_commits=False)
        self.notes = []

        self.view.window().show_quick_panel(
            [x["title"] for x in self.entries],
            on_select=self._entry_selector_cb,
        )

    def _entry_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        self.selected_entry = self.entries[index]

        self.notes = mixto.GetNotes((self.selected_entry["entry_id"]))

        self.view.window().show_quick_panel(
            [x["data"][:30] for x in self.notes],
            on_select=self._note_selector_cb,
        )

    def _note_selector_cb(self, index: int):
        if index == -1 or index == None or len(self.entries) == 0:
            return

        data = self.notes[index]["data"]

        v = self.view.window().new_file()
        v.run_command("append", {"characters": data})
