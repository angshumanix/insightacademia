# InsightAcademia

A lightweight static study-pack catalogue. HTML, CSS and a small progressive-enhancement script are the only browser dependencies. Python 3.9+ generates repeated pages from shared templates and JSON data using the standard library; no packages or subscriptions are required.

## Development status

This is Phase 2 development work. Do not merge or deploy without the owner's explicit approval. The original implementation remains in Git history at `2e5d05697a2a1e4ee1aa2e9afe02b093d021564c`. CNAME and the live Pages configuration have not been changed.

The default generated site is an unlaunched staging collection with **zero available products**, `noindex` metadata and policy drafts. The three product records are demonstrations, not real stock. Demo detail pages appear only in a separately generated preview. No paid downloads belong in this public repository.

## Build and preview

```sh
python scripts/build.py
python scripts/build.py --preview --out .preview
python -m http.server 8765
```

Open `http://localhost:8765/` for staging, or `http://localhost:8765/.preview/` for the labelled design preview. Both outputs work as static files. Local search and navigation enhancements require JavaScript; core links, product information, contact URLs and native FAQs work without it. Run a local server for realistic CSP testing.

For a portable offline review with page navigation and desktop/mobile frame controls, run `python scripts/preview.py` and open `.preview/InsightAcademia_Design_Preview.html`. This is a review document, not a deployment export.

Never serve the repository directory itself publicly: it contains source, configuration and documentation. Serve only a reviewed static export folder. `.preview` is ignored by Git.

## Editing

- `data/site.json`: brand, official Telegram URL, learning categories, seller identity and policy approval flag.
- `data/products.json`: product register; see `docs/PRODUCTS.md`.
- `templates/page.html`: shared document head, navigation and footer.
- `templates/product.html`: reusable product-page layout.
- `scripts/build.py`: content composition, validation and page generation.
- `css/style.css`: green/gold/ivory design, responsive layouts and accessible states.
- `js/main.js`: inline mobile-navigation disclosure and catalogue filters.
- `assets/`: intentionally public branding and preview assets only.

Edit the source and regenerate; do not hand-edit generated HTML. `.generated-pages.json` tracks generated pages so retired pages are removed on the next build. Existing non-generated files are preserved. Use one output directory per build mode.

## Verification

```sh
python -m unittest discover -s tests -p 'test_*.py'
node --check js/main.js
node tests/interactions.cjs
```

These checks cover page contracts, links, Telegram destinations, metadata, demo exclusion, publication safeguards, colour combinations and script behavior. They do not replace real browser layout, keyboard and assistive-technology review. Record results and remaining limitations in `docs/REVIEW.md`.

## Before any release

1. Resolve the hosting choice; GitHub Pages' commercial-use restrictions remain relevant. No host migration is implemented.
2. Approve the seller identity, policies, actual products, rights, preview extracts, prices and delivery process.
3. Replace demonstration records with real product records and approved public preview extracts; retain paid files privately for manual Telegram delivery.
4. Set `sellerName` and `policiesApproved` only after approval, and update the policy prose to match the decisions. This flag does not rewrite policy text.
5. Run `python scripts/build.py --release --out .preview/release`. This generates an indexable static export only; it does not publish anything. It fails until seller/policy approval and at least one ready product exist.
6. Complete browser QA on the release export, confirm canonical origin, validate structured data and obtain explicit deployment approval.

All customer contact links must remain exactly `https://t.me/InsightAcademiaPacks`. PayPal links and files are sent manually through Telegram. No transaction or customer data is stored by this site.
