# eBay API research

Researched 2026-10-24 for `docs/design.md`. Sources are eBay-owned pages only: developer.ebay.com
docs, eBay's OpenAPI specs, Trading API references and release notes, and a few ebay.co.uk /
pages.ebay.com help pages for Seller Hub behaviour. Two archived developer.ebay.com pages
(web.archive.org) are used for the retired Listing API and are marked as such. **UNCONFIRMED**
marks anything I could not check against a primary page.

Several developer.ebay.com pages returned HTTP 403 to automated fetches, including the
API Deprecation Status page, the OAuth guides (`/api-docs/static/oauth-*.html`) and API Call
Limits. Facts from those topics come from other eBay pages (newsletters, specs, references) or
are marked UNCONFIRMED.

## Summary and recommended design changes

1. **`UploadSiteHostedPictures` is gone.** It was decommissioned on 2026-09-30. Upload photos
   with the **Media API `createImageFromFile`** and put the returned EPS `imageUrl` into
   `Item.PictureDetails.PictureURL` of the Trading API call. eBay documents this combination as
   supported.
2. **Trading API is still the right choice for publishing.** `AddFixedPriceItem` and
   `VerifyAddFixedPriceItem` are current, with no deprecation notice. The latest release is 1487
   (2026-10-06). eBay states that **Inventory API listings cannot be edited in Seller Hub**,
   which confirms the reason the design chose Trading. (eBay does recommend the Inventory API for
   new integrations in general.)
3. **Read-only calls must use production.** `getCategorySuggestions` is "not supported in the
   Sandbox" and returns boilerplate there. Browse search in Sandbox only has mock data. eBay
   recommends production for search and metadata calls. Change "Sandbox only" in the design to
   **"writes in Sandbox; read-only Taxonomy, Metadata and Browse calls with a production
   *application* token"**. That needs production app keys early, but no user consent.
4. **Use the Metadata API for shipping services, not `GeteBayDetails`.** `GeteBayDetails` is
   deprecated and will be decommissioned on 2027-03-15. Use `getShippingServices`,
   `getItemConditionPolicies`, `getReturnPolicies` and `getNegotiatedPricePolicies`.
5. **The draft-handoff idea is possible, but not through the Listing API.** The Sell Listing API
   (`createItemDraft`) was "available only to select Partners", and its docs now return 404. The
   supported route is the **Sell Feed API `FX_LISTING` upload of a Seller Hub "Create new drafts"
   CSV**. It is **production only** (no Sandbox). It carries title, category, price, quantity,
   description, NEW/USED and up to 24 photo URLs, but **no item specifics or policies**. See
   section 0.
6. **Business policies:** opt in with `optInToProgram` (`SELLING_POLICY_MANAGEMENT`); it can
   take up to 24 hours. Then create one fulfillment, one return and one payment policy per preset
   with the Account API, and reference them in `Item.SellerProfiles`.

## 0. Draft listings for the seller to finish in eBay (priority question)

### (a) Sell Listing API `createItemDraft`: retired, partner-only

