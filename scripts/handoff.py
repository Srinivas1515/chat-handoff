#!/usr/bin/env python3
"""Helper for the chat-handoff skill. One call = one cheap save.

Commands:
  init     <dir> --title T            create a new handoff folder
  save     <dir> [--user U] [--claude C] [--state-file F] [--summary-file F --summary-out PATH]
           [--backfill-file F] [--gap TEXT ...] [--add PATH KIND NOTE ...]
           (--backfill-file = condensed history of the chat BEFORE the skill started)
           (--gap = something that could not be recovered; listed in HANDOFF.md)
           append to LOG.md, optionally replace the STATE section, optionally rewrite
           SUMMARY.md (and copy it to --summary-out for download), optionally copy files in
  bundle   <dir> --out ZIP            zip the folder into one portable file
  unpack   <zip> <dir>                restore a handoff folder from a zip
  show     <dir>                      print HANDOFF.md (the cheap layer) only
  verify   <dir>                      check every file in the index exists
  sync     <dir> [--uploads D] [--outputs D]  add any uploaded/created file not yet in the bundle
"""
import argparse, datetime, os, re, shutil, sys, zipfile

GAPS_RE = re.compile(r"(<!-- GAPS:START -->)(.*?)(<!-- GAPS:END -->)", re.S)
BACKFILL_RE = re.compile(r"(<!-- BACKFILL:START -->)(.*?)(<!-- BACKFILL:END -->)", re.S)
STATE_RE = re.compile(r"(<!-- STATE:START -->)(.*?)(<!-- STATE:END -->)", re.S)
FILES_RE = re.compile(r"(<!-- FILES:START -->)(.*?)(<!-- FILES:END -->)", re.S)

TEMPLATE = """# HANDOFF: {title}

## HOW TO RESUME (read this first)
You are Claude, picking up a conversation that began in another chat/account.
The person cannot re-explain everything, so this file is the memory.

1. Read ONLY the "Current state" section below. Do not read LOG.md yet; it is long
   and costs the person's usage limit. Open it only when you need a specific detail.
2. Files from the earlier chat are in `files/inputs/` (what the person gave) and
   `files/outputs/` (what was produced). The index below says what each one is.
3. Tell the person, in a few sentences: where things stand, what you will do next,
   and anything you are unsure about. Ask them to confirm or correct, then continue.
4. Keep this handoff alive: after each meaningful step, add to LOG.md and refresh
   the state (if the chat-handoff skill is installed, follow it; if not, edit these
   files by hand and give the person an updated zip at checkpoints).

## Current state
<!-- STATE:START -->
(not written yet)
<!-- STATE:END -->

## File index
<!-- FILES:START -->
| File | Kind | What it is |
|---|---|---|
<!-- FILES:END -->

## Gaps (could not be recovered)
<!-- GAPS:START -->
(none recorded)
<!-- GAPS:END -->

## Sessions
- Session 1 started {now}
"""

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def cmd_init(a):
    d = a.dir
    os.makedirs(os.path.join(d, "files", "inputs"), exist_ok=True)
    os.makedirs(os.path.join(d, "files", "outputs"), exist_ok=True)
    h = os.path.join(d, "HANDOFF.md")
    if not os.path.exists(h):
        open(h, "w").write(TEMPLATE.format(title=a.title, now=now()))
    sm = os.path.join(d, "SUMMARY.md")
    if not os.path.exists(sm):
        open(sm, "w").write(f"# Chat summary: {a.title}\n\n_Last updated: {now()}_\n\n(nothing summarized yet)\n")
    l = os.path.join(d, "LOG.md")
    if not os.path.exists(l):
        open(l, "w").write(f"# Conversation log: {a.title}\n\n## Earlier history (before the handoff started; condensed, key instructions verbatim)\n<!-- BACKFILL:START -->\n(none; handoff began with the chat)\n<!-- BACKFILL:END -->\n\n## Log (append-only, newest at the bottom)\n")
    print(f"ready: {d}")

