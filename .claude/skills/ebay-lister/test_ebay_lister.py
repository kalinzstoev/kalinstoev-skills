"""Tests for ebay_lister.py. Run: python -m unittest test_ebay_lister.py (from this folder)."""

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

import ebay_lister


def make_item(**overrides):
    item = {
        "id": "01-nike-trainers",
        "status": "approved",
        "title": "Nike Air Max 90 Trainers UK 9 Blue",
        "category_id": "15709",
        "category_name": "Men's Trainers",
        "condition": "USED",
        "price": 25,
        "specifics": {"Brand": "Nike", "Colour": "Blue", "Style": ""},
        "description_html": "<p>Nike trainers.</p>\n<ul>\n<li>UK 9</li>\n</ul>",
        "photos": ["photos/IMG_0001.jpg"],
    }
    item.update(overrides)
    return item


class ItemsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.items = self.root / "items"

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, item):
        folder = self.items / item["id"]
        (folder / "photos").mkdir(parents=True)
        (folder / "item.json").write_text(json.dumps(item), encoding="utf-8")

    def run_csv(self):
        return ebay_lister.main(["csv", "--items", str(self.items),
                                 "--out-dir", str(self.root / "out")])

    def read_csv(self):
        [path] = (self.root / "out").glob("drafts-*[0-9].csv")
        raw = path.read_bytes()
        with open(path, newline="", encoding="utf-8") as f:
            return raw, list(csv.reader(f))


class ProblemsTest(unittest.TestCase):
    def test_valid_item_has_no_problems(self):
        self.assertEqual(ebay_lister.problems(make_item()), [])

    def test_catches_each_required_field(self):
        cases = {
            "category_id": ("Trainers", "category_id"),
            "title": ("x" * 81, "81 characters"),
            "price": (0, "price"),
            "condition": ("Used - like new", "condition"),
            "description_html": ("  ", "description"),
        }
        for field, (value, expected) in cases.items():
            with self.subTest(field=field):
                found = ebay_lister.problems(make_item(**{field: value}))
                self.assertTrue(any(expected in p for p in found), found)


class CsvTest(ItemsTestCase):
    def test_writes_draft_rows_in_template_format(self):
        self.add(make_item())
        self.add(make_item(id="02-blender", title="Kenwood Hand Blender", price="12.5",
                           condition="NEW", specifics={"Brand": "Kenwood", "Model": "HB615"}))
        self.assertEqual(self.run_csv(), 0)
        raw, rows = self.read_csv()

        self.assertIn(b"\r\n", raw)
        self.assertTrue(rows[0][0] == "#INFO" and rows[3][0] == "#INFO")
        header = rows[4]
        # eBay ignores C: item specifics columns in the drafts template, so none are added.
        self.assertEqual(header, ebay_lister.UK_COLUMNS)
        self.assertTrue(all(len(r) == len(header) for r in rows))

        first, second = (dict(zip(header, r)) for r in rows[5:])
        self.assertEqual(first[header[0]], "Draft")
        self.assertEqual(first["Custom label (SKU)"], "01-nike-trainers")
        self.assertEqual(first["Price"], "25.00")
        self.assertEqual(first["Format"], "FixedPrice")
        self.assertEqual(first["Item photo URL"], "")
        self.assertNotIn("\n", first["Description"])
        self.assertEqual(second["Price"], "12.50")
        self.assertEqual(second["Condition ID"], "NEW")

    def test_only_approved_items_and_marks_them_in_csv(self):
        self.add(make_item())
        self.add(make_item(id="02-other", status="draft"))
        self.run_csv()
        _, rows = self.read_csv()
        self.assertEqual(len(rows), 6)
        saved = json.loads((self.items / "01-nike-trainers" / "item.json").read_text())
        self.assertEqual(saved["status"], "in-csv")
        self.assertTrue(saved["csv_file"].startswith("drafts-"))
        untouched = json.loads((self.items / "02-other" / "item.json").read_text())
        self.assertEqual(untouched["status"], "draft")

    def test_writes_a_checklist_of_what_is_left_to_do_in_ebay(self):
        self.add(make_item(photos=["photos/IMG_0002.jpg", "photos/IMG_0001.jpg"],
                           condition_suggestion="Pre-owned - Good"))
        self.run_csv()
        [path] = (self.root / "out").glob("drafts-*-checklist.txt")
        text = path.read_text(encoding="utf-8")
        self.assertIn("01-nike-trainers: Nike Air Max 90 Trainers UK 9 Blue", text)
        self.assertIn("Add the 2 photo(s) in this order: IMG_0002.jpg, IMG_0001.jpg", text)
        self.assertIn("(suggested: Pre-owned - Good)", text)
        self.assertIn("it may ask you for: Style", text)
        self.assertIn("£25.00", text)

    def test_invalid_item_blocks_the_whole_csv(self):
        self.add(make_item())
        self.add(make_item(id="02-bad", category_id=""))
        self.assertEqual(self.run_csv(), 1)
        self.assertFalse((self.root / "out").exists())

    def test_refuses_any_action_but_draft(self):
        original = ebay_lister.ACTION
        ebay_lister.ACTION = "Add"
        try:
            with self.assertRaises(RuntimeError):
                ebay_lister.csv_rows([make_item()])
        finally:
            ebay_lister.ACTION = original


