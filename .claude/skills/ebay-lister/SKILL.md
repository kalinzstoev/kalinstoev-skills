---
name: ebay-lister
description: Turn a folder of item photos into eBay draft listings. Sorts photos from inbox/ into items, writes title, category, condition, description and price for each, shows a preview, then writes a Seller Hub "Create drafts" CSV for the user to upload. Use when the user wants to list items on eBay from photos, process the inbox, or make the drafts CSV.
---

# eBay lister

The user photographs things to sell, you turn the photos into eBay draft listings, and they
upload one CSV in Seller Hub. They add photos, postage and the remaining details in the eBay app
and publish there.

**Safety:** you never touch the user's eBay account. Your only output is a CSV whose rows are all
`Action=Draft`, which the user uploads themselves. Never write any other Action.

Work in the folder the user started Claude Code in (the "working folder"):

```
inbox/                 photos to process (from the phone, JPEG)
items/<id>/photos/     photos moved here once sorted (never delete photos)
items/<id>/item.json   the listing
preview.html           built by the script
out/drafts-*.csv       built by the script, uploaded by the user
ebay-template.csv      optional: eBay's drafts template for a site other than eBay UK
```

The script is `ebay_lister.py` in this skill's folder. Run it with `python3` (on Windows,
`python`) from the working folder:

- `python3 <skill dir>/ebay_lister.py start`: creates `inbox/` if needed and prints its full
  path, what is in it, how many items exist already, and the eBay site and currency.
- `python3 <skill dir>/ebay_lister.py preview --open`: builds `preview.html` from all items,
  prints what is still missing per item, and opens the page in the user's browser.
- `python3 <skill dir>/ebay_lister.py csv`: checks every `approved` item and writes
  `out/drafts-<date-time>.csv` plus a matching `-checklist.txt` of what is left to do in eBay.
  It refuses if any approved item has a problem, and marks the written items `in-csv`.
- `python3 <skill dir>/ebay_lister.py site`: prints only the eBay site and currency.

## Talking to the user

Assume the user is not technical. They want to sell some things, not learn the tool.

- Use plain words. Say "the photos folder", "the preview page", "the file to upload"; don't
  mention JSON, scripts, commands or statuses unless they ask.
- Never ask them to edit a file or run a command. You do that. Give full folder paths they can
  paste into their file manager.
- Ask your questions about all the items in one short list, not one message per item, and
  only ask what the photos can't answer.
- At each stage say in a line or two what you did and what happens next.

## Get ready

1. Check Python works: try `python3 --version`, then `python --version`. If neither does, tell
   the user to install Python from python.org (on Windows, ticking "Add python.exe to PATH"),
   then restart Claude Code and run `/ebay-lister` again. Stop there.
