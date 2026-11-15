#!/usr/bin/env python3
"""Helpers for the ebaylister skill: build a preview page and write eBay's drafts CSV.

Standard library only, so it runs anywhere Python 3 does (container or Windows).

    python ebay_lister.py start   [--inbox inbox] [--items items] [--out-dir out]
    python ebay_lister.py preview [--items items] [--out preview.html] [--open]
    python ebay_lister.py csv     [--items items] [--out-dir out]
    python ebay_lister.py site

The CSV is written for eBay UK unless eBay's "Create drafts" template for another site is
saved as ebay-template.csv in the working folder (or passed with --template).

Each item lives in items/<id>/item.json next to a photos/ folder. See SKILL.md for the
item.json fields.
"""

import argparse
import csv
import datetime
import html
import json
import re
import shutil
import sys
import webbrowser
import zipfile
from pathlib import Path

# The only Action this tool may ever write. Anything else (e.g. "Add") would create a
# live listing when the CSV is uploaded.
ACTION = "Draft"

# The built-in template, copied from eBay's UK "Create drafts" template (Version=0.0.2),
# Seller Hub → Reports. Other sites are read from the seller's own copy (load_template).
UK_INFO_LINES = [
    ["#INFO", "Version=0.0.2", "Template= eBay-draft-listings-template_GB"],
    ["#INFO Action and Category ID are required fields. 1) Set Action to Draft 2) Please find "
     "the category ID for your listings here: "
     "https://pages.ebay.com/sellerinformation/news/categorychanges.html"],
    ["#INFO After you've successfully uploaded your draft from the Seller Hub Reports tab, "
     "complete your drafts to active listings here: https://www.ebay.co.uk/sh/lst/drafts"],
    ["#INFO"],
]
UK_COLUMNS = [
    "Action(SiteID=UK|Country=GB|Currency=GBP|Version=1193|CC=UTF-8)",
    "Custom label (SKU)", "Category ID", "Title", "UPC", "Price", "Quantity",
    "Item photo URL", "Condition ID", "Description", "Format",
]

# A template for another eBay site is picked up from this file in the working folder.
TEMPLATE_FILE = "ebay-template.csv"
# Columns this tool fills in; a template without them can't be used.
REQUIRED_COLUMNS = [
    "Custom label (SKU)", "Category ID", "Title", "Price", "Quantity", "Condition ID",
    "Description", "Format",
]
CURRENCY_SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€", "AUD": "A$", "CAD": "C$"}

CONDITIONS = {"NEW", "USED"}
TITLE_MAX = 80
STATUSES = {"draft", "approved", "in-csv"}
# Photo types Claude can look at directly; anything else in the inbox is reported.
PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".webp"}
# Also unpacked from zips, so they are reported rather than silently left behind.
OTHER_IMAGE_TYPES = {".heic", ".heif"}


# ── Items ────────────────────────────────────────────────────────────────────

