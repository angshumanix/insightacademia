# Product register and readiness

Each product record has a unique `id` and URL-safe `slug`, a `status` (`demo`, `draft`, `ready`), a category ID from `site.json`, title, summary, description, audience, contents array, formats array, page count, decimal price string, three-letter currency, version, ISO update date, cover style, public preview path and alternative text.

`cover` is one of `case`, `research`, `revision`: these are colour treatments, not content restrictions. Add a new token to validation and CSS when a new treatment is useful. Preview assets live in `assets/`; paths cannot traverse outside it.

The four `readiness` approvals are `fileVerified`, `rightsApproved`, `previewApproved`, `priceApproved`. All must be true for `ready`. Demo codes, demo version names and `assets/sample-*` previews are rejected for ready products. Never promote a demo record by simply flipping its status. Create and inspect the real resource first, then supply its real specifications and preview.

Example workflow:

1. Duplicate a record as an internal `draft`; assign a real SKU and descriptive slug.
2. Create and review the pack privately. Confirm contents, actual page/file counts, editable-file behavior, rights and licensing.
3. Export an intentionally public preview with no private information. Add it under `assets/` and describe it in `previewAlt`.
4. Approve the listed price, currency, version and all readiness fields. Set `status` to `ready` and rebuild.
5. Inspect the generated card, category and product page; confirm the Telegram code identifies the intended pack.

The builder generates full static HTML, not client-fetched product content. Product/Offer schema is generated only for ready products. It describes the listed product, not an automated checkout. Rich-result eligibility and output must be checked before release. Demo products are excluded from the sitemap and use no Product/Offer markup.

No external paid-file URL, attachment or payment endpoint belongs in the product register. Only approved public previews should be committed. File delivery remains manual on Telegram.

Categories with no approved products show an honest empty state. Search/filter controls are added only when cards exist, and are revealed only when JavaScript is running. Empty and filtered-empty states are separate.
