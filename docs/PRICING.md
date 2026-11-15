# Flexible suggested pricing

Every product has `suggestedLower` and `suggestedUpper` decimal strings, `currency: "USD"` and an integer `pricingBand` (1–7). The range is displayed as `USD 10.00–30.00` with **Pay what you think is fair**. Amounts may be discussed outside the displayed range. The final purchase amount is agreed manually on Telegram before a PayPal link is sent. There is no website transaction amount field, enforcement, slider or checkout.

`data/pricing-bands.json` stores the approved internal architecture:

| ID | Internal name | Suggested USD range |
| --- | --- | --- |
| 1 | Entry | 10–99.99 |
| 2 | Standard | 100–199.99 |
| 3 | Professional | 200–349.99 |
| 4 | Advanced | 350–549.99 |
| 5 | Premium | 550–899.99 |
| 6 | Comprehensive | 900–1,499.99 |
| 7 | Complete Collection | 1,500–2,499.99 |

Classification is selected during review and is not calculated from historic transactions. The product's own guidance is chosen for its contents, depth and value. Bands do not determine its range or a customer's final amount. Products remain organized by learning category; band names and a seven-tier table are not rendered on the storefront.

The approved bands were informed by historical payment amounts. No historical payment is represented as a verified study-pack sale. The site contains no transaction history or sales claims. These are purchases of downloadable products, not donations.

Old `price` fields are rejected. Suggested values must be positive finite amounts, with at most two decimal places and lower ≤ upper. Only USD is accepted. These are validation rules for the guidance data, not enforced bounds on the amount discussed with a customer. Band identifiers, category identifiers and range fields are validated independently.

`priceApproved` remains the required human approval flag for the product's suggested range. The existing file/rights/preview approvals and seller/policy release gate remain in force. All demonstrations use modest illustrative ranges and remain unavailable.

Structured data describes real ready products without `Offer`, `AggregateOffer`, `price`, `lowPrice` or `highPrice`. A suggested range is not a set of firm offers. Product rich-result eligibility is not promised; it may be limited without an offer or genuine reviews. Demo pages contain no Product or Offer markup and are excluded from the sitemap.
