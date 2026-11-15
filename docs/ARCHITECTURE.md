# Design and architecture

## Visual direction

Pine green (`#123e32`), ivory (`#f7f5ef`), restrained gold (`#c0a05a` for decoration, darker `#755b24` for light-surface text), Georgia headings and system body text. The temporary wordmark and small typographic `ia.` mark require no external font or image service and can be replaced in the shared page template. The homepage’s illustrative covers are CSS-native artwork, not claims of finished stock.

The homepage uses a compact introduction, four learning categories, product/empty-state section, the three-step ordering explanation and Telegram contact. Card artwork is distinct from the actual product preview. All demonstration specifications and prices are labelled explicitly.

## Architecture

Source data + shared templates → Python standard-library build → static HTML/CSS/JS/assets.

The script does not run on the hosting platform at request time. JSON is not fetched by the browser. Each product has full static text, navigation and SEO metadata. Repeated navigation, footers and detail layouts live in templates. Catalogue cards are composed by one shared builder function. Filtering is optional progressive enhancement.

## Accessibility decisions

- Main landmark, skip link, unique IDs, meaningful heading hierarchy and descriptive image alternatives.
- Inline mobile navigation disclosure, not a modal overlay. It uses natural tab order, accurate expanded state, close action and Escape/focus return. No focus trap is needed for this nonmodal disclosure.
- Navigation stays visible without JavaScript; native details/summary FAQs work independently.
- Search results use a live status and a separate zero-result state. Labels accompany search and category inputs.
- Focus outlines, contrast-tested primary text combinations, reduced-motion handling and responsive CSS at 1050/900/680/360px.
- Core body text is 16px; decorative cover typography is hidden from assistive technology because the same title is provided outside it.

Responsive rules are implemented but require real browser visual verification; automated source/behavior checks are not represented as a layout pass.

## SEO and privacy

Unique titles/descriptions, canonical links, social metadata, a local 1200×630 share image, Organization/WebSite/BreadcrumbList JSON-LD and conditional ready-product Product/Offer markup. Preview/demo pages are noindex and demos are excluded from the sitemap. The default staging build is noindex; approved release output becomes indexable.

The official Telegram URL is directly in HTML. There are no forms, external fonts, tracker libraries, payment scripts or browser storage. A restrictive meta CSP limits resources to local assets and blocks form submission/network connections. Response-header hardening should be reviewed with the eventual host; no unsupported GitHub response-header configuration is claimed.

`services.html` is a noindex legacy bridge with a canonical to the catalogue and a visible destination link. It is not claimed to be an HTTP 301. A future host may support a true redirect separately.

## Preview modes

The default build is safe staging with no demo products. `--preview` creates a separate noindex review with demo records. `scripts/preview.py` packages those generated pages into one offline review document, including the same CSS, script and embedded approved demo assets. Its wrapper allows local navigation and desktop/mobile frame widths. The review-only packaging replaces the page CSP to inline assets; it does not change the site's deployment files.

No build command deploys. No paid files are committed. Site approval, product readiness and hosting approval are independent decisions.