def cmd_save(a):
    d = a.dir
    h = os.path.join(d, "HANDOFF.md")
    if not os.path.isfile(h):
        sys.exit(f"error: no handoff at {d}. Run init first (or rebuild it from the conversation).")
    if a.user or a.claude:
        with open(os.path.join(d, "LOG.md"), "a") as f:
            f.write(f"\n---\n### {now()}\n")
            if a.user:
                f.write(f"**Person:** {a.user}\n\n")
            if a.claude:
                f.write(f"**Claude:** {a.claude}\n")
    if a.summary_file:
        if not os.path.isfile(a.summary_file):
            sys.exit(f"error: summary file not found: {a.summary_file}")
        title = re.match(r"# HANDOFF: (.*)", open(h).read())
        title = title.group(1).strip() if title else "Chat"
        body = open(a.summary_file).read().strip()
        content = f"# Chat summary: {title}\n\n_Last updated: {now()}_\n\n{body}\n"
        open(os.path.join(d, "SUMMARY.md"), "w").write(content)
        if a.summary_out:
            os.makedirs(os.path.dirname(os.path.abspath(a.summary_out)), exist_ok=True)
            open(a.summary_out, "w").write(content)
    if a.backfill_file:
        if not os.path.isfile(a.backfill_file):
            sys.exit(f"error: backfill file not found: {a.backfill_file}")
        lp = os.path.join(d, "LOG.md")
        lt = open(lp).read()
        new = open(a.backfill_file).read().strip()
        if BACKFILL_RE.search(lt):
            lt = BACKFILL_RE.sub(lambda m: f"{m.group(1)}\n{new}\n{m.group(3)}", lt)
        else:
            lt += f"\n## Earlier history (condensed)\n{new}\n"
        open(lp, "w").write(lt)
    text = open(h).read()
    for gap in a.gap or []:
        if GAPS_RE.search(text):
            def addgap(m, gap=gap):
                body = m.group(2).replace("(none recorded)", "").rstrip("\n")
                return f"{m.group(1)}{body}\n- {gap}\n{m.group(3)}"
            text = GAPS_RE.sub(addgap, text)
    if a.state_file:
        if not os.path.isfile(a.state_file):
            sys.exit(f"error: state file not found: {a.state_file}")
        new = open(a.state_file).read().strip()
        text = STATE_RE.sub(lambda m: f"{m.group(1)}\n{new}\n{m.group(3)}", text)
    for path, kind, note in a.add or []:
        if not os.path.isfile(path):
            print(f"warning: skipped missing file {path}", file=sys.stderr)
            continue
        kind = kind.lower().rstrip("/")
        kind = {"input": "inputs", "output": "outputs"}.get(kind, kind)
        if kind not in ("inputs", "outputs"):
            print(f"warning: kind '{kind}' not inputs/outputs, using outputs", file=sys.stderr)
            kind = "outputs"
        dest_dir = os.path.join(d, "files", kind)
        os.makedirs(dest_dir, exist_ok=True)
        name = os.path.basename(path)
        shutil.copy2(path, os.path.join(dest_dir, name))
        row = f"| files/{kind}/{name} | {kind[:-1]} | {note or name} |"
        if f"files/{kind}/{name} |" in text:
            text = re.sub(rf"^\| files/{kind}/{re.escape(name)} \|.*$", lambda m: row, text, flags=re.M)
        else:
            text = FILES_RE.sub(lambda m: m.group(1) + m.group(2).rstrip("\n") + "\n" + row + "\n" + m.group(3), text)
    open(h, "w").write(text)
    print("saved")

def cmd_bundle(a):
    out = a.out
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(a.dir):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, a.dir))
    print(f"bundled: {out} ({os.path.getsize(out)//1024} KB)")

def cmd_unpack(a):
    os.makedirs(a.dir, exist_ok=True)
    with zipfile.ZipFile(a.zip) as z:
        z.extractall(a.dir)
    print(f"unpacked to {a.dir}")

