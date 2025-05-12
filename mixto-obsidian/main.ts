import { FrontMatterCache, Notice, Plugin, TFolder } from "obsidian";
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

		this.addCommand({
			id: "mixto-sync-entry-note",
			name: "Sync current document to Mixto",
			callback: () => {
				this.syncDocumentAsNote();
			},
		});
	}

	onunload() {
		// TODO 🔥
	}

	async syncDocumentAsNote() {
		const mixto = new MixtoLite();
		if (!mixto.workspace_id) {
			new Notice(mixto.workspace_id ?? "Cannot load workspace");
			return;
		}

		// get entry_id from front matter
		const file = this.app.workspace.getActiveFile();
		var frontmatter: FrontMatterCache | undefined = undefined;
		var entryID: string;
		var noteID: string = "";
		if (file) {
			const metadata = this.app.metadataCache.getFileCache(file);
			if (metadata && metadata.frontmatter) {
				// get the needed infromation from frontmatter
				frontmatter = metadata.frontmatter;
				entryID = frontmatter.mixto_entry_id;
				noteID = frontmatter.mixto_note_id;
				if (!entryID) {
					this.showErrorNotice("Entry id not found");
					return;
				}
			}
		}
		// found entry_id so we will sync the document if it has content
		let content = await this.app.vault.read(file!);
		content = content.replace(/^---\n[\s\S]*?\n---\n*/, "");

		if (!noteID) {
			// note has never been synced so create a new note
			// add note content
			const mutation = `mutation m(
		$data: String!
		$workspace_id: uuid!
		$entry_id: String!
		$text: String = "obsidian"
		$title: String!
	) {
		note: insert_mixto_notes_one(
			object: {
				data: $data
				title: $title
				entry_id: $entry_id
				markdown: true
				workspace_id: $workspace_id
				tags_notes: {
					data: { text: $text, workspace_id: $workspace_id, entry_id: $entry_id }
				}
			}
		) {
			note_id
		}
	}`;
			const variables = {
				entry_id: entryID!,
				workspace_id: mixto.workspace_id,
				data: content,
				title: file?.name || "Untitled",
			};
			await mixto
				.GraphQL(mutation, variables)
				.catch(this.showErrorNotice)
				.then((res) => {
					noteID = res!.data!.note.note_id;
					this.showErrorNotice("Note synced");
				});
			// update the front matter with the last synced time
			this.app.fileManager.processFrontMatter(file!, (fm) => {
				fm.mixto_updated_at = new Date();
				// set note_id front matter
				fm.mixto_note_id = noteID!;
			});
		} else {
			// note already synced, so update it instead
			const mutation = `mutation m($note_id: uuid!, $data: String!) {
	update_mixto_notes_by_pk(pk_columns: {note_id: $note_id}, _set: {data: $data}) {
		note_id
	}
}
`;
			const variables = { note_id: noteID, data: content };
			await mixto
				.GraphQL(mutation, variables)
				.then((res) => {
					this.app.fileManager.processFrontMatter(file!, (fm) => {
						fm.mixto_updated_at = new Date();
					});
					this.showErrorNotice("Note updated");
				})
				.catch(this.showErrorNotice);
		}
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
      merged_data(where: {commit_type: {_nin: ["image", "asciinema", "file"]}}, order_by: {created_at: desc}) {
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
