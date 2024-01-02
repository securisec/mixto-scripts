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
                conf_path = str(os.path.expanduser("~/.mixto.json"))
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
            body = res.read()
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
            "/api/v1/commit",
            {
                "data": data,
                "commit_type": self.commit_type,
                "title": title,
                "entry_id": entry_id,
                "workspace_id": self.workspace_id,
            },
        )

    def GetEntryIDs(self):
        """Get entry ids, commits etc for a workspace

        Returns:
            List[dict]: Array of entry ids
        """
        return json.loads(
            self.MakeRequest("/api/v1/workspace", {"workspace_id": self.workspace_id})
        )


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
        # from ghidra.app.util import DisplayableEol
except:
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor
    # from ghidra.app.util import DisplayableEol


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
    return results.getDecompiledFunction().getC(), function


def sendToMixto(mixto, data, entryID, title):
    entry_id = entryID.split('id:')[1]
    mixto.AddCommit(data, entry_id, title)
    print("Commit added")


#
if __name__ == "__main__":

    mixto = MixtoLite()
    entries = mixto.GetEntryIDs()

    if len(entries) == 0:
        raise NoEntriesFound("No entries found")


    entries = ['{} id:{}'.format(w['title'], w["entry_id"]) for w in entries['data']['entries']]

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
            title = "(Ghidra) {} {} @0x{} decompiled".format(
                cp, fn.toString().encode(), fn.getEntryPoint()
            )
            data = "# {}\n{}".format(title, data)
            sendToMixto(mixto, data, entryID, title[0:79])

    # send a list of all functions
    elif choice == "All functions":
        hold = []
        for func in functionManager.getFunctions(True):
            fn, addr = func.getName(), func.getEntryPoint()
            if not fn.startswith("_"):
                # TODO
                # print([x.getFromAddress() for x in getReferencesTo(addr)])
                # print([GetFunctionName(functionManager, x.getFromAddress().getOffset()) for x in getReferencesTo(addr)])
                hold.append("{} @ 0x{}".format(fn, addr))
        if len(hold) > 0:
            data = "\n".join(hold)
            sendToMixto(
                mixto, data, entryID, "(Ghidra) All functions {}".format(cp)[0:79]
            )

    # send imports
    elif choice == "Imports":
        sm = currentProgram.getSymbolTable()
        symb = sm.getExternalSymbols()
        hold = {}
        for s in symb:
            parent = str(s.parentSymbol.toString())
            im = str(s.toString())
            if not im.startswith("_"):
                if parent not in hold:
                    hold[parent] = [im]
                else:
                    hold[parent].append(im)
        if len(hold) > 0:
            data = "\n\n".join(
                ["%s : \n\t%s" % (k, "\n\t".join(v)) for k, v in hold.items()]
            )
            sendToMixto(mixto, data, entryID, "(Ghidra) Imports {}".format(cp)[0:79])

    elif choice == "Exports":
        raise NotImplementedError("Exports not yet implemented TODO")

    elif choice == "Comments":
        listing = currentProgram.getListing()
        functionName = GetFunctionName(functionManager, GetCurrentAddress())
        try:
            func = getGlobalFunctions(functionName.toString())[0]
        except AttributeError:
            print("Not inside a function")
            exit()
        addrSet = func.getBody()
        codeUnits = listing.getCodeUnits(addrSet, True)

        comments = []
        commentTypes = {0: " EOL", 1: " PRE", 2: "POST"}

        for codeUnit in codeUnits:
            for k, v in commentTypes.items():
                comment = codeUnit.getComment(k)
                if comment is not None:
                    comment = comment.decode("utf-8")
                    if comment != "":
                        comments.append(
                            "0x{} - {} - {}".format(codeUnit.address, v, comment)
                        )
        if len(comments) > 0:
            data = "\n".join(comments)
            sendToMixto(mixto, data, entryID, "(Ghidra) Comments: {}".format(cp)[0:79])

    else:
        pass
