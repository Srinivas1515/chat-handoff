---
name: chat-handoff
description: Keeps a portable "handoff file" of a chat so the work can continue in a new chat or a different Claude account without re-explaining anything. Saves the conversation, decisions, preferences, and every input/output file into one zip, keeps a short always-fresh summary file after every reply, and resumes from that zip when it is uploaded. Make sure to use this skill whenever the user says "handoff", "save this chat", "I'm about to hit my limit", "ran out of credits", "continue my other chat", "switch accounts", "pick up where we left off", or uploads a file named HANDOFF.md or a handoff .zip. Also use it at the start of any long, file-heavy, multi-step project where losing context would hurt, even if the user never mentions limits.
---

# Chat Handoff

People often build up a lot of shared understanding with Claude in one chat (goals, preferences, corrections, uploaded files, drafts) and then hit a usage limit. Starting over in another account means re-teaching everything. This skill prevents that by keeping a small, well-organized "handoff bundle" up to date as the chat goes, and by reading that bundle in a new chat so Claude continues as if nothing happened.

Claude cannot see how close the person is to their limit, and a skill cannot run in the background. So the approach is: save small updates as you go, so there is never much to lose, plus a manual "handoff now" command.

## The bundle

One folder while working, one `.zip` when delivered:

```
handoff/
├── SUMMARY.md     human-readable recap: what we're doing, decisions, instructions
├── HANDOFF.md     cheap layer: resume instructions + current state + file index
├── LOG.md         full layer: append-only conversation log (read only when needed)
└── files/
    ├── inputs/    everything the person uploaded
    └── outputs/   everything Claude produced
```

The split matters because a new chat pays usage credits for everything it reads. If the new Claude had to read a whole long conversation just to catch up, the handoff would defeat its own purpose. So `HANDOFF.md` is short and sufficient on its own; `LOG.md` is the archive you dip into.

Use `scripts/handoff.py` for all file operations. It does each save in one command, which keeps credit use low. Work in `/mnt/user-data/outputs/handoff/` so the bundle can be shared.

## Mode 1: Save (starting and maintaining a handoff)

**Start.** At the first meaningful exchange of a project (or when the user asks), run:

```bash
python /mnt/skills/user/chat-handoff/scripts/handoff.py init /mnt/user-data/outputs/handoff --title "<short project name>"
```

If the skill lives elsewhere, use its actual path. Tell the person once, in one line, that you're keeping a handoff file for them and that they can say "handoff" anytime to get it.

**Every reply: refresh the summary and offer it for download.** `SUMMARY.md` is the one file that is updated and handed to the person after *every* reply, so they always hold a current recap even if the limit hits without warning. It is short on purpose (under ~40 lines), so doing this each turn is cheap. At the end of every reply in a chat where a handoff is active, write the summary to a temp file and run:

```bash
python .../handoff.py save /mnt/user-data/outputs/handoff \
  --summary-file /tmp/summary.md \
  --summary-out /mnt/user-data/outputs/CHAT_SUMMARY.md
```

then call `present_files` on `/mnt/user-data/outputs/CHAT_SUMMARY.md` and add nothing more about it in your reply (the file card is enough; repeating it every turn would be noise). Use this structure, rewriting the whole thing each time so it never gets stale or grows:

```markdown
## What we're working on
<1-3 sentences: the project and who it's for>

## Key decisions
- <settled choices, newest facts win over older ones>

## Instructions & preferences
- <rules the person gave: tone, format, things to avoid, corrections>

## What's happened so far
- <a few bullets of progress, files made>

## Where we are now / next step
<one or two lines>
```

Write it for a human skimming it in ten seconds, in plain words. It can be combined with the `save` call below when both are needed (one command is cheaper than two).

