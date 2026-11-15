# Phase 2 pricing revision and final technical review — 15 November 2026

## Current implementation

The existing redesign is preserved: 15 safe staging pages, four learning categories, reusable product templates, exact Telegram contact URLs, manual PayPal-link ordering, three policy drafts and no real available inventory. The separate 18-page review includes three clearly labelled demonstrations.

Flexible suggested USD ranges now replace fixed product prices everywhere. Each card/detail page displays “Pay what you think is fair.” Catalogue, ordering and FAQ explain that neither end of the range is compulsory and the final commercial purchase amount is agreed through Telegram before the PayPal link. All seven approved bands are supported internally; learning categories remain the browsing structure. Demonstrations use modest sample ranges. No historical payments or study-pack sales claims are published.

Ready-product schema contains Product identity/description only, without Offer or AggregateOffer prices. Demo pages have no Product/Offer markup and are excluded from the sitemap. Default staging remains noindex. Existing readiness approvals and the seller/policy/real-product release gate remain intact.

## Automated results: passed

- Nine Python contract tests, including all previous safeguards plus exact seven-band values, every band identifier, invalid/nonfinite/reversed/overprecise range rejection, USD-only data, obsolete fixed-price rejection, formatted range displays, visible pricing philosophy and schema omission.
- Generated staging/demo pages checked for local file/fragment links, exact Telegram destinations, metadata, headings/main landmark, image alt attributes, duplicate IDs and obsolete channels/content.
- Approved-product release fixture verifies future real-product generation without firm-price Offer markup. Actual demo inventory remains unavailable.
- JavaScript syntax and menu/filter unit checks pass: expanded state, Escape/focus return, outside-click close, breakpoint transitions, search/category/reset and empty results.
- Source-defined primary text colour combinations pass contrast calculations; this is not a full rendered contrast audit.
- Deterministic generation and stale-page cleanup pass. `git diff --check` passes. The offline review wrapper and embedded page scripts pass syntax checks.

## Genuine browser attempt: blocked before page load

The local Playwright package is available. Its bundled Chromium executable was missing; the attempted browser download failed. The alternative installed `/usr/bin/chromium` then failed to launch with:

`Check failed: . socket() failed: Operation not permitted (1)`

No page opened in Chromium. No layout, overflow, keyboard, JavaScript-disabled, preview rendering or Lighthouse result is claimed to have passed. No browser screenshots were fabricated. Earlier remote browsers could not reach this workspace's local HTTP server, so that failed route was not repeatedly retried.

`tests/browser.cjs` contains the reproducible suite for a working local QA environment. It targets homepage, catalogue, product detail, FAQ, contact and ordering pages at 1440/768/390/320px; also filtering/zero results, menu close/Escape, keyboard skip link, native FAQ, preview-image decoding, Telegram destinations and JavaScript-disabled browsing. Browser/server cleanup is included even on launch failure.

## Usable visual review

Run `python scripts/preview.py` and open `.preview/InsightAcademia_Design_Preview.html`. It packages the actual generated pages and assets, supports internal page navigation, and provides desktop, 768px, 390px and 320px frame controls. Frames are limited by the width of the window in which the review is opened. This is an inspectable preview, not proof of browser QA. No deployed preview or live-domain change is required.

## Remaining technical work before merge

Run the real-browser suite in an environment that permits Chromium and local sockets; visually inspect all four widths, long USD ranges, image readability, focus visibility, 200% zoom and no-JavaScript navigation. Run Lighthouse/axe and structured-data validation on the eventual approved export. No functional source/test failure is currently known, but rendered layout and performance remain unverified.

## Readiness and approvals

The data/template framework is ready for integration of separately created and approved real packs. It is not approved for launch. Confirm actual contents/files/rights, public preview extracts, product-specific suggested ranges and licences; finalize seller identity, order-record retention, delivery timing, refund/cancellation and update terms; approve the final logo/design; resolve commercially suitable hosting. Obtain explicit approval before merging or deployment.

PR #1 uses the existing phase-2-storefront branch. Main, CNAME, Pages settings, DNS and hosting remain unchanged. No paid files, checkout, customer accounts, trackers, external fonts or runtime backend have been introduced. Playwright is optional QA tooling, not a website dependency.
