# eBay Lister: design

This is the author's design record, written in the first person ("I" is the person selling).
It explains why the tool works the way it does. To use the tool, start with the README.

First agreed in a `/grill-me` session on 2026-10-24, then simplified the same day after the
eBay research (`docs/ebay-api-research.md`) and a manual draft-upload test. Code follows this;
change the doc first if the plan changes.

## The experience

1. Take photos of all the items with the phone (Android, JPEG).
2. Copy them in one dump into `inbox/` in the working folder.
3. In Claude Code, run `/ebaylister`.
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
  `Condition ID`, `Description`, `Format`.
- `Action` is always `Draft` and the code refuses to write anything else (another value, such as
  `Add`, would create a live listing). `Format` is `FixedPrice`, `Quantity` 1.
- `Custom label (SKU)` is the item id, so a draft can be matched back to its folder.
- `Condition ID` is `NEW` or `USED` only, and the test draft showed eBay does not set the
  condition from it (the value lands in the condition description). I pick the condition in
  eBay; Claude suggests one in the preview. Defects go in the description.
- `Item photo URL` is left empty: I add the photos on the phone. (The test draft did import a
  web-hosted photo from this column, so hosted photos would work if ever wanted.)
- Item specifics are **not** in the CSV: a test upload on 2026-10-24 with `C:Brand` and
  `C:Colour` columns went through, but the draft had no specifics. On the first real listing
  eBay's AI filled them itself; the filled ones are also listed in the description's DETAILS
  section, as the user's template asks.
  eBay's editor prefills item specifics from title keywords and photos ("Suggested item
  specifics"), and inferred some from the category (Department, Type, Style), so the title
  should carry brand, model, size and colour.
- What did carry over in the test draft: title, description, price, quantity, category and the
  photo. Category 47140 showed as Men's Shoes > Trainers. Listing fee showed £0.00.

## Listing rules

- Marketplace: **eBay UK**, GBP, Buy It Now (fixed price). Other sites: see "Other eBay sites".
- Category: the eBay UK leaf category ID that fits the item, from Claude's knowledge, checked
  with a web search when unsure. Shown with its name in the preview so I can catch a wrong one.
  On the first real listing eBay picked the category up correctly, so a best guess is enough.
- Item specifics: the category's usual required and recommended aspects (eBay UK names, e.g.
  `Colour`, `UK Shoe Size`), filled from the photos, blank and flagged where Claude can't tell.
  Listed in the description's DETAILS (eBay's AI fills the fields; I fix any it misses).
- Title: up to 80 characters, the words a buyer would search for, no filler or caps.
- Description: the user's template (in `SKILL.md`): a title line, one condition sentence, then
  FEATURES, CONDITION: <GRADE>, INCLUDED and DETAILS sections with typed `•` bullets. Plain text
  with `<br>` line breaks only, no other HTML. No templates, banners or emojis, and no claims the photos don't support.
- Price: Claude's estimate with a short reason, checked with a web search for similar items
  where useful. I set the final price in the preview or in eBay.
- Postage, returns, payment and Best Offer are set in eBay when I finish the draft.

## Other eBay sites

Added 2026-11-15, when the project was opened up for others to use.

- eBay UK stays the built-in default and is the only site tested.
- A seller on another site saves that site's own "Create drafts" template as
  `ebay-template.csv` in the working folder (or passes `--template`). The script copies the
  template's `#INFO` lines and header row, fills the columns it knows by name and leaves the
  rest empty. Site, country and currency are read from the `Action(SiteID=…|Country=…|
  Currency=…)` header.
- Reading eBay's own file was chosen over a table of sites in the code: the header values for
  other sites could not be confirmed from eBay's documentation, and a guessed header could be
  rejected or, worse, misread.
- A template without the columns the tool fills is refused. `Action` is still always `Draft`.
- Category IDs and item specific names differ per site, so `SKILL.md` has Claude run
  `ebay_lister.py site` first and work for that site.

## Ease of use