def load_items(items_dir):
    """All items under items_dir, sorted by id. Each gets a '_dir' key with its folder."""
    items = []
    for path in sorted(Path(items_dir).glob("*/item.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        item["_dir"] = path.parent
        items.append(item)
    return items


def save_item(item):
    data = {k: v for k, v in item.items() if not k.startswith("_")}
    path = item["_dir"] / "item.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def spec_value(value):
    """An item specific as text: lists are joined with ', ', blanks become ''."""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return "" if value is None else str(value).strip()


def problems(item):
    """Reasons this item can't go into the CSV yet (empty list = ready)."""
    found = []
    if not str(item.get("id", "")).strip():
        found.append("missing id")
    if not re.fullmatch(r"\d+", str(item.get("category_id", "")).strip()):
        found.append("category_id must be a number")
    title = str(item.get("title", "")).strip()
    if not title:
        found.append("missing title")
    elif len(title) > TITLE_MAX:
        found.append(f"title is {len(title)} characters (max {TITLE_MAX})")
    try:
        if float(item.get("price")) <= 0:
            found.append("price must be above 0")
    except (TypeError, ValueError):
        found.append("missing or invalid price")
    if item.get("condition") not in CONDITIONS:
        found.append("condition must be NEW or USED")
    if not str(item.get("description_html", "")).strip():
        found.append("missing description")
    if item.get("status", "draft") not in STATUSES:
        found.append(f"unknown status {item.get('status')!r}")
    return found


def blank_specifics(item):
    return [name for name, value in item.get("specifics", {}).items() if not spec_value(value)]


# ── Template ─────────────────────────────────────────────────────────────────

def load_template(path=None):
    """The drafts template to write: its #INFO lines, header columns and where it came from.

    Uses `path`, else ebay-template.csv in the working folder, else the built-in UK template.
    The file is eBay's own "Create drafts" template for the seller's site, as downloaded.
    """
    if path is None and Path(TEMPLATE_FILE).exists():
        path = TEMPLATE_FILE
    if path is None:
        return {"info_lines": UK_INFO_LINES, "columns": UK_COLUMNS, "source": "built-in"}

    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [[cell.strip() for cell in row] for row in csv.reader(f)]
    info_lines, columns = [], None
    for row in rows:
        while row and not row[-1]:
            row.pop()
        if row and row[0].startswith("#INFO"):
            info_lines.append(row)
        elif row and row[0].startswith("Action(") and row[0].endswith(")"):
            columns = row
            break
    if columns is None:
        raise ValueError(f"{path}: no header row starting with 'Action(' found. Is this "
                         "eBay's \"Create drafts\" template?")
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise ValueError(f"{path}: the template has no column(s): {', '.join(missing)}")
    return {"info_lines": info_lines, "columns": columns, "source": str(path)}


def site_info(template):
    """SiteID, Country, Currency… from the template's Action header, plus a currency symbol."""
    parts = template["columns"][0][len("Action("):-1].split("|")
    info = dict(part.split("=", 1) for part in parts if "=" in part)
    currency = info.get("Currency", "")
    info["symbol"] = CURRENCY_SYMBOLS.get(currency, f"{currency} ".lstrip())
    return info


def cmd_site(args):
    template = load_template(args.template)
    info = site_info(template)
    print(f"Site: {info.get('SiteID', '?')}, country: {info.get('Country', '?')}, "
          f"currency: {info.get('Currency', '?')}, template: {template['source']}")
    return 0


# ── Start ────────────────────────────────────────────────────────────────────

def free_path(folder, name):
    """folder/name, with -1, -2… added before the extension if that file already exists."""
    path = folder / name
    count = 0
    while path.exists():
        count += 1
        path = folder / f"{Path(name).stem}-{count}{Path(name).suffix}"
    return path


def unpack_zips(inbox, out_dir):
    """Unpack the images in every zip in the inbox, then move the zip to out_dir.

    Only image files are taken, each under its bare file name (folders inside the zip are
    dropped, so nothing can land outside the inbox), and nothing is overwritten.
    Returns {zip name: number of images unpacked}.
    """
    unpacked = {}
    for archive in sorted(f for f in inbox.iterdir() if f.suffix.lower() == ".zip"):
        count = 0
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                name = Path(member.filename.replace("\\", "/")).name
                if member.is_dir() or Path(name).suffix.lower() not in (
                        PHOTO_TYPES | OTHER_IMAGE_TYPES):
                    continue
                with z.open(member) as src, open(free_path(inbox, name), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                count += 1
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(archive), str(free_path(out_dir, archive.name)))
        unpacked[archive.name] = count
    return unpacked


def cmd_start(args):
    """Make sure the inbox exists, unpack any photo zips and say what is in the folder."""
    info = site_info(load_template(args.template))
    inbox = Path(args.inbox)
    inbox.mkdir(parents=True, exist_ok=True)
    unpacked = unpack_zips(inbox, Path(args.out_dir))
    files = sorted(f for f in inbox.iterdir() if f.is_file())
    photos = [f for f in files if f.suffix.lower() in PHOTO_TYPES]
    other = [f.name for f in files if f not in photos]

    print(f"Inbox folder: {inbox.resolve()}")
    for name, count in unpacked.items():
        print(f"  unpacked {count} image(s) from {name} (zip moved to {Path(args.out_dir)})")
    print(f"  {len(photos)} photo(s)")
    if other:
        print(f"  other files (not photos Claude can read): {', '.join(other)}")
    items = load_items(args.items)
    counts = {status: sum(i.get("status", "draft") == status for i in items)
              for status in sorted(STATUSES)}
    print(f"Items so far: {len(items)} "
          f"({', '.join(f'{n} {status}' for status, n in counts.items())})")
    print(f"eBay site: {info.get('SiteID', '?')}, currency: {info.get('Currency', '?')}")
    return 0


# ── CSV ──────────────────────────────────────────────────────────────────────

def csv_rows(items, template=None):
    """The full drafts CSV (info lines, header, one Draft row per item) as lists of cells.

    Item specifics are not written: a test upload on 2026-10-24 showed eBay ignores extra
    C:<aspect> columns in the drafts template. They go in the description instead.
    """
    template = template or load_template()
    header = template["columns"]
    info_lines = template["info_lines"]

    # eBay's template pads the info lines to the full width with empty cells.
    rows = [line + [""] * (len(header) - len(line)) for line in info_lines] + [header]
    for item in items:
        # Uploaded CSV cells are safest on one line; HTML doesn't need the newlines.
        description = " ".join(str(item["description_html"]).split())
        row = {
            header[0]: ACTION,
            "Custom label (SKU)": item["id"],
            "Category ID": str(item["category_id"]).strip(),
            "Title": str(item["title"]).strip(),
            "Price": f"{float(item['price']):.2f}",
            "Quantity": "1",
            "Condition ID": item["condition"],
            "Description": description,
            "Format": "FixedPrice",
        }
        rows.append([row.get(column, "") for column in header])

    # Belt and braces: never write a row that could create a live listing.
    for cells in rows[len(info_lines) + 1:]:
        if cells[0] != "Draft":
            raise RuntimeError(f"refusing to write Action {cells[0]!r}")
    return rows


def checklist(items, csv_name, symbol):
    """What the seller still does in eBay after the upload, as plain text to tick off."""
    lines = [
        "Finish your drafts in eBay",
        "",
        f"1. Upload {csv_name}: Seller Hub > Reports > Uploads > Upload template.",
        "   Don't open the file in Excel first.",
        "2. Open each draft below in the eBay app or Seller Hub and tick off the steps.",
        "   Each draft's custom label is the short name at the start of its entry here.",
    ]
    for item in items:
        photos = [Path(photo).name for photo in item.get("photos", [])]
        suggestion = str(item.get("condition_suggestion", "")).strip()
        blanks = blank_specifics(item)
        lines += [
            "",
            f"{item['id']}: {item['title']}",
            f"  [ ] Add the {len(photos)} photo(s) in this order: {', '.join(photos)}",
            "  [ ] Pick the condition" + (f" (suggested: {suggestion})" if suggestion else ""),
            "  [ ] Accept the item specifics eBay suggests"
            + (f"; it may ask you for: {', '.join(blanks)}" if blanks else ""),
            f"  [ ] Check the category: {item.get('category_name') or item['category_id']}",
            f"  [ ] Check the price ({symbol}{float(item['price']):.2f}) and the postage",
            "  [ ] Publish",
        ]
    return "\n".join(lines) + "\n"


def write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\r\n").writerows(rows)


def cmd_csv(args):
    template = load_template(args.template)
    items = [i for i in load_items(args.items) if i.get("status") == "approved"]
    if not items:
        print("No approved items. Set \"status\": \"approved\" in item.json first.")
        return 1
    bad = {i.get("id", str(i["_dir"])): problems(i) for i in items}
    bad = {k: v for k, v in bad.items() if v}
    if bad:
        for item_id, found in bad.items():
            print(f"{item_id}: {'; '.join(found)}")
        print("No CSV written.")
        return 1

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = Path(args.out_dir) / f"drafts-{stamp}.csv"
    write_csv(csv_rows(items, template), path)
    for item in items:
        item["status"] = "in-csv"
        item["csv_file"] = path.name
        save_item(item)
        note = f" (blank specifics: {', '.join(blank_specifics(item))})" if blank_specifics(item) else ""
        print(f"  {item['id']}: {item['title']}{note}")
    info = site_info(template)
    todo = path.with_name(f"{path.stem}-checklist.txt")
    todo.write_text(checklist(items, path.name, info["symbol"]), encoding="utf-8")
    print(f"Wrote {len(items)} draft(s) for eBay {info.get('SiteID', '?')} to {path.resolve()}")
    print(f"What to do next in eBay: {todo.resolve()}")
    return 0


# ── Preview ──────────────────────────────────────────────────────────────────

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>eBay drafts preview</title>
<style>
  :root {{ --bg: #f5f5f5; --card: #fff; --text: #191919; --muted: #707070;
          --line: #e5e5e5; --flag: #fff4cc; --bad: #c62828; --ok: #2e7d32; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #121212; --card: #1e1e1e; --text: #eee; --muted: #9e9e9e;
            --line: #333; --flag: #4a3d00; --bad: #ef9a9a; --ok: #a5d6a7; }}
  }}
  body {{ margin: 0; padding: 16px; background: var(--bg); color: var(--text);
         font: 15px/1.5 system-ui, sans-serif; }}
  main {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 20px; }}
  .item {{ background: var(--card); border: 1px solid var(--line); border-radius: 8px;
          padding: 16px; margin: 0 0 24px; }}
  .top {{ display: flex; justify-content: space-between; gap: 12px; color: var(--muted);
         font-size: 13px; flex-wrap: wrap; }}
  h2 {{ font-size: 20px; margin: 8px 0 4px; }}
  .price {{ font-size: 24px; font-weight: 700; }}
  .photos {{ display: flex; gap: 8px; overflow-x: auto; margin: 12px 0; }}
  .photos img {{ height: 160px; border-radius: 4px; border: 1px solid var(--line); }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  td {{ border-top: 1px solid var(--line); padding: 4px 8px; vertical-align: top; }}
  td:first-child {{ color: var(--muted); width: 35%; }}
  .flag {{ background: var(--flag); }}
  .problems {{ color: var(--bad); }}
  .ready {{ color: var(--ok); }}
  .desc {{ border-top: 1px solid var(--line); padding-top: 8px; }}
  .note {{ color: var(--muted); font-size: 13px; }}
</style>
</head>
<body>
<main>
<h1>eBay drafts preview · {count} item(s)</h1>
{items}
</main>
</body>
</html>
"""


def esc(value):
    return html.escape("" if value is None else str(value))


def render_item(item, page_dir, symbol="£"):
    found = problems(item)
    status = item.get("status", "draft")
    if found:
        state = f'<p class="problems">Not ready: {esc("; ".join(found))}</p>'
    else:
        state = f'<p class="ready">Ready ({esc(status)})</p>'

    photos = []
    for photo in item.get("photos", []):
        path = (item["_dir"] / photo).resolve()
        try:
            src = path.relative_to(page_dir.resolve()).as_posix()
        except ValueError:
            src = path.as_uri()
        photos.append(f'<img src="{esc(src)}" alt="{esc(Path(photo).name)}" loading="lazy">')

    spec_rows = []
    for name, value in item.get("specifics", {}).items():
        shown = spec_value(value)
        cls = "" if shown else ' class="flag"'
        spec_rows.append(f"<tr{cls}><td>{esc(name)}</td><td>{esc(shown) or '?'}</td></tr>")

    try:
        price = f"{symbol}{float(item.get('price')):.2f}"
    except (TypeError, ValueError):
        price = f"{symbol}?"
    suggestion = str(item.get("condition_suggestion", "")).strip()
    if suggestion:
        suggestion = f" · pick in eBay: {esc(suggestion)}"
    notes = "".join(f'<p class="note">{esc(n)}</p>' for n in item.get("notes", []))
    price_note = item.get("price_note")
    if price_note:
        notes = f'<p class="note">Price: {esc(price_note)}</p>' + notes

    return f"""<section class="item">
  <div class="top"><span>{esc(item.get("id"))} · {len(item.get("photos", []))} photo(s)</span>
  <span>Category {esc(item.get("category_id"))} · {esc(item.get("category_name"))}</span></div>
  <h2>{esc(item.get("title"))}</h2>
  <div class="note">{len(str(item.get("title", "")))}/{TITLE_MAX} characters · Condition: {esc(item.get("condition"))}{suggestion}</div>
  <div class="price">{price}</div>
  {state}
  <div class="photos">{"".join(photos)}</div>
  <table>{"".join(spec_rows)}</table>
  <div class="desc">{item.get("description_html", "")}</div>
  {notes}
</section>"""


def cmd_preview(args):
    symbol = site_info(load_template(args.template))["symbol"]
    items = load_items(args.items)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(render_item(i, out.parent, symbol) for i in items) or "<p>No items yet.</p>"
    out.write_text(PAGE.format(count=len(items), items=body), encoding="utf-8")
    print(f"Wrote {out} ({len(items)} item(s))")
    for item in items:
        found = problems(item)
        flags = "; ".join(found) if found else "ready"
        blanks = blank_specifics(item)
        if blanks:
            flags += f"; blank specifics: {', '.join(blanks)}"
        print(f"  {item.get('id')} [{item.get('status', 'draft')}]: {flags}")
    if args.open:
        if webbrowser.open(out.resolve().as_uri()):
            print("Opened the preview in the browser.")
        else:
            print(f"Couldn't open a browser. Open this file by hand: {out.resolve()}")
    return 0


# ── Main ─────────────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("start", help="create the inbox folder and show what is in it")
    p.add_argument("--inbox", default="inbox")
    p.add_argument("--items", default="items")
    p.add_argument("--out-dir", default="out")
    p.set_defaults(func=cmd_start)
    p = sub.add_parser("preview", help="build an HTML preview of all items")
    p.add_argument("--items", default="items")
    p.add_argument("--out", default="preview.html")
    p.add_argument("--open", action="store_true", help="open the preview in the browser")
    p.set_defaults(func=cmd_preview)
    p = sub.add_parser("csv", help="write the drafts CSV for approved items")
    p.add_argument("--items", default="items")
    p.add_argument("--out-dir", default="out")
    p.set_defaults(func=cmd_csv)
    p = sub.add_parser("site", help="show which eBay site and currency the CSV is written for")
    p.set_defaults(func=cmd_site)
    for p in sub.choices.values():
        p.add_argument("--template", help="eBay's \"Create drafts\" template for your site "
                       f"(default: {TEMPLATE_FILE} in the working folder, else eBay UK)")
    args = parser.parse_args(argv)
    # Titles and notes can hold characters a Windows console can't print; don't crash on them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    try:
        return args.func(args)
    except (ValueError, zipfile.BadZipFile) as error:
        print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
