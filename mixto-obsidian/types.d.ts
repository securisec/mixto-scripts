export namespace MixtoResponse {
	export interface MixtoWorkspaceResponse {
		data: Data;
	}

	export interface Data {
		workspace: Workspace;
	}

	export interface Workspace {
		workspace_name: string;
		entries: Entry[];
	}

	export interface Entry {
		title: string;
		merged_data: MergedDatum[];
	}

	export interface MergedDatum {
		title: string;
		data: string;
		created_at: Date;
		data_type: DataType;
		commit_type: string;
	}

	export type DataType = "notes" | "commits";
}
