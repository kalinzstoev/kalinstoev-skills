# eBay Lister

A [Claude Code](https://claude.com/claude-code) skill that turns phone photos of things you
want to sell into eBay **draft** listings.

You take photos and drop them in a folder. Claude sorts them into items and writes a title,
category, condition, price and description for each one. You check a preview page, then upload
one CSV file in eBay's Seller Hub. The drafts appear in your eBay account, where you add the
photos and publish.

It is meant for clearing out a cupboard, not running a shop: a dozen items at a time, no
database, no accounts to set up.

## What it does and doesn't do

- **It never touches your eBay account.** There are no eBay API calls, keys or logins. The only
  output is a CSV that you upload yourself, and every row in it is a draft. The script refuses
  to write anything else.
- **It needs no API keys at all.** Claude Code does the looking and writing with the
  subscription you already use it with.
- **You finish each draft in eBay.** eBay's draft upload carries the title, description, price
  and category. It doesn't carry photos, condition, item specifics or postage, so you set those
  in the eBay app before publishing (a few minutes per item). See
  [what carries into the draft](.claude/skills/ebay-lister/README.md#what-carries-into-the-draft).
- **Tested on eBay UK only.** Other eBay sites can be used by supplying that site's own
  template, but nobody has tried them yet. See [Other eBay sites](#other-ebay-sites).

## What you need

- [Claude Code](https://claude.com/claude-code) (terminal, desktop app or IDE extension).
- Python 3. No packages to install.
- An eBay seller account with Seller Hub.

## Quick start

1. Get the project:

   ```bash
   git clone https://github.com/kalinzstoev/ebay-lister.git
   ```

2. Copy your photos into an `inbox` folder inside it (create the folder if it isn't there).
   A zip downloaded from Google Photos works too. Take several photos of each item, one item
   after another, including any labels and any damage.

3. Start Claude Code in the project folder and run:

   ```
   /ebay-lister
   ```

4. Answer Claude's questions, open `preview.html` in your browser, and ask for any changes in
   plain words ("it's a size 10", "drop the blurry photo", "price it at 20").

5. Say which items you approve. Claude writes `out/drafts-<date-time>.csv`.

6. In eBay: Seller Hub → Reports → Uploads → Upload template, and choose the CSV. Don't open
   it in Excel first.

7. Open each draft in the eBay app, add its photos, pick the condition, check the details eBay
   suggests, and publish.

The full walkthrough, with the description layout and what each file is for, is in the
[skill's README](.claude/skills/ebay-lister/README.md).

Your photos, listings and CSVs stay in `inbox/`, `items/` and `out/`. These are git-ignored,
so they are never committed.

### Using it from any folder

To have `/ebay-lister` available everywhere, not only in this project, copy the skill folder
into your personal skills:

```bash
cp -r .claude/skills/ebay-lister ~/.claude/skills/
```

On Windows the destination is `%USERPROFILE%\.claude\skills\`. Then run `/ebay-lister` from
any folder that has an `inbox` folder with photos in it.

## Other eBay sites

Out of the box the CSV is written for eBay UK, in pounds. To use another eBay site:

1. On your eBay site, go to Seller Hub → Reports → Uploads → Get template → Listings →
   "Create drafts template" and download it.
2. Save it, unchanged, as `ebay-template.csv` in the folder you run Claude Code in.

The script then copies the header lines from your template, so the CSV matches what your site
expects, and the preview shows your currency. Claude picks categories and item specific names
for that site. You can check what it picked up with:

```bash
python3 .claude/skills/ebay-lister/ebay_lister.py site
```

(Use `python` instead of `python3` on Windows.)

This path is untested outside the UK. Upload a single draft first and check it arrives as you
expect. If it works, or doesn't, for your site, please open an issue so this section can say so.

## Changing how listings are written

The rules Claude follows are plain text in
[`.claude/skills/ebay-lister/SKILL.md`](.claude/skills/ebay-lister/SKILL.md): how titles are
built, the description layout, how prices are estimated. Edit that file to change them, or
just tell Claude what you want differently during a run.

## Project layout

```
.claude/skills/ebay-lister/   the skill: SKILL.md, ebay_lister.py, tests, README
docs/design.md                why it works the way it does
docs/ebay-api-research.md     research into eBay's APIs and the drafts upload
docs/dev-container.md         optional Docker setup for working on the project
resource/                     eBay's UK drafts template, as downloaded
```

## Working on it

Run the tests from the skill folder:

```bash
cd .claude/skills/ebay-lister && python3 -m unittest test_ebay_lister.py
```

The repo includes a Claude Code hook (`.claude/hooks/block-dangerous-git.sh`) that stops Claude
from running `git push`, `git reset --hard` and similar commands in this project. Remove it from
`.claude/settings.json` if you don't want it.

An optional Docker dev container, and the extra Claude Code skills used while building this,
are described in [docs/dev-container.md](docs/dev-container.md).

## Licence

[MIT](LICENSE). Not affiliated with or endorsed by eBay.