Added 2026-11-15. The skill should be usable by someone who has never opened a terminal.

- `/ebaylister` is the only thing the user types. Claude checks Python, and the script's
  `start` command creates `inbox/`, unpacks photo zips and reports what is there, so the user
  is told where to put photos instead of having to know. Unzipping is in the script because
  a test run on Windows showed shell `unzip` can't be relied on.
- `preview --open` opens the preview in the browser (falling back to printing the path, e.g.
  in a container).
- `csv` also writes `out/drafts-<date-time>-checklist.txt`: per item, the photos in order, the
  condition to pick (`condition_suggestion` in `item.json`), the specifics eBay may ask for,
  and the category and price to check. Finishing drafts in eBay is the most manual step, so it
  gets a list to tick off.
- `SKILL.md` tells Claude to use plain words and never ask the user to edit a file or run a
  command.
- The Docker dev container is the author's preference for isolation, not a requirement.

## Packaging

Added 2026-11-15.

- The repo root is a Claude Code plugin (`.claude-plugin/plugin.json`) and a one-plugin
  marketplace (`.claude-plugin/marketplace.json`, source `./`), so anyone can install with
  `/plugin install kalinstoev-skills --marketplace kalinzstoev/kalinstoev-skills` and get updates.
- The skill sits in `skills/ebaylister/`, the standard location that both the plugin loader
  and the `npx skills` CLI look in. It was in `.claude/skills/` while this was a personal
  project; that only worked for people who opened this repo's folder.
- `plugin.json` has no `version`, so each pushed commit is a new version and users get
  updates without a manual bump.
- `CLAUDE.md` moved to `.claude/CLAUDE.md`: Claude Code warns about one at a plugin root.
- Installed as a plugin the skill is `/kalinstoev-skills:ebaylister`; copied or installed as a
  plain skill it is `/ebaylister`. It also triggers from a plain request.
- Renamed the same day from plugin and skill both called `ebay-lister`, which gave the
  repetitive `/ebay-lister:ebay-lister`. Following the layout of `mattpocock/skills`, the
  plugin (and repo) is named for the collection, `kalinstoev-skills`, and each skill for
  what it does. More skills can be added under `skills/` without a new install. The
  script keeps its name, `ebay_lister.py`.

## Technical decisions

- A **Claude Code skill**, `skills/ebaylister/`, committed in this repo. The repo is also a
  Claude Code plugin and its own marketplace (see "Packaging"), and the folder still works
  copied into `~/.claude/skills/` (Windows: `%USERPROFILE%\.claude\skills\`).
  - `SKILL.md`: the workflow above and the listing rules.
  - `ebay_lister.py`: **Python 3, standard library only** (no venv, no packages). Commands:
    `start` (create the inbox, report the folder), `preview` (build `preview.html` from the
    items), `csv` (validate the approved items, write the drafts CSV and the checklist) and
    `site` (show which eBay site the CSV is written for).
- Claude Code itself does the photo work (sorting, reading labels, writing the listing). No
  Anthropic API key.
- **No eBay API and no keys** (decided 2026-10-24). Nothing to set up. If too many drafts need
  their category or item specifics fixed by hand, add read-only lookups later with a production
  application token (Taxonomy, Metadata and Browse APIs; see `docs/ebay-api-research.md`).
- No database. Each item is `items/<id>/` with `photos/` and `item.json` (listing + status:
  `draft`, `approved`, `in-csv`). `inbox/`, `items/` and `out/` are in the working folder and
  git-ignored.

## Order of work

1. Build the skill: `SKILL.md`, `ebay_lister.py` (preview, CSV), with tests for the CSV writer.
2. A dry run with 2–3 real items, then upload the first real CSV.
3. Review how many drafts needed fixing; decide whether eBay lookups are worth adding.

**Outcome (2026-11-15):** all 9 items listed. The skill worked well; the remaining manual
work was in eBay itself after the draft went live (photos, condition, specifics), which the
CSV can't carry. No eBay lookups needed. The tool is done.
