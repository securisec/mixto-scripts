import { Notice, Plugin, TFolder } from "obsidian";
import { MixtoLite } from "./mixto";
import { MixtoResponse } from "./types";

export default class MyPlugin extends Plugin {
	async onload() {
		// register mixto commands
		this.addCommand({
			id: "mixto-open-workspace",
			name: "Open current mixto workspace",
			callback: () => {
				this.showWorkspaceData();
			},
		});
	}

	onunload() {
		// TODO 🔥
	}

	async showWorkspaceData() {
		try {
			const mixto = new MixtoLite();
			if (!mixto.workspace_id) {
				new Notice(mixto.workspace_id ?? "Cannot load workspace");
				return;
			}

			// get mixto workspace name
			const workspaceName = await this.getWorkspaceName(mixto);
			if (!workspaceName) {
				this.showErrorNotice("Cannot get workspace name");
				return;
			}

			// Ensure `this.app` is accessible
			if (!this.app) {
				new Notice("App instance not available");
				return;
			}

			const mixtoFolderPath = `[ Mixto ] ${workspaceName}`;
			const { vault } = this.app;

			// Get all folders
			const folders = this.app.vault
				.getAllLoadedFiles()
				.filter((file) => file instanceof TFolder)
				.filter((folder) => folder.path.startsWith(mixtoFolderPath));

			if (folders.length === 0) {
				await this.app.vault.createFolder(mixtoFolderPath);
			}

			let filesInFolder =
				vault.getFolderByPath(mixtoFolderPath)?.children;
			if (filesInFolder && filesInFolder.length > 0) {
				this.showErrorNotice("Data already exists");
				return;
			}

			// get mixto data
			const workspaceData = await this.getWorkspaceData(mixto);

			// create entries
			workspaceData.workspace.entries.map(async (entry) => {
				const page = `${mixtoFolderPath}/${entry.title}.md`;
				let content = "";
				entry.merged_data.map(async (entryData) => {
					let title = `## ${entryData.title}\n`;
					content = content + title + entryData.data + "\n\n";
				});
				await vault.create(page, content);
			});
		} catch (error) {
			new Notice(error);
		}
	}

	showErrorNotice(msg: string) {
		new Notice(msg);
	}

	async getWorkspaceName(mixto: MixtoLite): Promise<string> {
		const query = `query q($workspace_id: uuid!) {
  workspace: mixto_workspaces_by_pk(workspace_id: $workspace_id) {
    workspace_name
  }
}
`;
		const { workspace } = (
			await mixto.GraphQL(query, { workspace_id: mixto.workspace_id })
		).data as MixtoResponse.Data;
		return workspace.workspace_name;
	}

	async getWorkspaceData(mixto: MixtoLite): Promise<MixtoResponse.Data> {
		const query = `query q($workspace_id: uuid!) {
  workspace: mixto_workspaces_by_pk(workspace_id: $workspace_id) {
    workspace_name
    entries {
      title
      merged_data(where: {commit_type: {_nin: ["image", "asciinema"]}}, order_by: {created_at: desc}) {
        title
        data
        created_at
        data_type
        commit_type
      }
    }
  }
}
`;
		return (
			await mixto.GraphQL(query, { workspace_id: mixto.workspace_id })
		).data as MixtoResponse.Data;
	}
}
