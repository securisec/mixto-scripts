# mixto-mitmproxy
`mixto-mitmproxy` is a [mitmproxy](https://mitmproxy.org/) addon script for Mixto. It is a simple python script that can be run against a *flow* in mitmproxy to send various data to the `Mixto` server. 

## Dependencies (python)
- mixto

#### Init
All plugins/extensions/modules relies on the local `.mixto.json` file to get its config variables. To set up the config file, run
```
mixto init -k yourapikey [--host mixtohost]
```

## Env
> If the environment variable `MIXTO_ENTRY_ID` is set, it always takes precedence over anything else set.

## Usage
Start mitmproxy with `mixto-mitmproxy.py` as a script argument and pass the `mixto_entry_id` to the Mixto entry as a paramter. Example:
```
mitmproxy -s mixto-mitmproxy.py --set mixto_entry_id=some_entry_abcd
```

This will initialize mitmproxy with the `mixto-mitmproxy.py` script which can then be run against any **individual** flows. This will work even if a flow has been modified or intercepted. 

The options for `mixto-mitmproxy` can be accessed directly from the mitmproxy interface using the `O` option. All options are prefixed with `mixto_...`

To process and send a particular set of data to the Mixto server, run the addons appropiate command. Make sure to use `@focus` to app this to a single flow. Example:
```
: mixto.request @focus
```

The available commands are:
- **mixto.request**: Send the request to the Mixto server
- **mixto.res_header**: Send the request header to the Mixto server 
- **mixto.response**: Send the response to the Mixto server
- **mixto.res_header**: Send the response header to the Mixto server
- **mixto.reqres**: Send both request/response to the Mixto server
