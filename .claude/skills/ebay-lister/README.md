# eBay lister

Turns phone photos of things to sell into eBay UK **draft** listings. Claude Code does the
looking and writing; a small script builds a preview and the drafts CSV; you upload the CSV
and finish each draft in the eBay app. Nothing here touches your eBay account.

## How a batch works

1. **Photos in.** Copy the photos (or the Google Photos download zip) into `inbox/` in the
   working folder.
2. **Run `/ebay-lister`** in Claude Code.
3. **Sort.** Claude unzips any zip (the zip is kept in `out/`), looks at every photo and groups
   them into items. You get a one-line summary per item and confirm or correct it. Blurry
   photos are flagged.
4. **Questions.** Claude asks what the photos can't show: brand or model if there's no label,
   size, age, wear, does it work.
5. **Move.** Each item's photos move to `items/<id>/photos/` (never deleted).
6. **Write.** Claude writes `items/<id>/item.json`: title, category, condition, price with a
   reason, item specifics and the description (the template below).
7. **Preview.** `preview.html` shows every item. Ask for changes in chat; Claude edits and
   rebuilds it.
8. **Approve.** Say "approve" and the item is marked approved.
9. **CSV.** Claude writes `out/drafts-<date-time>.csv` for the approved items, in eBay's UK
   "Create drafts" format. Every row is `Action=Draft`; the script refuses anything else.
10. **Upload.** ebay.co.uk → Seller Hub → Reports → Uploads → Upload template → choose the CSV
    (don't open it in Excel first).
11. **Finish on the phone.** Open each draft (its Custom label is the item id) and:
    add the photos in the order from the preview (eBay wants at least 5), pick the condition
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

## Description template

Plain text with line breaks (written as `<br>` in the CSV, no other HTML):

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
out/drafts-*.csv        CSVs to upload (and kept zips)
```

All of these are in the working folder and git-ignored.

## The script

`ebay_lister.py` is Python 3, standard library only:

- `python3 ebay_lister.py preview` builds `preview.html` and lists what's missing per item.
- `python3 ebay_lister.py csv` checks every approved item and writes the drafts CSV, then
  marks those items `in-csv` so they aren't sent twice. To redo one, set its status back to
  `approved`.

Tests: `python3 -m unittest test_ebay_lister.py` from this folder.

## Using it outside this project

Copy this folder to `~/.claude/skills/ebay-lister` (Windows:
`%USERPROFILE%\.claude\skills\ebay-lister`) and run `/ebay-lister` from any folder that has an
`inbox/`. On Windows use `python` instead of `python3`.

The workflow Claude follows is in `SKILL.md`; the design and the reasons behind it are in
`docs/design.md` in this repo.