def cmd_verify(a):
    text = open(os.path.join(a.dir, "HANDOFF.md")).read()
    rows = re.findall(r"^\| (files/(?:inputs|outputs)/[^|]+?) \|", text, flags=re.M)
    missing = [r for r in rows if not os.path.isfile(os.path.join(a.dir, r))]
    print(f"{len(rows) - len(missing)}/{len(rows)} indexed files present")
    for m in missing:
        print(f"MISSING: {m}")
    sys.exit(1 if missing else 0)

SKIP_NAMES = {"CHAT_SUMMARY.md"}

def cmd_sync(a):
    """Safety net: bundle every upload/output file the index doesn't know yet."""
    h = os.path.join(a.dir, "HANDOFF.md")
    if not os.path.isfile(h):
        sys.exit(f"error: no handoff at {a.dir}. Run init first.")
    text = open(h).read()
    handoff_abs = os.path.abspath(a.dir)
    added = []
    for root, kind in ((a.uploads, "inputs"), (a.outputs, "outputs")):
        if not root or not os.path.isdir(root):
            continue
        for dirpath, dirnames, files in os.walk(root):
            if os.path.abspath(dirpath).startswith(handoff_abs):
                dirnames[:] = []
                continue
            dirnames[:] = [x for x in dirnames if x not in ("artifacts", "handoff", "__pycache__")]
            for fn in files:
                if fn in SKIP_NAMES or fn.endswith(".skill") or (fn.startswith("handoff") and fn.endswith(".zip")):
                    continue
                if f"files/{kind}/{fn} |" in text:
                    continue
                src = os.path.join(dirpath, fn)
                dest = os.path.join(a.dir, "files", kind)
                os.makedirs(dest, exist_ok=True)
                shutil.copy2(src, os.path.join(dest, fn))
                row = f"| files/{kind}/{fn} | {kind[:-1]} | {fn} (auto-added; describe if known) |"
                text = FILES_RE.sub(lambda m: m.group(1) + m.group(2).rstrip("\n") + "\n" + row + "\n" + m.group(3), text)
                added.append(f"{kind}/{fn}")
    open(h, "w").write(text)
    print(f"synced: {len(added)} file(s) added" + ("".join(f"\n  + {x}" for x in added)))

def cmd_show(a):
    print(open(os.path.join(a.dir, "HANDOFF.md")).read())

p = argparse.ArgumentParser()
s = p.add_subparsers(dest="cmd", required=True)
x = s.add_parser("init"); x.add_argument("dir"); x.add_argument("--title", default="Untitled chat"); x.set_defaults(f=cmd_init)
x = s.add_parser("save"); x.add_argument("dir"); x.add_argument("--user"); x.add_argument("--claude")
x.add_argument("--state-file"); x.add_argument("--summary-file"); x.add_argument("--summary-out"); x.add_argument("--backfill-file"); x.add_argument("--gap", action="append"); x.add_argument("--add", action="append", nargs=3, metavar=("PATH", "KIND", "NOTE")); x.set_defaults(f=cmd_save)
x = s.add_parser("bundle"); x.add_argument("dir"); x.add_argument("--out", required=True); x.set_defaults(f=cmd_bundle)
x = s.add_parser("unpack"); x.add_argument("zip"); x.add_argument("dir"); x.set_defaults(f=cmd_unpack)
x = s.add_parser("show"); x.add_argument("dir"); x.set_defaults(f=cmd_show)
x = s.add_parser("sync"); x.add_argument("dir"); x.add_argument("--uploads", default="/mnt/user-data/uploads"); x.add_argument("--outputs", default="/mnt/user-data/outputs"); x.set_defaults(f=cmd_sync)
x = s.add_parser("verify"); x.add_argument("dir"); x.set_defaults(f=cmd_verify)
a = p.parse_args(); a.f(a)