class StartTest(ItemsTestCase):
    def test_creates_the_inbox_and_reports_what_is_there(self):
        inbox = self.root / "inbox"
        self.add(make_item())
        args = ["start", "--inbox", str(inbox), "--items", str(self.items)]
        self.assertEqual(ebay_lister.main(args), 0)
        self.assertTrue(inbox.is_dir())

        for name in ("IMG_1.jpg", "IMG_2.JPG", "photos.zip", "IMG_3.heic"):
            (inbox / name).write_bytes(b"")
        shown = io.StringIO()
        with contextlib.redirect_stdout(shown):
            ebay_lister.main(args)
        self.assertIn("2 photo(s), 1 zip file(s)", shown.getvalue())
        self.assertIn("IMG_3.heic", shown.getvalue())
        self.assertIn("Items so far: 1 (1 approved", shown.getvalue())
        self.assertIn("eBay site: UK", shown.getvalue())


US_TEMPLATE = (
    "#INFO,Version=0.0.2,Template= eBay-draft-listings-template_US,,,,,,,,\r\n"
    "#INFO,,,,,,,,,,\r\n"
    "Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8),Custom label (SKU),"
    "Category ID,Title,UPC,Price,Quantity,Item photo URL,Condition ID,Description,Format\r\n"
    "Draft,,47140,Sample row that must not be copied,,11,1,,NEW,Sample,FixedPrice\r\n"
)


class TemplateTest(ItemsTestCase):
    def write_template(self, text):
        path = self.root / "template.csv"
        path.write_text(text, encoding="utf-8", newline="")
        return str(path)

    def test_csv_and_preview_follow_another_sites_template(self):
        template = self.write_template(US_TEMPLATE)
        self.add(make_item())
        out = self.root / "preview.html"
        ebay_lister.main(["preview", "--items", str(self.items), "--out", str(out),
                          "--template", template])
        self.assertIn("$25.00", out.read_text(encoding="utf-8"))

        self.assertEqual(ebay_lister.main(["csv", "--items", str(self.items), "--out-dir",
                                           str(self.root / "out"), "--template", template]), 0)
        _, rows = self.read_csv()
        self.assertEqual(rows[0][2], "Template= eBay-draft-listings-template_US")
        self.assertTrue(rows[2][0].startswith("Action(SiteID=US|"))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[3][0], "Draft")
        self.assertEqual(rows[3][1], "01-nike-trainers")

    def test_rejects_a_file_that_is_not_the_drafts_template(self):
        self.add(make_item())
        for text in ("Title,Price\r\nShoe,5\r\n",
                     "Action(SiteID=US|Country=US|Currency=USD),Title,Price\r\n"):
            with self.subTest(text=text):
                code = ebay_lister.main(["csv", "--items", str(self.items), "--out-dir",
                                         str(self.root / "out"),
                                         "--template", self.write_template(text)])
                self.assertEqual(code, 1)
                self.assertFalse((self.root / "out").exists())


class PreviewTest(ItemsTestCase):
    def test_preview_shows_items_and_flags_blanks(self):
        self.add(make_item(title="<b>Nike</b>"))
        out = self.root / "preview.html"
        self.assertEqual(ebay_lister.main(["preview", "--items", str(self.items),
                                           "--out", str(out)]), 0)
        page = out.read_text(encoding="utf-8")
        self.assertIn("&lt;b&gt;Nike&lt;/b&gt;", page)
        self.assertIn('src="items/01-nike-trainers/photos/IMG_0001.jpg"', page)
        self.assertIn('<tr class="flag"><td>Style</td>', page)
        self.assertIn("£25.00", page)

    def test_preview_shows_the_condition_to_pick_in_ebay(self):
        self.add(make_item(condition_suggestion="Pre-owned - Good"))
        out = self.root / "preview.html"
        ebay_lister.main(["preview", "--items", str(self.items), "--out", str(out)])
        self.assertIn("pick in eBay: Pre-owned - Good", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