- The overview said: "This API is available only to select Partners." It supported EBAY_GB.
  URLs had to be https. Single-SKU items only.
  ([archived overview, 2020](http://web.archive.org/web/20200920113350/https://developer.ebay.com/api-docs/sell/listing/static/overview.html))
- `POST https://api.ebay.com/sell/listing/v1_beta/item_draft/`, scope `sell.item.draft`
  (authorization-code grant). The body held `categoryId`, `condition` (enum),
  `format` (FIXED_PRICE/AUCTION), `pricingSummary.price`, and `product.{title, description,
  aspects[], brand, epid, imageUrls[] (max 12)}`. It returned `itemDraftId`, `sellFlowUrl` (web)
  and `sellFlowNativeUri` (mobile app), where "the seller can change, update, and publish the
  item on eBay."
  ([archived createItemDraft, 2022](http://web.archive.org/web/20220116183839/https://developer.ebay.com/api-docs/sell/listing/resources/item_draft/methods/createItemDraft))
- **Today:** `https://developer.ebay.com/api-docs/sell/listing/overview.html` and the method
  pages return 404, although the site footer still links to them. The Listing Creation guide
  lists only the Inventory API, the Sell Feed API and the Trading API as ways to create listings
  ([Listing Creation](https://developer.ebay.com/develop/guides/sell/listing-creation)).
  I found no formal decommission notice because the deprecation page was blocked: the exact
  status is **UNCONFIRMED**. Either way it is not usable for a home app.

### (b) Inventory API unpublished offers: not a Seller Hub draft

- "An offer is first created, and then it is published"; eBay provides
  `getListingFees` for unpublished offers.
  ([Inventory API overview](https://developer.ebay.com/api-docs/sell/inventory/overview.html))
- The same page says: "listings created through the Inventory API cannot be edited through
  Seller Hub or any other listing platform." No eBay page says unpublished offers appear in Seller
  Hub or app drafts. **UNCONFIRMED, and very unlikely.**

### (c) Trading API: no draft, only scheduling

- AddFixedPriceItem has no draft mode. `Item.ScheduleTime` "allows the user to specify a time in
  the future that the listing becomes active"; ReviseItem can change it before go-live
  ([AddFixedPriceItem](https://developer.ebay.com/devzone/xml/docs/reference/ebay/AddFixedPriceItem.html)).
  A scheduled listing goes live automatically, so it is not a draft. Scheduling fees, the maximum
  lead time, and whether it shows as "Scheduled" in Seller Hub or the app are **UNCONFIRMED**.

### (d) The supported draft route: Seller Hub "Create new drafts" via the Sell Feed API

- The Sell Feed API feed type `FX_LISTING` uploads Seller Hub templates, including **"Create new
  drafts"**, which maps to the Trading call `VerifyAddItem`
  ([quick reference](https://developer.ebay.com/api-docs/sell/static/feed/fx-feeds-quick-reference.html)).
- Flow: `POST /sell/feed/v1/task` with `{"feedType":"FX_LISTING","schemaVersion":"1.0"}` and
  `X-EBAY-C-MARKETPLACE-ID: EBAY_GB` → `POST /task/{id}/upload_file` (multipart CSV) → poll
  `getTask` until COMPLETED or COMPLETED_WITH_ERROR → `getResultFile`. The task runs
  asynchronously. eBay's guide says the user OAuth token "stays active for two hours".
  ([Seller Hub feed flow](https://developer.ebay.com/api-docs/sell/static/feed/fx-feeds-overview.html),
  [Feed spec](https://developer.ebay.com/develop/api/spec/feed_api.json))
- **Sandbox is not available for this:** "The sandbox environment is not available for the
  upload method specifying either Seller Hub feedTypes ... To test input files without sending
  them to eBay as active listings, use the Draft Action (Create new drafts template)."
  ([feed flow](https://developer.ebay.com/api-docs/sell/static/feed/fx-feeds-overview.html))
- OAuth scope for FX_LISTING: `createTask` lists `sell.inventory` for LMS feed types but names
  none for FX types. Expect **`sell.inventory` (UNCONFIRMED)**.
- **Fields a draft row can carry** (Seller Hub Reports help,
  [Uploadable Templates](https://pages.ebay.com/sh/reports/help/uploadable-file-feeds/)):
  - `Action` = `Draft` (required) and `Category ID` (required). These are the only required
    fields.
  - Custom label (SKU), Title (max 80), UPC, Price, Quantity.
  - Description (simple HTML allowed).
  - Format (`FixedPrice` or `Auction`).
  - Condition ID: **only `NEW` or `USED`**. Finer conditions "will need to be edited in your
    Drafts folder."
  - Item photo URL: up to 24, separated by `|`. The URLs must be hosted somewhere (self-hosted
    or EPS). Photos can also be added later in the Drafts folder.
  - "We do not recommend adding additional columns to this template". **Item specifics,
    postage, returns and Best Offer are therefore not set by the draft.** The seller completes
    them in eBay.
  - Get the exact template from Seller Hub → Reports → Upload → Get template → Listings →
    "Create drafts template". The UK steps are in
    [ebay.co.uk help](https://www.ebay.co.uk/help/selling/selling-tools/file-exchange?id=4096).
- **Photos:** upload with the Media API `createImageFromFile` (production) and put the EPS
  `imageUrl`s in the photo column. Unused EPS images expire; `getImage` returns
  `expirationDate`. The exact unused-image lifetime for Media API images is **UNCONFIRMED** (the
  old UploadSiteHostedPictures doc said 30 days). Publish drafts promptly.
- **Where drafts appear:** the upload "will direct you to your account's Drafts folder". You
  finish them in the Drafts folder or in Bulk Edit and Relist
  ([Uploadable Templates](https://pages.ebay.com/sh/reports/help/uploadable-file-feeds/)).
  On eBay UK, drafts are kept 75 days after the last update. The limit is 250 drafts for "the
  quick listing tool on eBay.co.uk and the eBay mobile app" and 5,000 for "the single and bulk
  business listing tools in Seller Hub"
  ([Seller Centre, drafts retention](https://www.ebay.co.uk/sellercentre/news/2024-february/drafts-retention?targetgroup=B2C)).
  The two separate limits suggest separate draft pools. **Whether uploaded drafts appear in, and
  can be finished from, the eBay mobile app is UNCONFIRMED.** No eBay doc says so, and eBay
  Community reports (not primary) say bulk-tool drafts may not show in the app. Test this with one
  real draft before committing to the approach.
- **Risk of going live or paying fees:** an `Action=Draft` row creates a draft, not a listing.
  The real risk is a wrong `Action` value (for example `Add`), which would create a live
  listing. The app must hard-code `Draft` and validate the CSV. Draft creation corresponds to
  `VerifyAddItem`, and eBay says Verify calls do not "publish the listing or incur fees"
  ([Listing Creation](https://developer.ebay.com/develop/guides/sell/listing-creation)).
  That drafts are fee-free is inferred, so it is **UNCONFIRMED** as an explicit statement.
  Media API image uploads have no documented fee.

### Recommendation for the draft question

- If the user wants "app makes drafts, I finish in eBay", the only supported mechanism is
  **Sell Feed `FX_LISTING` + Create-drafts CSV + Media API photos, in production**. Sandbox is
  of little use: Feed uploads aren't available there, and the read-only calls need production
  anyway.
- Item specifics, detailed condition, postage and returns would be filled in eBay's UI. Claude
  could still draft them into the description or show them in the app for copy-paste.
- First, as a manual spike: upload one draft CSV through Seller Hub Reports in the browser and
  check whether it appears in the mobile app. That answers the biggest unknown without any code.
- If app visibility fails, or the user wants specifics filled automatically, stay with the
  current design: **Trading `VerifyAddFixedPriceItem` / `AddFixedPriceItem`** with Media API
  photos. Listings stay editable in Seller Hub.

## 1. Trading API vs Inventory API for listing

**Status**
- `AddFixedPriceItem`: "You can test this call in the Sandbox environment." There is no
  deprecation note. The latest Trading release is 1487 (2026-10-06). Recent decommissions were
  GetCategories (2026-04), GetCategoryFeatures (2026-06) and GetAdFormatLeads (1487), not the
  Add calls.
  ([AddFixedPriceItem](https://developer.ebay.com/devzone/xml/docs/reference/ebay/AddFixedPriceItem.html),
  [Trading release notes](https://developer.ebay.com/devzone/xml/docs/releasenotes.html))
- Deprecated Trading calls listed in the Q3 2026 newsletter: GetSellerDiscountProfiles and
  SetShippingDiscountProfiles (2027-01-19), GeteBayDetails (2027-03-15). UploadSiteHostedPictures
  was decommissioned in Q3 2026.
  ([Q3 2026 newsletter](https://developer.ebay.com/updates/newsletter/q3_2026),
  [Q2 2026 newsletter](https://developer.ebay.com/updates/newsletter/q2_2026))
- Inventory API: "listings created through the Inventory API cannot be edited through Seller Hub
  or any other listing platform. Any revisions must be done through the Inventory API." It also
  requires business policies and an inventory location.
  ([Inventory API overview](https://developer.ebay.com/api-docs/sell/inventory/overview.html))
  An Inventory-API listing also "cannot be revised using Trading API Revise/Relist calls"
  ([Listing Management](https://developer.ebay.com/develop/guides/sell/listing-management)).
  eBay recommends the Inventory API for new integrations
  ([Listing Creation](https://developer.ebay.com/develop/guides/sell/listing-creation)).
- **Recommendation: Trading API.** It is the only choice that keeps listings editable in Seller
  Hub, as the design requires.

**Fields for a GB fixed-price listing** (all from the
[AddFixedPriceItem reference](https://developer.ebay.com/devzone/xml/docs/reference/ebay/AddFixedPriceItem.html)
unless noted)

| Field | Notes |
|---|---|
| `Item.Title` | Conditionally required (unless a catalog match is used). Max 80 characters, no HTML. |
| `Item.Description` | Conditionally required. HTML goes in CDATA. |
| `Item.PrimaryCategory.CategoryID` | A leaf category on the site's tree. |
| `Item.ConditionID` | Required in most categories. An invalid or missing ID when required makes the call fail. |
| `Item.StartPrice` | "For AddFixedPriceItem and VerifyAddFixedPriceItem: Required when no variations are specified." (The Listing Creation guide mentions `BuyItNowPrice` for fixed price, but the call reference is authoritative: use `StartPrice`.) |
| `Item.Currency` | Required: `GBP`. |
| `Item.Quantity` | Defaults to 1. |
| `Item.ListingDuration` | Required. "As of April 1, 2019, 'GTC' is the only supported listing duration" (except some Motors categories). |
| `Item.ListingType` | `FixedPriceItem`. |
| `Item.Country` | Required: `GB`. |
| `Item.PostalCode` / `Item.Location` | One of the two is required. Location is derived from the postcode if omitted. |
| `Item.DispatchTimeMax` | Required with flat or calculated shipping. Taken from the shipping policy when using business policies. |
| `Item.PictureDetails.PictureURL` | Up to 24, https only. EPS and self-hosted URLs can't be mixed. Images at least 500 px on the longest side. Total length of all URLs ≤ 3975 characters. |
| `Item.ItemSpecifics.NameValueList` | 0..45 entries. Name max 65 characters, value max 65 (more for some instance aspects). Multiple values only if the aspect's cardinality is MULTI. |
| `Item.SellerProfiles` | `SellerPaymentProfile.PaymentProfileID`, `SellerReturnProfile.ReturnProfileID`, `SellerShippingProfile.ShippingProfileID`. "Exactly one" of each. The account must be opted in. These override any inline shipping, returns or payment fields. |
| `Item.Site` | Optional (`UK`). Must match the `X-EBAY-API-SITEID` header. |

- If the account is opted in to business policies, the listing must use `SellerProfiles`.
  Otherwise use the inline `ShippingDetails`, `ReturnPolicy`, `DispatchTimeMax` and so on.
  ([Listing Creation](https://developer.ebay.com/develop/guides/sell/listing-creation))
- `Regulatory` (GPSR, manufacturer and responsible person) exists in the schema. Whether it is
  required for a UK private seller is **UNCONFIRMED**. Verify will report it if it is required.

**`VerifyAddFixedPriceItem`**
- Same payload and validation as AddFixedPriceItem, but it "will not actually publish the listing
  or incur fees" ([Listing Creation](https://developer.ebay.com/develop/guides/sell/listing-creation)).
- Response: `ItemID` is always `0`; `Fees.Fee[]` (`Name`, `Fee` with `currencyID`) lists every
  listing fee, including 0.0 ones, and excludes final value fees; `Errors[]` holds
  `ErrorClassification`, codes and messages (warnings appear here too).
  ([VerifyAddFixedPriceItem](https://developer.ebay.com/devzone/xml/docs/reference/ebay/VerifyAddFixedPriceItem.html))
- AddFixedPriceItem returns `ItemID` and `Fees`. Add and Verify calls share a rate limit; going
  over it returns error 21919144.

**Calling the Trading API**
- Endpoint: `https://api.sandbox.ebay.com/ws/api.dll` (Sandbox) or
  `https://api.ebay.com/ws/api.dll` (production).
- Headers:
  - `X-EBAY-API-CALL-NAME` (for example `AddFixedPriceItem`)
  - `X-EBAY-API-SITEID: 3`
  - `X-EBAY-API-COMPATIBILITY-LEVEL` (always required; use the current version, `1487`)
  - `X-EBAY-API-IAF-TOKEN: <OAuth user access token>`
  - `Content-Type: text/xml`
- With the IAF token, omit `RequesterCredentials`. The App, Dev and Cert headers are not needed
  for listing calls.
  ([Making a Call](https://developer.ebay.com/devzone/xml/docs/Concepts/MakingACall.html),
  [Using the XML Trading API](https://developer.ebay.com/api-docs/user-guides/static/make-a-call/using-xml.html))
- UK is site ID 3, code `UK`, currency GBP
  ([SiteCodeType](https://developer.ebay.com/devzone/xml/docs/reference/ebay/types/SiteCodeType.html)).
- "The Sandbox might not support this call for all eBay sites." Sandbox UK (site 3) support is
  therefore **UNCONFIRMED**; check it in the setup wizard.

## 2. Category suggestions (Taxonomy API)

Source: [Taxonomy OpenAPI spec](https://developer.ebay.com/develop/api/spec/taxonomy_api.json).

- `GET https://api.ebay.com/commerce/taxonomy/v1/get_default_category_tree_id?marketplace_id=EBAY_GB`
  returns `categoryTreeId` and `categoryTreeVersion`. Read the GB tree ID from this call; I did not
  confirm the actual value (believed to be 3, **UNCONFIRMED**).
- `GET /commerce/taxonomy/v1/category_tree/{tree_id}/get_category_suggestions?q=...` returns
  suggested leaf categories with their ancestors.
- Auth: client-credentials (**application**) token with scope `https://api.ebay.com/oauth/api_scope`.
- **Sandbox:** "This call is not supported in the Sandbox environment. It will return a response
  payload in which the categoryName fields contain random or boilerplate text." Suggestions are
  partly driven by live inventory, so treat them as recommendations.

## 3. Item aspects and conditions

**Aspects:** `GET /commerce/taxonomy/v1/category_tree/{tree_id}/get_item_aspects_for_category?category_id=...`,
application token (`api_scope`). Source: the
[Taxonomy spec](https://developer.ebay.com/develop/api/spec/taxonomy_api.json).

- `aspects[].localizedAspectName` (for example "Colour" on UK) is the name to send in
  `NameValueList.Name`.
- `aspectConstraint.aspectRequired: true` means the aspect is required; listing is blocked
  without it.
- `aspectConstraint.aspectUsage` is `RECOMMENDED` or `OPTIONAL`. Required aspects *also* report
  `RECOMMENDED`, so treat "required" = `aspectRequired` and "recommended" = `aspectUsage ==
  RECOMMENDED && !aspectRequired`.
- `aspectMode`: `FREE_TEXT` means pick a value or type a new one; `SELECTION_ONLY` means it must
  be one of `aspectValues[].localizedValue`.
- `itemToAspectCardinality`: `SINGLE` or `MULTI` (up to 30 values).
- Also returned: `aspectDataType` (DATE, NUMBER, STRING, STRING_ARRAY), `aspectFormat`,
  `aspectMaxLength` (instance aspects only), and `expectedRequiredByDate`.

**Conditions:** Metadata API
`GET https://api.ebay.com/sell/metadata/v1/marketplace/EBAY_GB/get_item_condition_policies?filter=categoryIds:{id}`
(up to 50 IDs). It returns `itemConditionRequired` and `itemConditions[].{conditionId,
conditionDescription, conditionHelpText}`. It accepts an application token with `api_scope`.
([Metadata spec](https://developer.ebay.com/develop/api/spec/metadata_api.json))
The same API has `getNegotiatedPricePolicies` (Best Offer support per category),
`getReturnPolicies` and `getListingTypePolicies`.

## 4. Photos

- **UploadSiteHostedPictures:** "deprecated and will be decommissioned on September 30th, 2026.
  Users are recommended to migrate to the createImageFromFile and createImageFromUrl methods of
  the Media API."
  ([reference](https://developer.ebay.com/devzone/xml/docs/reference/ebay/UploadSiteHostedPictures.html))
  It is listed as decommissioned in Q3 2026
  ([newsletter](https://developer.ebay.com/updates/newsletter/q3_2026)).
- **Media API:** `POST https://apim.ebay.com/commerce/media/v1_beta/image/create_image_from_file`
  - multipart/form-data, field `image`, user token with scope `sell.inventory`.
  - Returns 201, a `Location` header containing the image ID, and a body with `imageUrl` and
    `expirationDate`. `GET /image/{image_id}` returns the same data.
  - "Use the retrieved EPS image URL to add the image to a listing through the Inventory API or
    the Trading API" (in `Item.PictureDetails.PictureURL`).
  - Formats: JPG, GIF, PNG, BMP, TIFF, AVIF, HEIC, WEBP.
  - Rate limit: 50 POSTs per 5 seconds per user.
  - Unused images expire; images in an active listing are kept.
  ([Media spec](https://developer.ebay.com/develop/api/spec/media_api.json),
  [Managing images](https://developer.ebay.com/api-docs/sell/static/inventory/managing-image-media.html))
- **Limits:** up to 24 pictures per listing at no cost (12 per variation). Size and dimension
  limits are returned in errors 190201 and 190202. eBay's examples use 12 MB and 15,000 px
  (height + width), but the exact current limits are not stated. At least 500 px on the longest
  side ([AddFixedPriceItem](https://developer.ebay.com/devzone/xml/docs/reference/ebay/AddFixedPriceItem.html)).
  Resize photos to about 1600 px with ImageMagick before upload.
- **Sandbox:** the Media spec lists only production servers (`api.ebay.com`, `apim.ebay.com`).
  Media API Sandbox support is **UNCONFIRMED**. If it isn't available, in Sandbox send an
  https self-hosted URL, or the dummy URL `https://i2.ebayimg.com/abc/M28/dummy.jpg` that eBay
  documents for VerifyAddItem.

## 5. Browse API comparables

Source: [Browse spec](https://developer.ebay.com/develop/api/spec/browse_api.json).

- `GET https://api.ebay.com/buy/browse/v1/item_summary/search` with the header
  `X-EBAY-C-MARKETPLACE-ID: EBAY_GB` (it defaults to EBAY_US if missing) and an application token
  (`api_scope`).
- Parameters:
  - `q`
  - `category_ids` (only one ID per request)
  - `limit` (1–200, default 50)
  - `offset`
  - `sort=price`
  - `filter`, for example
    `buyingOptions:{FIXED_PRICE},conditions:{USED},price:[10..50],priceCurrency:GBP,itemLocationCountry:GB`
- Only FIXED_PRICE listings are returned by default. `price` must be paired with
  `priceCurrency`. `buyingOptions` works best with a leaf category. `conditionIds:{1000|3000}`
  filters exact conditions.
  ([Buy API field filters](https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html))
- **Sandbox:** Sandbox search is documented only with mock data
  ([Browse guide](https://developer.ebay.com/api-docs/buy/static/api-browse.html)). eBay says:
  "We recommend using Production to test searching capabilities and metadata calls."
  ([Sandbox benefits](https://developer.ebay.com/api-docs/static/gs_sandbox-benefits.html))
  Use production for comps.
- Daily call limits (believed to be 5,000/day for Browse) are **UNCONFIRMED**: the limits page
  was blocked. They are irrelevant at this volume.

## 6. OAuth

- **Endpoints**, from eBay's own OAuth client
  ([ebay-oauth-python-client](https://github.com/eBay/ebay-oauth-python-client/blob/master/oauthclient/model/model.py))
  and the API specs:

  | | Production | Sandbox |
  |---|---|---|
  | Consent | `https://auth.ebay.com/oauth2/authorize` | `https://auth.sandbox.ebay.com/oauth2/authorize` |
  | Token | `https://api.ebay.com/identity/v1/oauth2/token` | `https://api.sandbox.ebay.com/identity/v1/oauth2/token` |

- **Application token** (client credentials grant, scope `https://api.ebay.com/oauth/api_scope`)
  covers Taxonomy, Metadata and Browse
  ([Taxonomy](https://developer.ebay.com/develop/api/spec/taxonomy_api.json),
  [Browse](https://developer.ebay.com/develop/api/spec/browse_api.json) specs).
- **User token** (authorization code grant) covers the Trading API (via the IAF header), the
  Account, Media and Feed APIs.
- Scopes (from the specs):
  - `sell.account`: business policies and `optInToProgram`.
  - `sell.inventory`: Media API and Feed uploads.
  - `api_scope`: base scope.
  - Exact scope(s) the Trading API requires: **UNCONFIRMED**. The OAuth-for-Trading page was
    blocked. Request `api_scope sell.inventory sell.account` and test.
  - `sell.fulfillment` and `commerce.taxonomy` are not needed for this app.
- Lifetimes: user access token is 2 hours ("This authorization stays active for two hours but can
  be regenerated using Refresh Token",
  [Feed guide](https://developer.ebay.com/api-docs/sell/static/feed/fx-feeds-overview.html)).
  Refresh token is about 18 months (`refresh_token_expires_in` 47304000 s): **UNCONFIRMED**, the
  OAuth pages were blocked. The application token is believed to also be 2 hours (**UNCONFIRMED**).
- Redirect: the `redirect_uri` is the app's **RuName** for that environment, not a URL. It is
  configured on the developer portal (User Tokens page) with accept and decline URLs. The
  keyset, RuName and test user must all be from the same environment
  ([KB 1881](https://developer.ebay.com/support/knowledge-base/1881)). For a single-user home
  app, the accept URL can be a page that just shows the `code` for pasting, or
  `http://localhost:8000/callback` if eBay allows non-https localhost URLs (**UNCONFIRMED**).
- The Trading API accepts OAuth user tokens through `X-EBAY-API-IAF-TOKEN`
  ([Making a Call](https://developer.ebay.com/devzone/xml/docs/Concepts/MakingACall.html)).

## 7. Business policies, postage, returns, Best Offer

**Business policies** (Account API v1, user token, `sell.account`;
[Account spec](https://developer.ebay.com/api-docs/master/sell/account/openapi/3/sell_account_v1_oas3.json),
[business policies guide](https://developer.ebay.com/api-docs/sell/static/seller-accounts/business-policies.html))

- Opt in: `POST /sell/account/v1/program/opt_in` with
  `{"programType":"SELLING_POLICY_MANAGEMENT"}`. This is required before policies can be
  attached to listings. Processing "can take up to 24-hours"; check with `getOptedInPrograms`.
  Whether it is needed in Sandbox the same way is **UNCONFIRMED**; assume yes and call it in the
  wizard.
- Create policies:
  - `POST /fulfillment_policy/` with `name`, `marketplaceId: EBAY_GB`,
    `categoryTypes:[{name: ALL_EXCLUDING_MOTORS_VEHICLES}]`, `handlingTime{unit:DAY,value}`,
    `localPickup`, and
    `shippingOptions[{optionType: DOMESTIC, costType: FLAT_RATE, shippingServices[{shippingServiceCode, shippingCost{value,currency}, freeShipping, sortOrder}]}]`.
  - `POST /return_policy` with `returnsAccepted` (false = no returns). When true, add
    `returnPeriod{unit:DAY,value:30}` and `returnShippingCostPayer` BUYER or SELLER.
  - `POST /payment_policy` with `immediatePay: true`. eBay manages electronic payment methods.
- Each create returns the policy ID. Read existing ones with
  `GET /fulfillment_policy?marketplace_id=EBAY_GB` and the matching return and payment calls.
- Plan: about 3 fulfillment policies (2 postage presets + collection only), 2 return policies
  (none, 30 days), 1 payment policy.

**UK shipping service codes**

- Get the authoritative list with Metadata
  `GET /sell/metadata/v1/shipping/marketplace/EBAY_GB/get_shipping_services`. It uses `api_scope`
  and returns `shippingService`, `description`, `shippingCarrier`, `shippingCategory`,
  `min/maxShippingTime`, `packageLimits`, `validForSellingFlow`. Use only services with
  `validForSellingFlow: true`.
  ([Metadata spec](https://developer.ebay.com/develop/api/spec/metadata_api.json))
  It replaces `GeteBayDetails` (`ShippingServiceDetails`), which is decommissioned on 2027-03-15
  ([GeteBayDetails](https://developer.ebay.com/devzone/xml/docs/reference/ebay/GeteBayDetails.html)).
- Codes in the Trading enum
  ([ShippingServiceCodeType](https://developer.ebay.com/devzone/xml/docs/reference/ebay/types/ShippingServiceCodeType.html),
  which says not to rely on its completeness):
  - `UK_RoyalMailSecondClassStandard` (Royal Mail 2nd Class)
  - `UK_RoyalMailFirstClassStandard` (1st Class)
  - `UK_RoyalMailTracked` (**Royal Mail Tracked 48**)
  - `UK_RoyalMailSpecialDeliveryNextDay`
  - `UK_OtherCourier48`, `UK_myHermesDoorToDoorService`
  - `UK_CollectInPerson` (Collection in Person)
- There is no `UK_RoyalMailTracked48` code. Whether each code is still valid for selling must be
  checked with `getShippingServices`.

**Collection only:** fulfillment policy `localPickup: true` ("the buyer and seller make
arrangements for pickup time and location"). The exact form for a collection-only policy
(`localPickup` with no shipping options, or with a `UK_CollectInPerson` service) is
**UNCONFIRMED**; test it with Verify in Sandbox.

**Returns:** `returnsAccepted: false` for no returns, or `true` with 30 days. Most categories
support 30 and 60 days; check per category with Metadata `getReturnPolicies`
([Account spec](https://developer.ebay.com/api-docs/master/sell/account/openapi/3/sell_account_v1_oas3.json)).

**Best Offer (Trading):** set `Item.BestOfferDetails.BestOfferEnabled=true`, and optionally
`Item.ListingDetails.MinimumBestOfferPrice` (auto-decline below this) and
`Item.ListingDetails.BestOfferAutoAcceptPrice`. Best Offer must be enabled for these thresholds
to apply, and the category must support it (Metadata `getNegotiatedPricePolicies`). Changing
`StartPrice` in a revision drops both thresholds.
([AddFixedPriceItem](https://developer.ebay.com/devzone/xml/docs/reference/ebay/AddFixedPriceItem.html))

## 8. Sandbox

- **Test users:** log in to the developer portal and open Sandbox user registration. User names
  get a `TESTUSER_` prefix. Test users get play money that is topped up weekly
  ([Configuring Sandbox test users](https://developer.ebay.com/api-docs/static/sandbox-test-users.html)).
  Sandbox credentials work only in Sandbox
  ([KB 1881](https://developer.ebay.com/support/knowledge-base/1881)).
- **Endpoints:**
  - Trading: `https://api.sandbox.ebay.com/ws/api.dll`
  - REST: `https://api.sandbox.ebay.com/...`
  - OAuth consent: `https://auth.sandbox.ebay.com/oauth2/authorize`
  - Legacy sign-in: `https://signin.sandbox.ebay.com/...`
  ([Making a Call](https://developer.ebay.com/devzone/xml/docs/Concepts/MakingACall.html),
  [KB 1881](https://developer.ebay.com/support/knowledge-base/1881),
  [eBay OAuth client](https://github.com/eBay/ebay-oauth-python-client/blob/master/oauthclient/model/model.py))
- **Limitations relevant here**
  ([KB 684, unsupported features](https://developer.ebay.com/support/knowledge-base/684),
  updated 2024-12):
  - Fees in Sandbox are not guaranteed to match production.
  - "Mobile apps and Mobile Web is not supported on Sandbox".
  - Gallery images and thumbnails are unreliable.
  - ConditionDescription is not shown on View Item.
  - Many catalog product IDs are missing.
  - The Sandbox is not for heavy testing.
- Sandbox doesn't support `getCategorySuggestions`, has only mock Browse data, and has no Seller
  Hub Feed uploads (see above). Media API support is UNCONFIRMED.
- Category IDs and aspects in the Sandbox may differ from production (**UNCONFIRMED**). Any
  Sandbox listing must use categories that exist in Sandbox, so verify a hard-coded test
  category there.
