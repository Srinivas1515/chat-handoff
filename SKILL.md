---
name: chat-handoff
description: Use in EVERY conversation, short or long, whatever the topic. Keeps a short summary file after every reply and builds a portable "handoff" zip of the whole chat (conversation, decisions, preferences, every input and output file) so work can continue in a new chat or another Claude account without re-explaining anything. Works even when started mid-chat, by rebuilding the earlier history and files. Make sure to use this skill whenever the user says "handoff", "save this chat", "I'm about to hit my limit", "ran out of credits", "continue my other chat", "switch accounts", "pick up where we left off", "stop summaries", or uploads a file named HANDOFF.md, SUMMARY.md, CHAT_SUMMARY.md, or a handoff .zip.
Chat Handoff
People build up a lot of shared understanding with Claude in one chat (goals, preferences, corrections, uploaded files, drafts) and then hit a usage limit. Starting over in another account means re-teaching everything. This skill prevents that by keeping a small, organized handoff bundle up to date, and by reading that bundle in a new chat so Claude continues as if nothing happened.
Claude cannot see how close the person is to their limit, and a skill cannot run in the background. So the design is: a tiny summary refreshed every reply, small saves as the work progresses, and a "handoff" command that produces the complete zip.
The bundle
One folder while working, one `.zip` when delivered:
```
handoff/
├── SUMMARY.md     human-readable recap: what we're doing, decisions, instructions
├── HANDOFF.md     cheap layer: resume instructions + current state + file index + gaps
├── LOG.md         full layer: earlier history (condensed) + append-only log
└── files/
    ├── inputs/    everything the person uploaded
    └── outputs/   everything Claude produced
```
The split matters because a new chat pays usage credits for whatever it reads. `HANDOFF.md` is short and sufficient on its own; `LOG.md` is an archive to search, not to read in full.
Use `scripts/handoff.py` (in this skill's folder; below it is written as `.../handoff.py`, so use its real path) for all file operations. It does each save in one command, which keeps credit use low. Work in `/mnt/user-data/outputs/handoff/`.
When this skill is active
It applies to every chat, from the first reply, no matter how short or small. Do not wait for the chat to get long or file-heavy. If the person says "stop summaries", pause the per-reply summary (and say so in one short line); resume if they say "resume summaries" or ask for a handoff. The handoff command always works, even while paused.
Mode 1: Save
First activation
On your first reply in a chat, run `init`:
```bash
python .../handoff.py init /mnt/user-data/outputs/handoff --title "<short project name>"
```
Tell the person once, in one line, that you're keeping a summary and a handoff file, and that they can say "handoff" anytime for the full zip.
If the chat already has history (the skill started mid-chat, for example it was installed or triggered partway through), rebuild the past immediately, in this same first reply, not later at handoff time, because the rebuild itself could be cut off by a limit:
Read back through everything still visible in the conversation.
Write a condensed account of the earlier part to a temp file: the person's requests, decisions, corrections, what was produced and when. Keep word for word any instruction where exact wording matters (tone requests, titles, numbers, rules, corrections). Do not copy long passages of earlier replies; condense them. Pass it with `--backfill-file`.
Add every earlier file: run `sync` (below), which finds everything in the uploads and outputs folders. Then refine notes by re-adding important files with `--add` and a meaningful note.
Record anything you could not recover with `--gap "<what is missing and why>"` (for example a file made earlier that no longer exists on disk, or a part of the conversation no longer visible). Never silently skip a gap; the next Claude and the person must know.
Build the state and the summary (below) from the full picture.
```bash
python .../handoff.py save /mnt/user-data/outputs/handoff \
  --backfill-file /tmp/earlier.md \
  --state-file /tmp/state.md \
  --summary-file /tmp/summary.md --summary-out /mnt/user-data/outputs/CHAT_SUMMARY.md \
  --gap "draft_v0.docx was created earlier but is no longer on disk"
python .../handoff.py sync /mnt/user-data/outputs/handoff
```
Every reply: refresh the summary and offer it for download
`SUMMARY.md` is updated and handed to the person after every reply, so they always hold a current recap even if a limit hits without warning. It is short on purpose (under ~40 lines), so doing it each turn is cheap. At the end of every reply, write the summary to a temp file and run:
```bash
python .../handoff.py save /mnt/user-data/outputs/handoff \
  --summary-file /tmp/summary.md \
  --summary-out /mnt/user-data/outputs/CHAT_SUMMARY.md
```
Then call `present_files` on `/mnt/user-data/outputs/CHAT_SUMMARY.md` and say nothing further about it (the file card is enough). Use this structure, rewriting the whole thing each time so it never goes stale or grows:
```markdown
## What we're working on
<1-3 sentences: the project and who it's for>

## Key decisions
- <settled choices; newer facts win over older ones>

## Instructions & preferences
- <rules the person gave: tone, format, things to avoid, corrections>

## What's happened so far
- <a few bullets of progress, files made>

## Where we are now / next step
<one or two lines>
```
Even in a tiny chat, fill it in honestly (a two-message chat gets a two-line summary). Write for a human skimming it in ten seconds. When a full save is also due, put both in one `save` command; one command is cheaper than two.
After each meaningful step: update the full handoff
A meaningful step is a decision, a correction, a new or changed file, a finished deliverable, or a change of direction (not every trivial message). Do it in a single `save` call at the end of your turn, silently:
```bash
python .../handoff.py save /mnt/user-data/outputs/handoff \
  --user "<what the person asked or decided, condensed>" \
  --claude "<what you did or answered, condensed, with file names>" \
  --state-file /tmp/state.md \
  --add "/mnt/user-data/uploads/brief.pdf" inputs "Client brief, source of truth" \
  --add "/mnt/user-data/outputs/draft_v2.docx" outputs "Current draft after round 2 edits"
```
`--add` takes three values: file path, `inputs` or `outputs`, and a note on what the file is (quote each, so any file name works). Re-adding a file refreshes its copy. Every flag is optional. Condense log entries (the log is for recall, not a transcript dump), but keep verbatim anything where exact wording matters.
The state section (`--state-file`; it replaces the old state) is the most important part of the skill, because it is all the next Claude reads by default. It must contain:
Goal: what the person ultimately wants, and who the work is for.
Decisions made: settled choices, so they aren't reopened.
Preferences and style: tone, format, length, likes and dislikes.
Corrections: every time the person said "no, not like that", and what they wanted instead. These are the hardest things to re-learn.
Done / In progress: what is finished (with file names) and exactly where unfinished work stopped.
Next step: the single most likely next action, concrete enough to start immediately.
Open questions: anything unresolved or uncertain.
Keep it under roughly 60 lines; compress older detail instead of letting it bloat.
Handoff on command (the complete zip)
When the person says "handoff", "save", "I'm running low", or similar, act immediately and keep the reply short, since they may be cut off any moment. The zip must contain the entire chat from the very first message, not just the part after the skill started:
If no handoff folder exists yet, or the earlier history was never backfilled, do the full first-activation rebuild above now.
Run `sync` so that every uploaded and generated file still on disk is in the bundle, even ones missed earlier.
Run `verify` and fix or record (`--gap`) anything missing.
Do a final `save` with the latest state and summary.
Bundle and present:
```bash
python .../handoff.py sync /mnt/user-data/outputs/handoff
python .../handoff.py verify /mnt/user-data/outputs/handoff
python .../handoff.py bundle /mnt/user-data/outputs/handoff --out /mnt/user-data/outputs/handoff-<project>.zip
```
then `present_files` on the zip. Also give the zip at natural checkpoints (after a major deliverable). One closing sentence: download the zip, upload it in the new chat. If anything went into the Gaps section, say so plainly.
Files saved in the sandbox are only reachable by the person once presented, so always present; saving alone is not enough.
If the handoff folder disappears mid-chat (a sandbox reset), rebuild it from the conversation you can see rather than failing.
Mode 2: Resume (a handoff was uploaded)
Trigger: the person uploads a `.zip` containing `HANDOFF.md`, a bare `HANDOFF.md`, a bare `SUMMARY.md` or `CHAT_SUMMARY.md`, or says they're continuing from another chat.
Unpack: `python .../handoff.py unpack /mnt/user-data/uploads/<file>.zip /mnt/user-data/outputs/handoff` (skip for a bare file; just read it).
Read only `HANDOFF.md` and `SUMMARY.md` (both short). Do not open `LOG.md` yet; search it (grep) only when you need a specific detail.
Run `python .../handoff.py verify /mnt/user-data/outputs/handoff`. Note anything missing, and read the Gaps section.
Reply with a short re-orientation: the goal in one line, what's done, where you stopped, what you plan next, plus any gaps or uncertainty. Ask the person to confirm or correct. This catches summary mistakes before they become wasted work.
Once confirmed, continue. Add a line under "Sessions" in `HANDOFF.md` and from then on follow Mode 1 so the same bundle keeps growing.
A bare summary file carries less detail than a zip: use it to re-orient, say plainly that finer details and earlier files aren't available, ask the person to re-upload any files you need, then `init` a fresh handoff and carry the summary's content into the state.
If the bundle came from a chat with tools or skills this account lacks, do the same work with what's available and say what differs.
Mode 3: Many handoffs in a row
Keep one project name and folder across handoffs so the bundle accumulates a single coherent history. When state or log grows large, fold old detail into a short "earlier history" paragraph and keep the full text in `LOG.md`, so `HANDOFF.md` stays cheap to read however long the project runs.
Honest limits to tell the person
Say these plainly when relevant; overpromising would leave someone stranded at the worst moment:
Claude can't detect the usage limit. Frequent small saves plus the person saying "handoff" when the limit feels near is the safety net.
The summary is only as fresh as the last finished reply. If a limit cuts a reply off, the person still has the summary from the reply before.
A new chat knows only what the bundle contains. Claude does not truly remember the old chat, so unrecorded details are lost.
For mid-chat activation, Claude can only recover what is still visible in the conversation and still on disk. Trimmed history or files that no longer exist are listed under Gaps, not invented.
Very large files may be too big to bundle; list them in the index and ask the person to re-upload them directly.
A skill installed mid-chat may not load until a new chat begins; if it isn't active, the person can start a new chat in the same account and attach what they have.
