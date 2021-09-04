# Not used for commiting data
# @author Hapsida @securisec
# @category Integrate
# @keybinding Shift-M
# @menupath Tools.Mixto
# @toolbar


# Mixto python2 lite sdk
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
                conf_path = str(os.path.expanduser("~/.mixto.json"))
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
            "/api/entry/{}/commit".format(e_id),
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


"""
Mixto Ghidra plugin
Reference: https://github.com/HackOvert/GhidraSnippets
"""
try:
    import typing
    if typing.TYPE_CHECKING:
        import ghidra
        from ghidra.ghidra_builtins import *
        from ghidra.app.decompiler import DecompInterface
        from ghidra.util.task import ConsoleTaskMonitor
        from ghidra.app.util import DisplayableEol
except:
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor
    from ghidra.app.util import DisplayableEol



def GetCurrentAddress():
    """Returns the current cursor address as int"""
    return int(currentAddress.toString(), 16)


def GetFunctionAddress(offset):
    """Get the Ghidra compitable function address"""
    return (
        currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(offset)
    )


def GetFunctionName(functionManager, offset):
    """Get current function name"""
    return functionManager.getFunctionContaining(GetFunctionAddress(offset))


class NoEntriesFound(BaseException):
    pass


def GetDecompiled(functionManager):
    functionName = GetFunctionName(functionManager, GetCurrentAddress())
    program = getCurrentProgram()
    ifc = DecompInterface()
    ifc.openProgram(program)

    # here we assume there is only one function named `main`
    function = getGlobalFunctions(functionName.toString())[0]

    # decompile the function and print the pseudo C
    results = ifc.decompileFunction(function, 0, ConsoleTaskMonitor())
    return results.getDecompiledFunction().getC(), functionName


def sendToMixto(mixto, data, entryID, title):
    mixto.AddCommit(data, entryID, title)
    print("Commit added")


#
if __name__ == "__main__":

    mixto = MixtoLite()
    workspaces = mixto.GetWorkspaces()
    workspaces = json.loads(workspaces)

    entries = [w["entry_id"] for w in workspaces if w["workspace"] == mixto.workspace]

    if len(entries) == 0:
        raise NoEntriesFound("no entries found")

    choice = askChoice(
        "Select operation",
        "",
        ["Decompile function", "Comments", "All functions", "Imports", "Exports"],
        "Decompile function",
    )
    entryID = askChoice("Select Mixto Entry", "", entries, "")

    cp = str(getCurrentProgram().toString())
    functionManager = currentProgram.getFunctionManager()

    # send decompiled function
    if choice == "Decompile function":
        data, fn = GetDecompiled((functionManager))
        if data:
            sendToMixto(
                mixto, data, entryID, "(Ghidra) {} {} decompiled".format(cp, fn)
            )

    # send a list of all functions
    elif choice == "All functions":
        hold = []
        for func in functionManager.getFunctions(True):
            fn, addr = func.getName(), func.getEntryPoint()
            if not fn.startswith("_"):
                hold.append("{} @ 0x{}".format(fn, addr))
        if len(hold) > 0:
            data = "\n".join(hold)
            sendToMixto(mixto, data, entryID, "(ghidra) All functions {}".format(cp))

    # send imports
    elif choice == "Imports":
        sm = currentProgram.getSymbolTable()
        symb = sm.getExternalSymbols()
        hold = []
        for s in symb:
            parent = str(s.parentSymbol.toString())
            im = str(s.toString())
            if not im.startswith("_"):
                hold.append("{} - {}".format(parent, im))
        if len(hold) > 0:
            data = "\n".join(hold)
            sendToMixto(mixto, data, entryID, "(ghidra) Imports {}".format(cp))

    elif choice == "Exports":
        raise NotImplementedError("Exports not yet implemented TODO")

    elif choice == "Comments":
        raise NotImplementedError("Comments not yet implemented TODO")

    else:
        pass
