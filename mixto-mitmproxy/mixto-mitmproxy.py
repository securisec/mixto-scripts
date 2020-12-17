"""Script to integrate Mixto with mitmproxy"""
from os import getenv
from typing import Any
from mixto import Mixto
from mitmproxy import ctx, flow
from mitmproxy.command import command
import mitmproxy.net.http.http1.assemble as assemble
from mitmproxy.addons.export import curl_command, httpie_command

__version__ = "1.0.0"
__author__ = "Hapsida @securisec"


class mixtoMitmproxy:
    def __init__(self):
        self.mixto = Mixto()
        self.mixto.commit_type = "tool"
        self.mitm_host = None
        self.mitm_method = None

    def _send_to_mixto(self, data: Any, title_postfix: str, flow: flow.Flow):
        """Post data to Mixto server

        Args:
            data (Any): Data
            title_postfix (str): Title for commit
            flow (flow.Flow): mitmproxy flow
        """
        mixto_entry_id = ctx.options.mixto_entry_id
        checkEnv = getenv("MIXTO_ENTRY_ID")
        if checkEnv is not None:
            mixto_entry_id = checkEnv
        if mixto_entry_id == "":
            print("Entry ID not specified")
            return
        self.mixto.commitAdd(
            entry_id=mixto_entry_id,
            title="mitmproxy: {} {} - {}".format(
                self.mitm_method, self.mitm_host[0:60], title_postfix
            ),
            data="{}\n{}\nCurl:\n{}\n\nHttpie:\n{}".format(
                data, "-" * 20, curl_command(flow), httpie_command(flow)
            ),
        )
        print("\nSent!")

    def load(self, loader):
        loader.add_option(
            name="mixto_entry_id",
            typespec=str,
            default="",
            help="The entry ID to commit data to",
        )

    @command("mixto.request")
    def req(self, flow: flow.Flow) -> None:
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self._send_to_mixto(
            assemble.assemble_request(flow.request).decode("utf-8", errors="ignore"),
            "request",
            flow,
        )

    @command("mixto.req_header")
    def req_header(self, flow: flow.Flow) -> None:
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self._send_to_mixto(
            assemble.assemble_request_head(flow.request).decode(
                "utf-8", errors="ignore"
            ),
            "req-header",
            flow,
        )

    @command("mixto.res_header")
    def res_header(self, flow: flow.Flow) -> None:
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self._send_to_mixto(
            assemble.assemble_response_head(flow.response).decode(
                "utf-8", errors="ignore"
            ),
            "res-header",
            flow,
        )

    @command("mixto.response")
    def res(self, flow: flow.Flow) -> None:
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self._send_to_mixto(
            assemble.assemble_response(flow.response).decode("utf-8", errors="ignore"),
            "response",
            flow,
        )

    @command("mixto.full")
    def full(self, flow: flow.Flow) -> None:
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        reqdata = assemble.assemble_request(flow.request).decode(
            "utf-8", errors="ignore"
        )
        resdata = assemble.assemble_response(flow.response).decode(
            "utf-8", errors="ignore"
        )
        data = "\n\n\n".join([reqdata, resdata])
        self._send_to_mixto(data, "req,res", flow)


addons = [mixtoMitmproxy()]
