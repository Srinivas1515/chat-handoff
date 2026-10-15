# Chat Handoff — Claude Skill

**Save your context. Preserve your progress. Continue your work in a new chat.**

Chat Handoff is a Claude skill designed to preserve important project context across conversations.

It helps organize conversation summaries, decisions, user preferences, corrections, project state, and input/output files into a portable handoff bundle that can be used to resume work in a new chat.

The goal is to reduce the need to explain an entire project again whenever you start a new conversation or switch accounts.

## ✨ Features

* **Conversation Handoffs:** Prepare a portable bundle of important conversation context.
* **Project Summaries:** Maintain a concise summary of the current project and its progress.
* **Decision Tracking:** Preserve important decisions, preferences, and corrections.
* **File Organization:** Organize uploaded inputs and generated outputs.
* **Conversation Logs:** Keep a record of important project developments.
* **Resume Instructions:** Help a new chat understand the current state of a project.
* **Archive Management:** Use a Python helper script to initialize, save, bundle, unpack, and verify handoff files.
* **Multi-Session Continuity:** Carry project context across multiple conversations.

## 🎯 Who Is This For?

This skill is useful for:

* Claude users working on long projects
* Developers managing multi-step coding tasks
* Writers working on long documents
* Researchers organizing ongoing projects
* AI-assisted workflows that involve many files
* Users who need to continue work in a new chat or account

## 📦 Repository Structure

```text
chat-handoff/
├── README.md
├── SKILL.md
└── scripts/
    └── handoff.py
```

### File descriptions

* `SKILL.md` contains the main skill instructions.
* `scripts/handoff.py` provides helper operations for managing handoff files.
* `README.md` explains the project and its usage.

## 🚀 Installation

1. Download this repository using **Code → Download ZIP**.
2. Extract the downloaded archive.
3. Locate the `chat-handoff` skill folder.
4. Verify that `SKILL.md` and `scripts/handoff.py` are present.
5. Package the skill folder into a ZIP archive if your Claude interface requires it.
6. Follow the current Claude instructions for uploading and enabling custom skills.

Official Claude support documentation:

https://support.claude.com/

## 🧠 How It Works

Chat Handoff is designed around three operating modes.

### 1. Save

Create and maintain a handoff bundle containing important project context.

The bundle can include:

* `SUMMARY.md` — a short, current project summary
* `HANDOFF.md` — resume instructions, current state, and a file index
* `LOG.md` — a longer record of project developments
* `files/inputs/` — source files
* `files/outputs/` — generated files

The exact files depend on the workflow and the operations performed.

### 2. Resume

Upload a previously created handoff archive into a new chat.

The skill's instructions guide Claude to inspect the handoff information, understand the current project state, identify missing files, and continue from the previous stopping point.

### 3. Continue Across Multiple Handoffs

Maintain project continuity across successive conversations by updating the project state and preserving important historical details.

## 🛠️ Python Helper Script

The repository includes:

```text
scripts/handoff.py
```

The script provides commands for operations such as:

* `init` — initialize a handoff workspace
* `save` — update handoff information and manage files
* `bundle` — create a ZIP archive
* `unpack` — extract an existing handoff archive
* `verify` — check the handoff bundle's file index

The helper script is intended to be run in a compatible environment with Python available.

Refer to the skill instructions and the script's command-line help for the supported arguments and requirements.

## ⚠️ Important Notes

* A handoff can preserve only the information and files that have actually been captured.
* The skill cannot independently detect when a user is about to reach a usage limit.
* A new chat does not automatically remember an old conversation; the handoff must be provided to it.
* File paths and available tools may differ between environments. Commands in the skill instructions may need to be adapted to the environment where the skill is running.
* Keep sensitive information, credentials, and confidential project files out of public handoff archives.

## 🧪 Testing

Before relying on a handoff, verify that:

1. The bundle can be created.
2. The ZIP archive can be extracted.
3. The handoff files are present.
4. The file index matches the actual files.
5. A new chat can understand the saved project state.
6. Important decisions and the next steps are preserved.

## 🤝 Contributions

Suggestions, bug reports, and improvements are welcome.

If you modify the skill, test the changes before publishing an updated version.

## 📄 License

No license has been specified for this project yet.

Check the repository's licensing terms before redistributing, modifying, or incorporating this skill into other projects.
