# eBay Lister: design

First agreed in a `/grill-me` session on 2026-10-24, then simplified the same day after the
eBay research (`docs/ebay-api-research.md`) and a manual draft-upload test. Code follows this;
change the doc first if the plan changes.

## The experience

1. Take photos of all the items with the phone (Android, JPEG).
2. Copy them in one dump into `inbox/` in the working folder.
3. In Claude Code, run `/ebay-lister`.
4. Claude looks at the photos and sorts them into items (filename order helps: `IMG_0412`,
   `0413`, …). It shows a short summary, one line per item with its photos; I confirm or
   correct it. Photos are then moved into `items/<id>/photos/`, never deleted.
5. For each item Claude writes `items/<id>/item.json`: title, category, item specifics,
   condition, description and a suggested price. Anything it can't tell from the photos is
   left blank and flagged.
6. Claude builds `preview.html` showing every item roughly as it will look on eBay. I ask for
   changes in chat ("it's a 2019 model", "drop photo 3"); Claude edits and rebuilds.
7. For the items I approve, Claude writes one drafts CSV in eBay's "Create drafts" template
   format (`out/drafts-<date-time>.csv`).
8. I upload the CSV in Seller Hub → Reports → Uploads. The drafts appear in Seller Hub and in
   the eBay phone app, where I add the photos, check the details, let eBay suggest postage and
   publish.

The tool never talks to my eBay account. The only thing that reaches it is a CSV I upload
myself, and every row in it is a draft.

## The drafts CSV

Based on eBay's UK template (`resource/eBay-draft-listing-template-*.csv`, version 0.0.2):

- Same `#INFO` lines and header row as the template, CRLF line endings, UTF-8.
- Columns: `Action(SiteID=UK|Country=GB|Currency=GBP|Version=1193|CC=UTF-8)`,
  `Custom label (SKU)`, `Category ID`, `Title`, `UPC`, `Price`, `Quantity`, `Item photo URL`,
  `Condition ID`, `Description`, `Format`, then one `C:<aspect name>` column per item specific
  used by any row in the file.
- `Action` is always `Draft` and the code refuses to write anything else (another value, such as
  `Add`, would create a live listing). `Format` is `FixedPrice`, `Quantity` 1.
- `Custom label (SKU)` is the item id, so a draft can be matched back to its folder.
- `Condition ID` is `NEW` or `USED` only. The detailed condition and any defects go in the
  description; I can refine the condition in eBay.
- `Item photo URL` is left empty: I add the photos on the phone.
- Item specifics: `C:` columns were tested on 2026-10-24 (`C:Brand`, `C:Colour`) and the upload
  went through. Names must be eBay's exact aspect names for the category (e.g. `Colour`, not
  `Color`).

## Listing rules

- Marketplace: **eBay UK**, GBP, Buy It Now (fixed price).
- Category: eBay's suggested category for what the item is.
- Item specifics: the category's required and recommended aspects, filled from the photos,
  blank (and flagged in the preview) where Claude can't tell. Use eBay's allowed values where
  the aspect only accepts a fixed list.
- Title: up to 80 characters, the words a buyer would search for, no filler or caps.
- Description: clean, simple HTML. Short intro, bullet list of features and condition, defects,
  what's included. No templates, banners or emojis, and no claims the photos don't support.
- Price: Claude's estimate with a short reason, checked against a few **active** comparable
  listings where available. I set the final price in the preview or in eBay.
- Postage, returns, payment and Best Offer are set in eBay when I finish the draft.

## Technical decisions

- A **Claude Code skill**, `.claude/skills/ebay-lister/`, committed in this repo. It also works
  outside the container: copy the folder into `~/.claude/skills/` (Windows:
  `%USERPROFILE%\.claude\skills\`).
  - `SKILL.md`: the workflow above and the listing rules.
  - `ebay_lister.py`: **Python 3, standard library only** (no venv, no packages). Commands:
    `category`, `aspects`, `comps`, `preview` and `csv`.
- Claude Code itself does the photo work (sorting, reading labels, writing the listing). No
  Anthropic API key.
- **eBay lookups are read-only**, with a production *application* token (client credentials:
  App ID and Cert ID only, no access to my account). They use the Taxonomy API for category
  suggestions and aspects, the Metadata API for conditions, and the Browse API for active
  comps. Sandbox is not used: it returns placeholder data for these calls, and the drafts
  upload doesn't exist there.
- Keys live in a config file in the home folder, not in the repo: `~/.config/ebay-lister/`
  (Windows: `%APPDATA%\ebay-lister\`). The skill's setup step asks for them.
- No database. Each item is `items/<id>/` with `photos/` and `item.json` (listing + status:
  `draft`, `approved`, `in-csv`). `inbox/`, `items/` and `out/` are in the working folder and git-ignored.

## Order of work

1. Developer account approval (in progress), then copy the production App ID and Cert ID into
   the config. This is the only setup.
2. Build the skill: `SKILL.md`, `ebay_lister.py` (lookups, preview, CSV), with tests for the
   CSV writer.
3. A dry run with 2–3 real items, then upload the first real CSV.
