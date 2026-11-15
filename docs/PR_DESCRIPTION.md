# Add flexible suggested pricing to the study-pack framework

The existing static storefront now supports product-specific suggested USD ranges with “Pay what you think is fair.” The guidance has no compulsory minimum or maximum; the purchase amount is agreed manually on Telegram before a PayPal link is sent. Seven approved bands classify products internally without replacing the learning categories or forcing expensive prices.

Updated product data, validation, cards, detail templates, ordering/FAQ/policy copy and maintenance guidance. Product structured data omits price-bearing Offer/AggregateOffer markup. Existing demo exclusion, noindex and release approvals remain intact; no real inventory is advertised as available.

Validation: nine Python tests, JavaScript syntax/menu/filter behavior checks and offline preview script syntax pass. Genuine Playwright testing was attempted but Chromium failed before opening a page because local socket creation is denied. The reproducible browser suite and updated desktop/768/390/320px offline preview are provided; visual/end-to-end QA remains pending. See docs/REVIEW.md.

Keep this PR in draft. Before merge/launch: complete browser QA, integrate approved real products, finalize seller/policy/licence decisions and choose hosting. Main, live domain, Pages settings and DNS remain unchanged. No deployment or merge is authorized.
