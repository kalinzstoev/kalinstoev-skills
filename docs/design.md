# eBay Lister: design

Agreed in a `/grill-me` session on 2026-10-24. Code follows this; change the doc first if
the plan changes.

## The experience

1. Take photos of all the items with the phone.
2. Copy them in one dump into `inbox/` in the project folder on the PC.
3. Open the web app (http://localhost:8000) and click **Process inbox**.
4. Claude sorts the photos into items by appearance (helped by capture timestamps) and
   drafts a listing per item. Each item is a card that looks like an eBay listing.
5. Fix any sorting mistakes: drag a photo to another card, split or merge cards, then
   regenerate the affected cards.
6. Review each card. Every field is editable in place; fields Claude couldn't fill from
   the photos (dimensions, "does it work?") are highlighted. **Regenerate** takes an
   optional instruction ("mention it's a 2019 model").
7. **Approve** runs eBay's verify call: shows fees and any errors, posts nothing.
8. **Publish** creates the live listing; the card shows the eBay link. That's where the
   app stops: revising, ending and sales are handled in eBay Seller Hub.

Nothing is listed without an explicit Approve and Publish on that card.

## Listing rules

- Marketplace: **eBay UK** (`EBAY_GB`), GBP. Fixed price (Buy It Now).
- Category: eBay's suggested category; item specifics are the category's required and
  recommended aspects from eBay, filled by Claude from the photos and blank (highlighted)
  where it can't tell.
- Description: clean, simple HTML. Short intro, bullet list of features and condition,
  defects, what's included. No templates, banners or emojis, no claims the photos don't
  support.
- Price: Claude's estimate plus a few **active** comparable listings (Browse API) as a
  sanity check; I set the final price. Sold comps are not used.
- Best Offer: per-item toggle, off by default, with an auto-decline floor.
- Postage: two or three fixed presets (e.g. Royal Mail small/medium parcel), Claude
  suggests one, I confirm. Collection-only as an option for bulky items.
- Returns: none by default; 30-day returns as a per-item option.
- Postage/returns/payment are eBay business policies created once and picked per card.

## Technical decisions

- **Python**, venv. **FastAPI** backend, server-rendered pages, small vanilla JS for
  drag-and-drop and inline editing. No frontend framework, no build step.
- **Claude Opus 5.5** for sorting and drafting (check the `claude-api` skill before coding).
- **eBay Trading API** (`AddFixedPriceItem`, `VerifyAddFixedPriceItem`) so listings stay
  editable in Seller Hub. To be confirmed with `research` against eBay docs, along with:
  category suggestions, item aspects, photo upload/hosting, Browse API comps, auth tokens,
  business policies in Sandbox.
- **Sandbox only** until I say otherwise; the page shows a clear SANDBOX banner.
- No database. Each item is `items/<id>/` with `photos/` and `item.json` (draft + status).
  Photos are moved from `inbox/` into item folders, never deleted. `inbox/` and `items/`
  are git-ignored.
- The app listens on port 8000, published as `127.0.0.1:8000:8000` in
  `docker-compose.yml` (needs `docker compose up -d` on the host).

## Order of work

1. `research`: confirm the eBay API facts above; write findings to `docs/`.
2. `wizard`: one-time setup I do myself (developer account, Sandbox keys, Sandbox test
   seller, app authorisation, business policies), ending with a check that the keys work.
3. Build: inbox sorting and drafting → web app cards and editing → verify/publish in
   Sandbox.
4. Switch to production only on my go-ahead.
