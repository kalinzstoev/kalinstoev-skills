# eBay lister

Turns phone photos of things to sell into eBay **draft** listings (eBay UK by default; see
[Other eBay sites](#other-ebay-sites)). Claude Code does the
looking and writing; a small script builds a preview and the drafts CSV; you upload the CSV
and finish each draft in the eBay app. Nothing here touches your eBay account.

## How a batch works

1. **Run `/ebay-lister`** in Claude Code. The first time, Claude checks Python is installed,
   creates `inbox/` in the working folder and tells you where it is.
2. **Photos in.** Copy the photos (or the Google Photos download zip) into `inbox/` and tell
   Claude.
3. **Sort.** The script unpacks any zip (the zip is kept in `out/`). Claude looks at every photo and groups
   them into items. You get a one-line summary per item and confirm or correct it. Blurry
   photos are flagged.
4. **Move.** Each item's photos move to `items/<id>/photos/` (never deleted).
5. **Write.** Claude writes `items/<id>/item.json`: title, category, condition, price with a
   reason, item specifics and the description (the template below). It only states what the
   photos show.
6. **Preview.** `preview.html` opens in your browser and shows every item.
7. **Questions and changes.** Claude asks, in one short list, what the photos can't show:
   brand or model if there's no label, size, wear on sides it can't see, does it work. Answer
   and ask for changes in chat; Claude edits and rebuilds the preview.
8. **Approve.** Say "approve" and the item is marked approved.
9. **CSV.** Claude writes `out/drafts-<date-time>.csv` for the approved items, in eBay's
   "Create drafts" format. Every row is `Action=Draft`; the script refuses anything else.
   Next to it is a `-checklist.txt` file: a tick-list per item of what is left to do in eBay.
10. **Upload.** Your eBay site (ebay.co.uk) → Seller Hub → Reports → Uploads → Upload template → choose the CSV
    (don't open it in Excel first).
11. **Finish on the phone.** Open each draft (its Custom label is the item id) and follow
    the checklist:
    add the photos in the order given (eBay wants at least 5), pick the condition
    Claude suggested, apply eBay's suggested item specifics, check category and postage,
    publish.

## What carries into the draft

| Field | From the CSV? |
|---|---|
| Title, description, price, quantity | Yes |
| Category | Yes, and eBay corrects it if needed |
| Photos | Only as web links; we leave them empty and you add them on the phone |
| Condition | No: pick it in eBay (Claude suggests one) |
| Item specifics | No: eBay's AI fills them from title and photos |
| Postage, returns | No: eBay suggests them |

That's why the title carries brand, model, size and colour: eBay reads specifics from it.

This is what a test draft and the first real listings showed on eBay UK in October 2026. eBay
may change it.

## Other eBay sites

With nothing else set up, the CSV is written for eBay UK in pounds. For another site, download
that site's own template (Seller Hub → Reports → Uploads → Get template → Listings → "Create
drafts template") and save it, unchanged, as `ebay-template.csv` in the working folder. The
script copies its `#INFO` lines and header row into every CSV it writes and takes the currency
from it. Claude then uses that site's category IDs and item specific names.

`python3 ebay_lister.py site` prints the site, country and currency in use. `--template <file>`
on any command points at a template somewhere else.

Only eBay UK has been tested. On another site, upload one draft first and check it.

## Description template

Plain text with line breaks (written as `<br>` in the CSV, no other HTML, because eBay strips
most HTML from uploaded drafts). To change the layout, edit the template in `SKILL.md`.

```text
Rains Backpack – Mint Green

Barely used, only worn a few times, and in near-new condition.

FEATURES
• Matte rubberised outer with flap top and swivel hook clip closure
• Front slip pocket

CONDITION: EXCELLENT
• One small chip on the metal swivel clip (see photos)
• No other visible wear

INCLUDED
The backpack only.

DETAILS
Brand: Rains
Model: Backpack
Colour: Mint green
```

## Files

```
inbox/                  new photos or zips
items/<id>/photos/      an item's photos
items/<id>/item.json    the listing (status: draft → approved → in-csv)
preview.html            the preview page
out/drafts-*.csv        CSVs to upload, each with a -checklist.txt (and kept zips)
ebay-template.csv       optional: your eBay site's drafts template (not needed for UK)
```

All of these are in the working folder and git-ignored.

## The script

`ebay_lister.py` is Python 3, standard library only:

- `python3 ebay_lister.py start` creates `inbox/`, unpacks any photo zip in it and reports
  what is in the working folder.
- `python3 ebay_lister.py site` prints the eBay site and currency the CSV is written for.
- `python3 ebay_lister.py preview` builds `preview.html` and lists what's missing per item
  (`--open` also opens it in the browser).
- `python3 ebay_lister.py csv` checks every approved item and writes the drafts CSV, then
  writes the checklist and marks those items `in-csv` so they aren't sent twice. To redo one, set its status back to
  `approved`.

Tests: `python3 -m unittest test_ebay_lister.py` from this folder.

## Using it outside this project

Copy this folder to `~/.claude/skills/ebay-lister` (Windows:
`%USERPROFILE%\.claude\skills\ebay-lister`) and run `/ebay-lister` from any folder that has an
`inbox/`. On Windows use `python` instead of `python3`.

The workflow Claude follows is in `SKILL.md`; the design and the reasons behind it are in
`docs/design.md` in the project repo.