2. Run `start`.
3. If the inbox has no photos and no zip, give the user its full path and ask them to copy
   their photos there and tell you when they have. Pass on these tips:
   - several photos per item, one item after another (don't mix them up);
   - include labels, model numbers, sizes, and any marks or damage;
   - eBay wants at least 5 photos per listing.
4. If the inbox has files that aren't JPEG, PNG or WebP (iPhones save HEIC), convert them to
   JPEG if a tool is installed (`magick`, `sips` on macOS), keeping the originals in `out/`.
   Otherwise ask the user to export them as JPEG.

## Which eBay site

`start` prints the eBay site. Everything below that depends on the marketplace (category IDs, item specific
names, spelling, currency, the Seller Hub address) follows the site it prints.

- With no `ebay-template.csv` in the working folder the site is **eBay UK** (GBP). This is the
  only site the tool has been tested on.
- If the user sells on another eBay site, they need that site's own template: Seller Hub →
  Reports → Uploads → Get template → Listings → "Create drafts template", saved unchanged as
  `ebay-template.csv` in the working folder. The script copies its `#INFO` lines and header row,
  so the CSV matches what that site expects. On a first run (no items yet) with the site showing
  UK, ask the user once whether they sell on ebay.co.uk; if not, walk them through this before
  writing any listings.
- Tell the user once that sites other than UK are untested, and suggest uploading a single
  draft first to check it arrives as expected.

## Workflow

### 1. Sort the photos into items

- If `inbox/` holds a zip (a Google Photos download), list its contents first, extract only
  plain image files (no paths, no `..`) into `inbox/`, and move the zip to `out/`. Never
  delete it.
- If a photo is blurry or duplicates another, say so and suggest leaving it out of the listing
  (keep the file in the item folder).
- List `inbox/` sorted by filename. Phone filenames run in shooting order (`IMG_20261024_…`),
  so one item's photos are usually consecutive.
- Look at every photo. Group them by the item shown (same object, background, lighting). A
  close-up of a label or a defect belongs with the item it shows.
- Show the user a short summary and wait for their OK or corrections:

  ```
  Item 1 – Blue Nike Air Max 90 trainers       IMG_0412–0416 (5 photos)
  Item 2 – Kenwood hand blender                IMG_0417–0420 (4 photos)
  Unsure – IMG_0421 (blurry box, maybe item 2?)
  ```

- Once confirmed, create `items/<id>/photos/` and **move** (not copy) each item's photos there.
  The id is a two-digit number continuing after the highest existing one in `items/`, plus a
  short slug: `03-nike-air-max-90`.

### 2. Write each listing

Look closely at all of an item's photos (labels, model numbers, sizes, tags, wear) and write
`items/<id>/item.json` (values below are examples, for eBay UK):

```json
{
  "id": "03-nike-air-max-90",
  "status": "draft",
  "title": "Nike Air Max 90 Men's Trainers UK 9 Blue White Leather",
  "category_id": "47140",
  "category_name": "Clothes, Shoes & Accessories > Men > Men's Shoes > Trainers",
  "condition": "USED",
  "condition_suggestion": "Pre-owned - Good",
  "price": 35.00,
  "price_note": "Similar used pairs are listed around £30–45; light creasing, clean soles.",
  "specifics": {
    "Brand": "Nike",
    "Model": "Air Max 90",
    "UK Shoe Size": "9",
    "Colour": "Blue",
    "Upper Material": "Leather",
    "Style": ""
  },
  "description_html": "<p>…</p>",
  "photos": ["photos/IMG_0412.jpg", "photos/IMG_0413.jpg"],
  "notes": ["Size read from the tongue label; check it's UK not US."]
}
```

- **title:** at most 80 characters. Start with brand and model, then what it is, then
  size, colour and key features: the words a buyer would search for. No filler ("L@@K", "wow"),
  no all-caps, no claims the photos don't support. The title matters most: it is one of the
  two fields that reliably carry into the draft, and eBay prefills item specifics from title
  keywords, so get brand, model, size and colour into it where they fit.
- **category_id:** the leaf category for the item **on the user's eBay site** (category IDs
  differ between sites, so a UK ID is wrong on eBay US). Use what you know, and web search when
  unsure (the site's category browse pages show the ID at the end of the URL). Always set
  `category_name` so the user can see in the preview whether it's right. Note in `notes` if you
  are not sure.
- **condition:** `NEW` (unused, with tags or in the box) or `USED`. The drafts template only takes
  these two, and in the test draft eBay left the condition itself unset (the value only went into
  the condition description), so the user picks it in eBay. Put the condition you would choose
  from eBay's list for that category (e.g. "Pre-owned - Good", "New with box") in
  `condition_suggestion`; it is shown in the preview and the checklist. Describe the real
  condition in the description.
- **price:** your estimate, in the site's currency, for a Buy It Now listing that sells within a
  few weeks. Search the web for similar items on that site when that helps, and give the reason
  in `price_note`. The user sets the final price.
- **specifics:** the item specifics a buyer would filter on for this category, with the names
  and spelling the user's site uses (on eBay UK: `Colour`, not `Color`; `UK Shoe Size`). Leave a
  value `""` when the photos don't show it; the preview highlights it. The CSV can't carry
  specifics (eBay ignores extra columns); eBay's AI usually fills them, and the filled ones also
  go in the description's DETAILS.
- **description_html:** follow the template below exactly, unless the user has asked for a
  different layout. It is plain text laid out in lines; write each line break as `<br>` (a blank
  line is `<br><br>`), with no other tags, styles, images or emojis (eBay strips most HTML from
  uploaded drafts). Section headings are in capitals, bullets are typed `•` characters. Write in
  the language and spelling of the user's site.

  ```text
  Rains Backpack – Mint Green

  Barely used, only worn a few times, and in near-new condition.

  FEATURES
  • Matte rubberised outer with flap top and swivel hook clip closure
  • Front slip pocket
  • Black grab handle and adjustable shoulder straps
  • Padded back panel with vertical zip pocket
  • Grey lined main compartment with inner sleeve

  CONDITION: EXCELLENT
  • One small chip on the metal swivel clip (see photos)
  • Slight marks on the strap end where it passes through the buckle
  • No other visible wear

  INCLUDED
  The backpack only.

  DETAILS
  Brand: Rains
  Model: Backpack
  Colour: Mint green
  Department: Unisex
  Closure: Clip
  ```

  - First line: brand, model and what it is, then ` – ` and the colour or key variant.
  - Second: one sentence on overall condition and use.
  - FEATURES: what the photos show, one per bullet, no full stops.
  - CONDITION: the grade in capitals (EXCELLENT, VERY GOOD, GOOD, FAIR or NEW), then a bullet for
    every defect visible in the photos, ending with "No other visible wear" when true.
  - INCLUDED: what's in the photos (box, charger, manual) and nothing else.
  - DETAILS: the filled-in specifics as `Name: value` lines (skip blank ones).

  Never claim it works, is genuine, or is complete unless the photos show it; put questions for
  the user in `notes`.
- **photos:** paths relative to the item folder, best photo first (the user will add photos in
  eBay in that order).
- **notes:** anything the user should check or tell you (does it work, the exact size, missing
  parts).

### 3. Preview and revise

- Run `preview --open`. It opens the page in the user's browser; if it says it couldn't (for
  example inside a container), give the user the file's full path to open themselves.
  Summarise per item what is blank or uncertain, from the script's output and your notes, and
  remind them they can ask for changes in plain words.
- Apply changes the user asks for ("it's the 2019 model", "drop photo 3", "price it at 20"),
  then rebuild the preview. If they say photos belong to a different item, move them and redo
  both items.
- When the user approves an item, set its `"status"` to `"approved"`. Only the user approves.

### 4. Write the drafts CSV

- Run `csv`. If it lists problems, fix them (or ask the user) and run it again.
- Give the user the CSV's full path and the steps, and tell them the same steps are saved as a
  tick-list next to it (the `-checklist.txt` file the script printed):
  1. On their eBay site (ebay.co.uk for UK): Seller Hub → Reports → Uploads → Upload template,
     and choose the CSV. Don't open and resave it in Excel first.
  2. Check the upload result for errors.
  3. Open each draft in Seller Hub or the eBay app. Its Custom label (SKU) is the item id. Then:
     add the photos (from the phone, in the order in the checklist; eBay asks for at least 5),
     pick the condition, check the category, apply the item specifics eBay suggests and fill
     any required ones it misses (from the description's DETAILS), check
     postage, and publish.
- Offer to help if the upload shows an error: ask them to paste the message.
- Items marked `in-csv` are not written again. If an upload failed and the user wants it redone,
  set those items back to `approved` and rerun `csv`.
