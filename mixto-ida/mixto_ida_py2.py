# Mixto python2 lite lib for integrations without any dependencies

from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode
from urlparse import urljoin
import os
import json

MIXTO_ENTRY_ID = os.getenv("MIXTO_ENTRY_ID")
MIXTO_HOST = os.getenv("MIXTO_HOST")
MIXTO_API_KEY = os.getenv("MIXTO_API_KEY")


class MissingRequired(Exception):
    """Missing params"""

    pass


class BadResponse(Exception):
    """Bad response from Mixto API"""

    pass


class MixtoLite:
    def __init__(self, host=None, api_key=None):
        self.host = host
        self.api_key = api_key
        self.worksapce = None
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
                conf_path = str(os.path.expanduser("~/.mixto.json"))
                with open(conf_path) as f:
                    j = json.loads(f.read())
                    self.host = j["host"]
                    self.api_key = j["api_key"]
                    self.worksapce = j["workspace"]
            except:
                print("Cannot read mixto config file")
                raise

    def MakeRequest(
        self,
        uri,
        data={},
        is_query=False,
    ):
        """Generic method helpful in extending this lib for other Mixto
        API calls. Refer to Mixto docs for all available API endpoints.

        Args:
            method (str): Request method
            uri (str): Mixto URI.
            data (dict, optional): Body or query params. Defaults to {}.
            is_query (bool, optional): True if query params. Defaults to False.

        Raises:
            BadResponse: If status code is not 200, raises exception

        Returns:
            None: None
        """
        # add base url with endpoint
        url = urljoin(str(self.host), uri)
        # if query params, add data as query params
        if is_query:
            data = urlencode(data)
            url += "?" + data
        else:
            # add as json body
            data = json.dumps(data)
        # create request object
        req = Request(
            url=url,
            headers={
                "x-api-key": self.api_key,
                "user-agent": "mixto-lite-py2",
            },
        )
        # add json content type if post body
        if not is_query:
            req.add_header("Content-Type", "application/json")
            req.add_data(data)

        # send request
        try:
            res = urlopen(req)
            body = res.read().decode()
            self.status = res.getcode()
            if self.status > 300:
                raise BadResponse(self.status, res)
            else:
                return body
        except HTTPError as e:
            raise BadResponse(e.code, e.read())

    def AddCommit(self, data, entry_id=None, title=""):
        """Add/commit data to an entry. This is the primary functionality of
        an integration

        Args:
            data (str): Data to add
            entry_id (str, optional): Entry ID. Will use MIXTO_ENTRY_ID as primary. Defaults to None.
            title (str, optional): Title for commit. Defaults to "Untitled".

        Raises:
            MissingRequired: If entry id is missing

        Returns:
            any: Commit added response
        """
        if MIXTO_ENTRY_ID is None and entry_id is None:
            raise MissingRequired("Entry id is missing")

        e_id = MIXTO_ENTRY_ID if MIXTO_ENTRY_ID else entry_id
        return self.MakeRequest(
            "/api/entry/{}/{}/commit".format(self.worksapce, e_id),
            {"data": data, "type": self.commit_type, "title": title},
        )

    def GetWorkspaces(self):
        """Get all workspaces, entries and commits in a compact format.
        Helpful when trying to populate entry ID and commit ID's or
        filter by workspace

        Returns:
            List[dict]: Array of workspace items
        """
        return self.MakeRequest("/api/misc/workspaces", {"all": "true"}, True)

    def GetEntryIDs(self):
        """Get all entry ids filtered by the current workspace

        Returns:
            List[str]: List of entry ids
        """
        # get all workspaces
        workspaces = self.GetWorkspaces()
        # filter workspaces by current workspace
        return [w["entry_id"] for w in workspaces if w["workspace"] == self.workspace]


"""
Mixto IDA Plugin
"""
import idc
import idaapi
import idautils
import ida_hexrays

# Retrieving imports from IDAPython is a little weird
# So need this global variable
AllImports = ""


def imports_cb(ea, name, ord):
    global AllImports
    if not name:
        AllImports += "0x{:x}: ord#{}\n".format(ea, ord)
    else:
        AllImports += "0x{:x}: {} ord#{}\n".format(ea, name, ord)
    # True -> Continue enumeration
    # False -> Stop enumeration
    return True


def start_ea_of(o):
    return getattr(o, "start_ea" if idaapi.IDA_SDK_VERSION >= 700 else "startEA")


def end_ea_of(o):
    return getattr(o, "end_ea" if idaapi.IDA_SDK_VERSION >= 700 else "endEA")


def get_flags_at(ea):
    return getattr(
        idaapi, "get_flags" if idaapi.IDA_SDK_VERSION >= 700 else "getFlags"
    )(ea)


def is_data(flags):
    return getattr(idaapi, "is_data" if idaapi.IDA_SDK_VERSION >= 700 else "isData")(
        flags
    )


MenuAllFunc = "Mixto:AllFunc"
MenuImports = "Mixto:Imports"
MenuExports = "Mixto:Exports"
MenuAllComments = "Mixto:AllComments"
MenuDecFunc = "Mixto:DecompileFunc"
MenuAskEntryId = "Mixto:AskEntryId"


