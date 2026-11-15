# Demonstration-only public architecture

The existing green/gold/ivory design and static templates are preserved. Public generation reads only data/demonstrations.json and produces LearningResource metadata, demonstration cards/details, category pages, sample PDFs and information/policy pages. No Product/Offer, public pricing, checkout, full-product listing or full commercial file is generated.

Full-product model/pricing validation helpers are retained independently for future private workflows. The repository is public; its artificial historical examples must never be replaced with confidential inventory or purchase records. Public export copies an explicit list of branding and referenced demonstration assets rather than the entire asset directory.

The default site and review preview are noindex. Release requires explicit seller details, policies, library content and deployment approvals plus per-sample approval, not full-product stock. A release build makes no hosting, DNS or deployment change.

Navigation is an inline disclosure with accurate expanded state and Escape/focus return. Core pages, links and native FAQs work without JavaScript; filters are progressive enhancement. Skip link/main landmarks, alt text, focus outlines, reduced motion and responsive CSS remain. Rendered browser QA is tracked separately from automated source/behavior checks.

Privacy: no tracker, enquiry form, account system, external font or customer database. Telegram and PayPal data processing are distinguished in the privacy draft. Recordkeeping instructions are in PURCHASE_RECORDS.md; no records are included. A meta CSP restricts page resources and form/network behavior; actual response-header policy depends on the selected host.

The old services.html and how-to-order.html URLs are retained for compatibility with clear demonstration/how-it-works wording. No false HTTP 301 claim is made. No claim is made that this architecture resolves the current host's commercial-use restrictions.
