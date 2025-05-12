import { existsSync, readFileSync } from "fs";
import { homedir } from "os";
import * as path from "path";
import * as http from "http";
import * as https from "https";

export class MixtoLite {
	host: string | undefined;
	api_key: string | undefined;
	workspace_id: string | undefined;

	/**
	 *Creates an instance of MixtoLite.
	 * @param {string} [host] The host URL.
	 * @param {string} [apiKey] A valid API key
	 * @memberof MixtoLite
	 */
	constructor(host?: string, apiKey?: string) {
		this.host = host;
		this.api_key = apiKey;
		this.workspace_id = undefined;

		if (!this.host) {
			this.host = process.env.MIXTO_HOST;
		}
		if (!this.api_key) {
			this.api_key = process.env.MIXTO_API_KEY;
		}
		// if host and api key is still empty, read config file
		if (!this.host || !this.api_key) {
			const confPath = path.join(homedir(), ".mixto.json");
			if (!existsSync(confPath)) {
				throw new Error("Mixto config file not found");
			}
			const config = JSON.parse(readFileSync(confPath, "utf-8"));
			this.host = config.host;
			this.api_key = config.api_key;
			this.workspace_id = config.workspace_id;
		}
	}

	/**
	 *A generic request handler that allows making requests 
	 to the Mixto API easy.
	 *
	 * @param {string} endpoint The URI. Example: /api/entry/...
	 * @param {http.RequestOptions} options Request options. Needed 
	 * when building a custom request to the API
	 * @param {*} [data] Data object to send as JSON
	 * @param {*} [query] Query params as an object
	 * @returns Thenable string
	 * @memberof MixtoLite
	 */
	MakeRequest(
		endpoint: string,
		options: http.RequestOptions,
		data?: any,
		query?: any
	) {
		return new Promise((resolve, reject) => {
			const url = new URL(endpoint, this.host);
			if (query) {
				Object.keys(query).map((k) =>
					url.searchParams.append(k, query[k])
				);
			}
			options.headers = {
				"x-api-key": this.api_key,
				"content-type": "application/json",
				"user-agent": "mixto-lite-node",
			};
			const bufferData = Buffer.from(data);
			if (data) {
				options.headers["content-length"] = bufferData.length;
			}
			const reqLib = url.protocol === "https:" ? https : http;
			const req = reqLib.request(url.toString(), options, (res) => {
				var body: any[] = [];
				if (res.statusCode) {
					if (res.statusCode < 200 || res.statusCode >= 300) {
						return reject(
							new Error(`Bad response: ${res.statusCode}`)
						);
					}
				}
				res.on("data", (c) => body.push(c));
				res.on("end", () => {
					resolve(Buffer.concat(body).toString());
				});
				res.on("error", () =>
					reject(`Bad response: ${res.statusCode}`)
				);
			});
			if (bufferData) {
				req.write(bufferData);
			}
			req.end();
		});
	}

	/**
	 *Get an array of all workspaces, entries and commits. 
	 Helpful when creating builders to select an entry.
	 *
	 * @returns {Promise<Workspace[]>} Thenable array of workspaces
	 * @memberof MixtoLite
	 */
	GetWorkspaces(): Promise<Workspace[]> {
		return this.MakeRequest(
			`/api/v1/workspace`,
			{ method: "GET" },
			null
		).then((d) => {
			return JSON.parse(d as any).data as Workspace[];
		});
	}

	/**
	 *Get all entry ids filtered by current workspace.
	 *
	 * @param {boolean} [includeCommits] Include all commits in response
	 * @returns {Promise<Entry[]>}
	 * @memberof MixtoLite
	 */
	async GetEntryIDs(includeCommits: boolean = false): Promise<Entry[]> {
		let body = JSON.stringify({
			workspace_id: this.workspace_id,
			include_commits: includeCommits,
		});
		return this.MakeRequest(
			`/api/v1/workspace`,
			{ method: "POST" },
			body
		).then((res: any) => {
			return JSON.parse(res).data.entries;
		});
	}

	/**
	 *Add a commit to an entry
	 *
	 * @param {*} data Data to commit
	 * @param {string} [entry_id] A valid entry ID
	 * @param {string} [title] Title for the entry. Optional. Defaults
	 * to untitled
	 * @returns {Promise<Commit>} Thenable Commit object
	 * @memberof MixtoLite
	 */
	AddCommit(data: any, entry_id?: string, title?: string): Promise<Commit> {
		if (!entry_id && !process.env.MIXTO_ENTRY_ID) {
			throw new Error("Entry ID not specified");
		}
		let body = JSON.stringify({
			data: data,
			commit_type: "tool",
			title: title,
			workspace_id: this.workspace_id,
			entry_id: entry_id,
			meta: {},
		});
		return this.MakeRequest(
			`/api/v1/commit`,
			{ method: "POST" },
			body
		).then((d) => {
			return JSON.parse(d as any) as Commit;
		});
	}

	/**
	 * Make a generic graphql request to the mixto server
	 * @param query gql query
	 * @param variables optional variables
	 * @returns {Promise<GQLResponse>} Thenable GQLResponse object
	 */
	GraphQL(query: string, variables?: any): Promise<GQLResponse> {
		let body: any = { query: query };
		if (variables) {
			body["variables"] = variables;
		}
		return this.MakeRequest(
			"/api/v1/gql",
			{ method: "POST" },
			JSON.stringify(body)
		).then((d) => {
			return JSON.parse(d as any) as GQLResponse;
		});
	}
}

export interface Workspace {
	workspace_id: string;
	workspace_name: string;
}

export interface Entry {
	entry_id: string;
	title: string;
	commits?: Commit[];
}

export interface Commit {
	commit_it: string;
	title: string;
	type: string;
}

export interface GQLResponse {
	data?: {
		[key: string]: any;
	};
	error?: any;
}
