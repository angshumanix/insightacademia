# Hosting decision — separate from development

No hosting resource, domain, DNS record, subscription, Pages setting or deployment has been changed. The existing CNAME file is preserved. This branch is not approved for production deployment.

The build is portable static HTML/CSS/JS/assets. Two Cloudflare candidates can serve this architecture without a runtime database or application backend:

| Candidate | Relevant current documentation | Assessment |
| --- | --- | --- |
| Workers Static Assets | Static-asset requests are free and unlimited, with no additional asset-storage cost. Worker execution has separate pricing/limits. | A suitable technical candidate for a static-only export; no Worker-first routing is needed for this catalogue. |
| Cloudflare Pages | Free plan documentation lists 500 builds/month and one concurrent build. | A straightforward static-export candidate; repository integration and preview controls would need separate review. |

Checked 15 November 2026 against official documentation:

- https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/
- https://developers.cloudflare.com/pages/platform/limits/

These are technical/cost observations, not a completed contractual clearance. Before selecting a host, confirm commercial-use terms for the seller and products, limits, canonical URL/path behavior, custom-domain configuration, privacy/logging and preview access. The current GitHub Pages commercial-use conflict remains unresolved; external payment does not itself resolve it.

There is no deployment configuration or automatic deployment workflow in this development change. Host selection and any migration require the owner's explicit approval.
