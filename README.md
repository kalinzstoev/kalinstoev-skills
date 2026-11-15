# eBay Lister

[![tests](https://github.com/kalinzstoev/ebay-lister/actions/workflows/tests.yml/badge.svg)](https://github.com/kalinzstoev/ebay-lister/actions/workflows/tests.yml)

A [Claude Code](https://claude.com/claude-code) skill that turns phone photos of things you
want to sell into eBay **draft** listings.

<img src="docs/preview.jpg" alt="The preview page: a brown crossbody bag listing with three photos, title, price, item specifics with brand and material highlighted as unknown, and a description listing features and condition" width="640">

*The preview page for a real item. Everything in it was read from three phone photos: the
push-lock clasp, the two compartments seen from the side, the zip pocket on the back, and the
scuffs on the back panel. The highlighted rows, brand and material, are things the photos
don't show, so they were left blank and asked about, not guessed.*

You take photos and drop them in a folder. Claude looks at them, works out which photos belong
to which item, and reads what is actually there: the brand on a label, the material, the
pockets and fastenings, the scuff on a corner. From that it writes a title, a feature list, an
honest condition report and a price for each item. You check a preview page, then upload one
CSV file in eBay's Seller Hub. The drafts appear in your eBay account, where you add the photos
and publish.

eBay's own tools already suggest a category and item specifics. What they don't do is look at
your photos and describe the item for you. That is the part this skill does.

It is meant for clearing out a cupboard, not running a shop: a dozen items at a time, no
database, no accounts to set up.

## What it does and doesn't do

- **It only states what the photos show.** No "genuine", "works perfectly" or "waterproof"
  unless a label or a photo shows it, or you say so. Anything it can't tell, it asks you.
- **It never touches your eBay account.** There are no eBay API calls, keys or logins. The only
  output is a CSV that you upload yourself, and every row in it is a draft. The script refuses
  to write anything else.
- **It needs no API keys at all.** Claude Code does the looking and writing with the
  subscription you already use it with.
- **You finish each draft in eBay.** eBay's draft upload carries the title, description, price
  and category. It doesn't carry photos, condition, item specifics or postage, so you set those
  in the eBay app before publishing (a few minutes per item, from a tick-list the skill writes).
  See [what carries into the draft](skills/ebay-lister/README.md#what-carries-into-the-draft).
- **Tested on eBay UK only.** Other eBay sites can be used by supplying that site's own
  template, but nobody has tried them yet. See [Other eBay sites](#other-ebay-sites).

## What you need

- [Claude Code](https://claude.com/claude-code). The Claude desktop app is the easiest way to
  run it if you don't use a terminal.
- [Python 3](https://www.python.org/downloads/). Nothing else to install. (On Windows, tick
  "Add python.exe to PATH" in the installer.)
- An eBay seller account with Seller Hub.

## Install

In a Claude Code session, run:

```
/plugin install ebay-lister --marketplace kalinzstoev/ebay-lister
```

On an older Claude Code, where that isn't recognised, use the two-step form:

```
/plugin marketplace add kalinzstoev/ebay-lister
/plugin install ebay-lister@kalinzstoev
```

Choose "Install for you" when asked. The skill is then available in every folder.

Other ways to install are [listed below](#other-ways-to-install).

## Use

1. **Make a folder for your selling** (anywhere, for example `Documents/ebay`), open it in
   Claude Code, and type:

   ```
   /ebay-lister:ebay-lister
   ```

   or just say "help me list some things on eBay". Claude creates a photos folder (`inbox`)
   and tells you where it is.

2. **Copy your photos into it** and tell Claude. A zip downloaded from Google Photos works
   too. Take several photos of each item, one item after another, including any labels and
   any damage.

3. **Check Claude's work.** It shows which photos it thinks belong to which item, then opens
   a preview page in your browser and asks what the photos can't tell it (size, does it work).
   Ask for changes in plain words: "it's a size 10", "drop the blurry photo", "price it at 20".

4. **Say which items you approve.** Claude writes the file to upload and a tick-list of what
   is left to do, and tells you where both are.

5. **Upload it to eBay:** Seller Hub → Reports → Uploads → Upload template. Don't open the
   file in Excel first.

6. **Finish each draft in the eBay app,** following the tick-list: add the photos, pick the
   condition, check what eBay suggests, publish.

You never type a command or edit a file yourself. The full walkthrough, with the description
layout and what each file is for, is in the [skill's README](skills/ebay-lister/README.md).

Your photos, listings and CSVs stay in the folder you started in (`inbox/`, `items/`, `out/`).

## Other eBay sites

Out of the box the CSV is written for eBay UK, in pounds. To use another eBay site:

1. On your eBay site, go to Seller Hub → Reports → Uploads → Get template → Listings →
   "Create drafts template" and download it.
2. Save it, unchanged, as `ebay-template.csv` in the folder you run Claude Code in.

The skill then copies the header lines from your template, so the CSV matches what your site
expects, and the preview shows your currency. Claude picks categories and item specific names
for that site.

This path is untested outside the UK. Upload a single draft first and check it arrives as you
expect. If it works, or doesn't, for your site, please open an issue so this section can say so.

## Changing how listings are written

The rules Claude follows are plain text in
[`skills/ebay-lister/SKILL.md`](skills/ebay-lister/SKILL.md): how titles are built, the
description layout, how prices are estimated. Edit that file to change them, or just tell
Claude what you want differently during a run.

## Other ways to install

- **From your shell,** without opening a session:

  ```bash
  claude plugin marketplace add kalinzstoev/ebay-lister
  ```

  ```bash
  claude plugin install ebay-lister@kalinzstoev
  ```

- **As a plain skill,** with the [skills CLI](https://github.com/vercel-labs/skills) (needs
  Node). The skill is then called `/ebay-lister`:

  ```bash
  npx skills add kalinzstoev/ebay-lister
  ```

- **By hand:** download this repository (Code → Download ZIP) and copy the
  `skills/ebay-lister` folder into `~/.claude/skills/` (on Windows,
  `%USERPROFILE%\.claude\skills\`). The skill is then called `/ebay-lister`.

## How it is built, and why

The full reasoning is in [docs/design.md](docs/design.md). The short version:

- **Claude does the judgement, a script does the exact work.** Reading photos and writing a
  listing is what a model is good at, so that lives in `SKILL.md` as instructions. Checking a
  title is under 80 characters, or producing a CSV eBay will accept byte for byte, is not, so
  that lives in `ebay_lister.py` (Python, standard library only) with tests.
- **Safe by construction, not by instruction.** The tool has no way to reach eBay: no API, no
  keys, no login. The script can only write rows marked `Draft`, and a test checks that it
  refuses anything else. The worst a mistake can do is create a draft you delete.
- **Decisions came from evidence.** The first design used eBay's APIs. Research
  ([docs/ebay-api-research.md](docs/ebay-api-research.md)) and one test upload showed the
  drafts CSV was enough, and that eBay ignores item specifics in it. So the API was dropped,
  and the specifics go into the description and a tick-list instead.
- **Tested the way it is used.** Besides the unit tests, a fresh Claude with no knowledge of
  the project ran the skill from a clean copy against real photos, with a person's part played
  in plain words. That run found the skill stating "waterproof" from brand knowledge, which led
  to the rule that only what the photos show may be stated.
- **Honest about limits.** Only eBay UK is tested. Other sites work from eBay's own template
  file for that site instead of header values guessed in code.

It was built with Claude Code, by one person, for a real clear-out: nine items listed with it
before it was made public.

## Project layout

```
skills/ebay-lister/           the skill: SKILL.md, ebay_lister.py, tests, README
.claude-plugin/               plugin and marketplace manifests, for /plugin install
.github/workflows/tests.yml   runs the tests on Linux, Windows and macOS
docs/design.md                why it works the way it does
docs/ebay-api-research.md     research into eBay's APIs and the drafts upload
docs/dev-container.md         optional Docker setup for working on the project
resource/                     eBay's UK drafts template, as downloaded
```

## Working on it

Load your checkout as a plugin for one session:

```bash
claude --plugin-dir .
```

Run the tests from the skill folder:

```bash
cd skills/ebay-lister && python3 -m unittest test_ebay_lister.py
```

(Use `python` instead of `python3` on Windows.)

The repo includes a Claude Code hook (`.claude/hooks/block-dangerous-git.sh`) that stops Claude
from running force pushes, `git reset --hard` and similar commands in this project. It only
applies when you work inside this repository, not when you install the plugin. Remove it from
`.claude/settings.json` if you don't want it.

An optional Docker dev container, and the extra Claude Code skills used while building this,
are described in [docs/dev-container.md](docs/dev-container.md).

## Licence

[MIT](LICENSE). Not affiliated with or endorsed by eBay.
