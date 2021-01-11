"""Script to integrate Mixto with mitmproxy"""
from mitmproxy import ctx, flow
from mitmproxy.command import command
import mitmproxy.net.http.http1.assemble as assemble
from mitmproxy.addons.export import curl_command, httpie_command
from mixto import MixtoLite

__version__ = "1.0.0"
__author__ = "Hapsida @securisec"


class mixtoMitmproxy:
    def __init__(self):
        self.mixto = MixtoLite()
        self.mixto.commit_type = "tool"
        self.mitm_host = None
        self.mitm_method = None

    def _get_data(self, data, flow):
        return "{}\n\n{}\nCurl:\n{}\n\nHttpie:\n{}".format(
            data, "-" * 20, curl_command(flow), httpie_command(flow)
        )

    def _get_title(self, title_postfix: str):
        return "mitmproxy: {} {} - {}".format(
            self.mitm_method, self.mitm_host[0:60], title_postfix
        )

    def load(self, loader):
        loader.add_option(
            name="mixto_entry_id",
            typespec=str,
            default="",
            help="The entry ID to commit data to",
        )

    def get_entry_id(self):
        mixto_entry_id = ctx.options.mixto_entry_id
        if not mixto_entry_id:
            raise "Missing Entry ID"
        return mixto_entry_id

    @command("mixto.request")
    def req(self, flow: flow.Flow) -> None:
        mixto_entry_id = self.get_entry_id()
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self.mixto.AddCommit(
            data=self._get_data(
                assemble.assemble_request(flow.request).decode(
                    "utf-8", errors="backslashreplace"
                ),
                flow,
            ),
            entry_id=mixto_entry_id,
            title=self._get_title("request"),
        )
        print("Sent!")

    @command("mixto.request_header")
    def req_header(self, flow: flow.Flow) -> None:
        mixto_entry_id = self.get_entry_id()
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self.mixto.AddCommit(
            data=self._get_data(
                assemble.assemble_request_head(flow.request).decode(
                    "utf-8", errors="backslashreplace"
                ),
                flow,
            ),
            entry_id=mixto_entry_id,
            title=self._get_title("request.header"),
        )
        print("Sent!")

    @command("mixto.response_header")
    def res_header(self, flow: flow.Flow) -> None:
        mixto_entry_id = self.get_entry_id()
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self.mixto.AddCommit(
            data=self._get_data(
                assemble.assemble_response_head(flow.response).decode(
                    "utf-8", errors="backslashreplace"
                ),
                flow,
            ),
            entry_id=mixto_entry_id,
            title=self._get_title("response.header"),
        )
        print("Sent!")

    @command("mixto.response")
    def res(self, flow: flow.Flow) -> None:
        mixto_entry_id = self.get_entry_id()
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        self.mixto.AddCommit(
            data=self._get_data(
                assemble.assemble_response(flow.response).decode(
                    "utf-8", errors="backslashreplace"
                ),
                flow,
            ),
            entry_id=mixto_entry_id,
            title=self._get_title("response"),
        )
        print("Sent!")

    @command("mixto.full")
    def full(self, flow: flow.Flow) -> None:
        mixto_entry_id = self.get_entry_id()
        self.mitm_method = flow.request.method
        self.mitm_host = flow.request.host
        reqdata = assemble.assemble_request(flow.request).decode(
            "utf-8", errors="backslashreplace"
        )
        resdata = assemble.assemble_response(flow.response).decode(
            "utf-8", errors="backslashreplace"
        )
        data = "\n\n\n".join([reqdata, resdata])
        self.mixto.AddCommit(
            data=self._get_data(data, flow),
            entry_id=mixto_entry_id,
            title=self._get_title("request.response"),
        )
        print("Sent!")

    @command("mixto.cert")
    def certificate(self, flow: flow.Flow) -> None:
        try:
            mixto_entry_id = self.get_entry_id()
            self.mitm_method = flow.request.method
            self.mitm_host = flow.request.host
            server = flow.server_conn
            client = flow.client_conn
            addr = server.ip_address
            data = "Server Host: {}\n".format(flow.request.host)
            data += "Server Address: {}:{}\n\n".format(addr[0], addr[1])
            data += "X509 Certificate:\n{}\n\n".format(
                client.mitmcert.to_pem().decode("utf-8", errors="backslashreplace")
            )
            data += "OpenSSL command: openssl x509 -in cert.pem -text"
            self.mixto.AddCommit(
                data=data, title=self._get_title("certificate"), entry_id=mixto_entry_id
            )
            print("Sent!")
        except Exception as e:
            if hasattr(e, "message"):
                ctx.log.error(e.message)
            else:
                ctx.log.error(e)


addons = [mixtoMitmproxy()]
