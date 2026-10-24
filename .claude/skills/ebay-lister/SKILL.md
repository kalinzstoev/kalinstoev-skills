---
name: ebay-lister
description: Turn a folder of item photos into eBay UK draft listings. Sorts photos from inbox/ into items, writes title, category, condition, description and price for each, shows a preview, then writes a Seller Hub "Create drafts" CSV for the user to upload. Use when the user wants to list items on eBay from photos, process the inbox, or make the drafts CSV.
---

# eBay lister

The user photographs things to sell, you turn the photos into eBay UK draft listings, and they
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
```

The script is `ebay_lister.py` in this skill's folder. Run it with `python3` (on Windows,
`python`) from the working folder:

- `python3 <skill dir>/ebay_lister.py preview`: builds `preview.html` from all items and prints
  what is still missing per item.
- `python3 <skill dir>/ebay_lister.py csv`: checks every `approved` item and writes
  `out/drafts-<date-time>.csv`. It refuses if any approved item has a problem, and marks the
  written items `in-csv`.

## Workflow

### 1. Sort the photos into items

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
`items/<id>/item.json` (values below are examples):

```json
{
  "id": "03-nike-air-max-90",
  "status": "draft",
  "title": "Nike Air Max 90 Men's Trainers UK 9 Blue White Leather",
  "category_id": "15709",
  "category_name": "Clothes, Shoes & Accessories > Men > Men's Shoes > Trainers",
  "condition": "USED",
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
  no all-caps, no claims the photos don't support.
- **category_id:** the eBay **UK** leaf category for the item. Use what you know, and web search
  when unsure (eBay UK category browse pages show the ID at the end of the URL). Always set
  `category_name` so the user can see in the preview whether it's right. Note in `notes` if you
  are not sure.
- **condition:** `NEW` (unused, with tags or in the box) or `USED`. The drafts template only takes
  these two. Describe the real condition in the description.
- **price:** your estimate in GBP for a Buy It Now listing that sells within a few weeks. Search
  the web for similar items when that helps, and give the reason in `price_note`. The user sets
  the final price.
- **specifics:** the item specifics a buyer would filter on for this category, with eBay UK
  names (`Colour`, not `Color`; `UK Shoe Size`). Leave a value `""` when the photos don't show
  it; the preview highlights it. The CSV can't carry specifics (eBay ignores extra columns), so
  they go into the description and the user can copy them into eBay.
- **description_html:** clean, simple HTML, no styles, images, banners or emojis:

  ```html
  <p>One or two plain sentences: what it is and the overall condition.</p>
  <ul>
    <li>Key feature</li>
    <li>Key feature</li>
  </ul>
  <p><b>Condition:</b> honest detail, including every defect visible in the photos.</p>
  <p><b>Included:</b> what's in the photos (box, charger, manual) and nothing else.</p>
  <p><b>Details:</b></p>
  <ul>
    <li>Brand: Nike</li>
    <li>Model: Air Max 90</li>
  </ul>
  ```

  The Details list repeats the filled-in specifics (skip blank ones). Never claim it works,
  is genuine, or is complete unless the photos show it; put questions for the user in `notes`.
- **photos:** paths relative to the item folder, best photo first (the user will add photos in
  eBay in that order).
- **notes:** anything the user should check or tell you (does it work, the exact size, missing
  parts).

### 3. Preview and revise

- Run `preview`, then tell the user to open `preview.html` in the working folder in a browser
  (from Windows Explorer when running in the container). Summarise per item what is blank or
  uncertain, from the script's output and your notes.
- Apply changes the user asks for ("it's the 2019 model", "drop photo 3", "price it at £20"),
  then rebuild the preview. If they say photos belong to a different item, move them and redo
  both items.
- When the user approves an item, set its `"status"` to `"approved"`. Only the user approves.

### 4. Write the drafts CSV

- Run `csv`. If it lists problems, fix them (or ask the user) and run it again.
- Give the user the CSV's path and the upload steps:
  1. ebay.co.uk → Seller Hub → Reports → Uploads → Upload template, and choose the CSV. Don't
     open and resave it in Excel first.
  2. Check the upload result for errors.
  3. Open each draft in Seller Hub or the eBay app. Its Custom label (SKU) is the item id. Then:
     add the photos (from the phone, in the order in `item.json`), check the category, fill
     the item specifics (copy them from the preview's table or the description's Details), set
     the detailed condition and postage, and publish.
- Items marked `in-csv` are not written again. If an upload failed and the user wants it redone,
  set those items back to `approved` and rerun `csv`.