class mixto_t(idaapi.plugin_t):

    flags = idaapi.PLUGIN_UNL
    comment = ""
    help = ""
    wanted_name = "Mixto"
    wanted_hotkey = ""
    mixto = MixtoLite()

    def init(self):
        self.add_menu_items()
        return idaapi.PLUGIN_OK

    @classmethod
    def add_menu_item_helper(self, name, text, tooltip, icon, shortcut):
        description = idaapi.action_desc_t(
            name, text, self.StartHandler(self, name), shortcut, tooltip, icon
        )
        idaapi.register_action(description)
        idaapi.attach_action_to_menu(
            self.wanted_name + "/" + text, name, idaapi.SETMENU_APP
        )

    @classmethod
    def add_menu_items(self):
        idaapi.create_menu(self.wanted_name, self.wanted_name)
        self.add_menu_item_helper(
            MenuAskEntryId,
            "Set Mixto Entry ID",
            "Specify entry id to send subsequent data",
            -1,
            "",
        )
        self.add_menu_item_helper(
            MenuAllFunc,
            "Send all functions",
            "Send all function names and addresses to mixto",
            -1,
            "",
        )
        self.add_menu_item_helper(
            MenuDecFunc,
            "Send decompilation of selected function",
            "Send decompilation of selected function to mixto",
            -1,
            "",
        )
        self.add_menu_item_helper(
            MenuImports, "Send all imports", "Send all imports to mixto", -1, ""
        )
        self.add_menu_item_helper(
            MenuExports, "Send all exports", "Send all exports to mixto", -1, ""
        )
        self.add_menu_item_helper(
            MenuAllComments,
            "Send all comments",
            "Send all comments and respective addresses to mixto",
            -1,
            "",
        )

    class StartHandler(idaapi.action_handler_t):
        def __init__(self, outer_self, menu_title):
            idaapi.action_handler_t.__init__(self)
            self.menu_title = menu_title
            self.outer_self = outer_self

        def activate(self, ctx):
            if self.menu_title == MenuAskEntryId:
                self.outer_self.mixto.entry_id = idaapi.ask_str(
                    "", 1000, "Mixto Entry Id"
                )

            else:
                if self.outer_self.mixto.entry_id is None:
                    self.outer_self.mixto.entry_id = idaapi.ask_str(
                        "", 1000, "Mixto Entry Id"
                    )

            if self.menu_title == MenuAllFunc:
                all_func = ""
                # Get count of all functions in the binary
                count = idaapi.get_func_qty()

                for i in range(count):
                    fn = idaapi.getn_func(i)

                    # Function should not have dummy name such as sub_*
                    # and should not start with underscore (possible library functions)
                    if not idaapi.has_dummy_name(
                        get_flags_at(start_ea_of(fn))
                    ) and not idaapi.get_func_name(start_ea_of(fn)).startswith("_"):
                        all_func += "{} @ 0x{:x}\n".format(
                            idaapi.get_func_name(start_ea_of(fn)), start_ea_of(fn)
                        )
                self.outer_self.mixto.AddCommit(
                    all_func, self.outer_self.mixto.entry_id, "(IDA) All Functions"
                )

            elif self.menu_title == MenuImports:
                global AllImports
                AllImports = ""
                # Get count of all import modules in the binary
                count = idaapi.get_import_module_qty()

                for i in range(count):
                    module_name = idaapi.get_import_module_name(i)

                    AllImports += "{}:\n".format(module_name)
                    idaapi.enum_import_names(i, imports_cb)
                self.outer_self.mixto.AddCommit(
                    AllImports, self.outer_self.mixto.entry_id, "(IDA) All Imports"
                )

            elif self.menu_title == MenuDecFunc:
                addr_current = idc.get_screen_ea()
                addr_func = idaapi.get_func(addr_current)

                if not addr_func:
                    idaapi.msg("Place cursor inside a function!")
                    return False
                else:
                    err = None
                    out = str(idaapi.decompile(addr_func))
                    # print(out)
                    self.outer_self.mixto.AddCommit(
                        str(out),
                        self.outer_self.mixto.entry_id,
                        "(IDA) Function Decompilation {}".format(
                            idc.GetFunctionName(addr_func.startEA)
                        ),
                    )

            elif self.menu_title == MenuExports:
                all_exports = ""
                for entry in idautils.Entries():
                    _, ord, ea, name = entry
                    if not name:
                        all_exports += "0x{:x}: ord#{}\n".format(ea, ord)
                    else:
                        all_exports += "0x{:x}: {} ord#{}\n".format(ea, name, ord)
                self.outer_self.mixto.AddCommit(
                    all_exports, self.outer_self.mixto.entry_id, "(IDA) All Exports"
                )

            elif self.menu_title == MenuAllComments:
                addr_current = idc.get_screen_ea()
                addr_func = idaapi.get_func(addr_current)

                uniq_comments = {}
                comments = []
                for ea in range(addr_func.startEA, addr_func.endEA):
                    comment = idaapi.get_cmt(ea, 0)
                    if comment is not None:
                        # hacky way to make sure only uniq comments are added
                        if uniq_comments.get(comment) == 1:
                            pass
                        else:
                            print(uniq_comments)
                            comments.append(
                                "{offset} {value}".format(offset=hex(ea), value=comment)
                            )
                            print("here")
                            uniq_comments[comment] = 1
                if len(comments) > 0:
                    out = "\n".join(comments)
                    self.outer_self.mixto.AddCommit(
                        str(out),
                        self.outer_self.mixto.entry_id,
                        "(IDA) Function Comments {}".format(
                            idc.GetFunctionName(addr_func.startEA)
                        ),
                    )

                else:
                    raise TypeError("No comments found")

            return True

        def update(self, ctx):
            return idaapi.AST_ENABLE_ALWAYS

    def run(self, arg):
        pass

    def term(self):
        pass


def PLUGIN_ENTRY():
    return mixto_t()