**Update the full handoff after each meaningful step**, not after every trivial message. A meaningful step is a decision, a correction from the person, a new or changed file, a finished deliverable, or a change of direction. Do the update in a single `save` call at the end of your turn, silently (don't narrate it):

```bash
python .../handoff.py save /mnt/user-data/outputs/handoff \
  --user "<what the person asked or decided, condensed>" \
  --claude "<what you did or answered, condensed, with file names>" \
  --state-file /tmp/state.md \
  --add "/mnt/user-data/uploads/brief.pdf" inputs "Client brief, source of truth" \
  --add "/mnt/user-data/outputs/draft_v2.docx" outputs "Current draft after round 2 edits"
```

`--add` takes three values: the file path, `inputs` or `outputs`, and a short note on what the file is (quote each, so any file name works). Re-adding a file with the same name refreshes its copy. Each flag is optional. Skip `--state-file` when the state hasn't changed, and skip `--add` when no file changed. Condense the log entries; the log is for recall, not a transcript dump. Keep verbatim anything where exact wording matters (a requested tone, a title, a number, a quoted instruction).

**What the state section must contain** (write it to a temp file, then pass with `--state-file`; it replaces the old state). This is the most important part of the whole skill, because it is all the next Claude will have by default:

- **Goal:** what the person is ultimately trying to achieve, and who the work is for.
- **Decisions made:** choices already settled, so they aren't reopened.
- **Preferences and style:** tone, format, length, things they like and things they dislike.
- **Corrections:** every time the person said "no, not like that", and what they wanted instead. These are the hardest things to re-learn and the most valuable to keep.
- **Done:** what is finished, with the file names.
- **In progress:** what is half-finished and where exactly it stopped.
- **Next step:** the single most likely next action, concrete enough to start on immediately.
- **Open questions:** anything unresolved or that you were unsure about.

Keep the state under roughly 60 lines. If it grows past that, compress older details rather than letting it bloat.

**Delivering the bundle.** Anything saved inside Claude's sandbox is only reachable by the person once you present it, so saving alone isn't enough. Bundle and present the zip:

```bash
python .../handoff.py bundle /mnt/user-data/outputs/handoff --out /mnt/user-data/outputs/handoff-<project>.zip
```

then call `present_files` on the zip. Do this:
- when the person says "handoff", "save", "I'm running low", or similar (do it immediately and keep the reply short, since they may be about to be cut off);
- at natural checkpoints, such as after finishing a major deliverable, so a recent copy exists even if the limit hits without warning;
- not on every turn: the zip is bigger and the summary file already covers the every-turn case.

If the person says they're near the limit, also reassure them in one sentence about exactly what to do next: download the zip, and upload it in the new chat.

**If the handoff folder is missing mid-chat** (for example the sandbox reset), rebuild it from the conversation you can see rather than failing: re-run `init`, write the state from what's in context, and re-add any files still on disk.

## Mode 2: Resume (a handoff was uploaded)

Trigger: the person uploads a `.zip` containing `HANDOFF.md`, or a bare `HANDOFF.md`, or a bare `SUMMARY.md` / `CHAT_SUMMARY.md`, or says they're continuing from another chat. A bare summary file carries less detail than a full zip: use it to re-orient, say plainly that finer details and the earlier files aren't available, and ask the person to re-upload any files you need. Then start a fresh handoff with `init` and carry the summary's content into the state.

1. Unpack: `python .../handoff.py unpack /mnt/user-data/uploads/<file>.zip /mnt/user-data/outputs/handoff` (skip for a bare `HANDOFF.md` or summary file; just read it).
2. Read **only** `HANDOFF.md` and `SUMMARY.md` (both short). Do not open `LOG.md` yet. Open it later only if you need a specific detail the state doesn't cover, and then search it (grep) instead of reading it all.
3. Run `python .../handoff.py verify /mnt/user-data/outputs/handoff` to check that every file in the index exists. Note any that are missing.
4. Reply to the person with a short re-orientation: the goal in one line, what's done, where you stopped, and what you plan to do next. Mention anything missing or uncertain. Ask them to confirm or correct. This step catches summary mistakes before they turn into wasted work, and it shows the person the context really did transfer.
5. Once confirmed, continue the work. Add a new line under "Sessions" in `HANDOFF.md` noting that a new session began, and from then on follow Mode 1 so the same bundle keeps growing.

If the file says it came from a chat with skills or tools this account doesn't have, adapt: do the same work with what's available and tell the person what differs.

## Mode 3: Continue across many handoffs

Keep the same project name and folder across handoffs so the bundle accumulates one coherent history. When state or log grows large, compress: fold old log detail into a short "Earlier history" paragraph at the top of the state, and keep the full text in `LOG.md`. The goal is that `HANDOFF.md` stays cheap to read no matter how long the project runs.

## Honest limits to tell the person

Say these plainly when relevant, since overpromising here would leave someone stranded at the worst moment:
- Claude can't detect the usage limit, so the safety net is frequent small saves plus the person saying "handoff" when they sense the limit is near.
- The summary file is only as fresh as the last reply. If the limit cuts a reply off, the person still has the summary from the reply before.
- A new chat knows only what the bundle contains. Claude does not truly remember the old chat, so unrecorded details will be lost.
- Very large files may be too big to bundle; if so, list them in the file index and tell the person to re-upload those directly.
