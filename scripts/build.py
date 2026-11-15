#!/usr/bin/env python3
"""Dependency-free static catalogue. Default: safe, unlaunched staging build."""
import argparse
import html
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TG = 'https://t.me/InsightAcademiaPacks'

def esc(value):
    return html.escape(str(value), quote=True)

def validate(site, products):
    if site['telegram'] != TG:
        raise ValueError('The official Telegram URL must be used exactly.')
    category_ids=[c['id'] for c in site['categories']]
    if not category_ids or len(category_ids)!=len(set(category_ids)) or not all(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', c) for c in category_ids):
        raise ValueError('Category IDs must be unique, safe URL slugs.')
    bands = json.loads((ROOT/'data/pricing-bands.json').read_text())
    if [b['id'] for b in bands] != list(range(1, 8)):
        raise ValueError('Exactly seven ordered internal pricing bands are required.')
    for band in bands:
        if band['currency'] != 'USD' or Decimal(band['suggestedLower']) > Decimal(band['suggestedUpper']):
            raise ValueError('Invalid internal pricing band.')
    categories = {c['id'] for c in site['categories']}
    ids, slugs = set(), set()
    for p in products:
        if p['id'] in ids or p['slug'] in slugs:
            raise ValueError('Product IDs and slugs must be unique.')
        ids.add(p['id']); slugs.add(p['slug'])
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', p['slug']):
            raise ValueError('Unsafe product slug.')
        if p['status'] not in {'demo', 'draft', 'ready'} or p['category'] not in categories:
            raise ValueError('Invalid product status or category.')
        if 'price' in p:
            raise ValueError('Fixed price is obsolete; use suggestedLower and suggestedUpper.')
        try:
            lower, upper = (Decimal(p[key]) for key in ('suggestedLower', 'suggestedUpper'))
            if any(not value.is_finite() or value <= 0 or value.as_tuple().exponent < -2 for value in (lower, upper)) or lower > upper:
                raise ValueError('Suggested prices must be positive, ordered amounts with at most two decimals.')
        except (InvalidOperation, KeyError, TypeError) as exc:
            raise ValueError('Invalid suggested price range.') from exc
        if p['currency'] != 'USD':
            raise ValueError('Suggested ranges must be in USD.')
        if type(p.get('pricingBand')) is not int or p['pricingBand'] not in range(1, 8):
            raise ValueError('Select an internal pricing band from 1 to 7.')
        date.fromisoformat(p['updated'])
        if not isinstance(p['pages'], int) or p['pages'] < 1 or not p['formats'] or not p['contents']:
            raise ValueError('Products require page count, formats and contents.')
        if p['cover'] not in {'case', 'research', 'revision'}:
            raise ValueError('Unknown cover style.')
        for field in ['title','summary','description','audience','version','previewAlt']:
            if not isinstance(p[field], str) or not p[field].strip():
                raise ValueError(f'Missing product field: {field}')
        sample = Path(p['preview'])
        if sample.is_absolute() or '..' in sample.parts or sample.parts[0] != 'assets' or not (ROOT/sample).is_file():
            raise ValueError('Preview must be an existing public asset under assets/.')
        if p['status'] == 'ready' and not all(p['readiness'].get(k) is True for k in ('fileVerified','rightsApproved','previewApproved','priceApproved')):
            raise ValueError(f"{p['id']}: all readiness approvals are required.")
        if p['status'] == 'ready' and (p['id'].startswith('DEMO') or p['version'].lower() == 'demo' or p['preview'].startswith('assets/sample-')):
            raise ValueError('Demo identity and sample assets cannot be published as ready products.')

def price_range(product):
    return f"USD {Decimal(product['suggestedLower']):,.2f}–{Decimal(product['suggestedUpper']):,.2f}"

PRICING_MESSAGE = 'Pay what you think is fair'
PRICING_EXPLANATION = "We believe useful learning resources should remain accessible. Each pack has a suggested USD range to help you decide. The range is guidance, not a compulsory minimum or maximum. Get in touch on Telegram to discuss an amount that feels fair and comfortable for your budget. We agree the final purchase amount before sending your PayPal payment link."

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--preview', action='store_true', help='Build offline review output; always noindex.')
    mode.add_argument('--release', action='store_true', help='Indexable demonstration output; requires all approvals. Does not deploy.')
    parser.add_argument('--out', default='.', help='Output directory relative to repository root.')
    args = parser.parse_args(argv)
    site = json.loads((ROOT/'data/site.json').read_text())
    # Full-product records are never inputs to public generation.
    products = json.loads((ROOT/'data/demonstrations.json').read_text())
    categories_set = {c['id'] for c in site['categories']}
    seen_ids, seen_slugs = set(), set()
    for demo in products:
        if demo['status'] != 'demo' or demo['category'] not in categories_set or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', demo['slug']):
            raise ValueError('Public catalogue accepts safe demonstration records only.')
        if demo['id'] in seen_ids or demo['slug'] in seen_slugs:
            raise ValueError('Demonstration IDs and slugs must be unique.')
        seen_ids.add(demo['id']); seen_slugs.add(demo['slug'])
        if any(k in demo for k in ('price','suggestedLower','suggestedUpper','pricingBand')):
            raise ValueError('Public demonstrations cannot contain commercial pricing fields.')
        for key in ('preview','samplePdf'):
            asset=Path(demo[key])
            if asset.is_absolute() or '..' in asset.parts or not asset.parts or asset.parts[0] != 'assets' or not (ROOT/asset).is_file():
                raise ValueError('Demonstrations require local public sample assets.')
    if args.release and (not site['sellerName'].strip() or not all(site.get(k) is True for k in ('sellerDetailsApproved','policiesApproved','demonstrationsApproved','deploymentApproved')) or not products or not all(d.get('approved') is True for d in products)):
        parser.error('Release blocked: approve seller details, policies, each demonstration, demonstration library and deployment arrangements first.')
    output = (ROOT/args.out).resolve()
    if not output.is_relative_to(ROOT) or output == ROOT/'.git' or '.git' in output.relative_to(ROOT).parts:
        parser.error('Output must stay inside the repository and outside .git.')
    output.mkdir(parents=True, exist_ok=True)
    if output != ROOT:
        import shutil
        for folder in ['css', 'js']:
            shutil.copytree(ROOT/folder, output/folder, dirs_exist_ok=True)
        public_assets={'assets/favicon.svg','assets/logo-dark.svg','assets/logo-light.svg','assets/emblem.svg','assets/social-card.png'}
        public_assets.update(d[k] for d in products for k in ('preview','samplePdf'))
        for asset in public_assets:
            target=output/asset;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/asset,target)
    visible = products
    cats = {c['id']:c for c in site['categories']}
    layout = Template((ROOT/'templates/page.html').read_text())
    product_layout = Template((ROOT/'templates/product.html').read_text())
    written, sitemap = set(), []
    robots = 'index, follow' if args.release else 'noindex, nofollow'
    def href(path, prefix): return f'{prefix}/{path}'
    def telegram(label='Get in touch on Telegram', extra=''):
        return f'<a class="button {extra}" href="{TG}">{esc(label)} <span aria-hidden="true">↗</span></a>'
    def process(prefix):
        steps = [('Explore a demonstration','Browse an educational sample, read a worksheet and download the sample PDF.'),('Get in touch on Telegram','Ask about full-pack availability, contents, formats, compatibility, pricing, updates and licence terms.'),('Discuss the details privately','If an available full pack suits your needs, we agree the purchase terms through Telegram. Any payment link and file delivery are handled privately.')]
        return '<div class="process-grid">'+''.join(f'<div class="process-step"><span>0{i}</span><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for i,(t,d) in enumerate(steps,1))+'</div>'
    def empty(prefix, category=False):
        return f'<div class="empty-state"><p class="eyebrow">The collection is taking shape</p><h2>{"New resources are being prepared." if category else "Good learning starts with a clear resource."}</h2><p>Our first study packs are being developed. New approved educational demonstrations will appear here.</p>{telegram()}<p class="fine-print">Follow up with us on Telegram for collection updates.</p></div>'
    def cards(items, prefix):
        if not items: return empty(prefix)
        result = '<div class="product-grid">'
        for p in items:
            demo = p['status'] == 'demo'
            url = href('packs/'+p['slug']+'.html',prefix)
            result += f'''<article class="product-card" data-product data-category="{esc(p['category'])}"><a href="{url}" class="card-art" aria-label="View {esc(p['title'])} demonstration"><div class="book book-{esc(p['cover'])}" aria-hidden="true"><span class="book-brand">INSIGHTACADEMIA</span><div class="book-lines"></div><span class="book-kicker">EDUCATIONAL SAMPLE</span><span class="book-title">{esc(p['title'])}</span><span class="book-foot">Demonstration material</span></div></a><div class="card-body"><p class="eyebrow">{esc(cats[p['category']]['name'])}</p><h3><a href="{url}">{esc(p['title'])}</a></h3><p>{esc(p['summary'])}</p><p class="card-status">Demonstration material — not a complete commercial study pack.</p><div class="card-bottom"><span class="fine-print">Sample {esc(p['id'])}</span><a class="text-link" href="{url}">Explore sample →</a></div></div></article>'''
        return result+'</div>'
    def categories(prefix):
        return '<div class="category-grid">'+''.join(f'<a class="category-card" href="{href("categories/"+c["id"]+".html",prefix)}"><span class="category-number">{esc(c["number"])}</span><h3>{esc(c["name"])}</h3><p>{esc(c["description"])}</p><span class="category-link">Explore category <span aria-hidden="true">↗</span></span></a>' for c in site['categories'])+'</div>'
    def page(path, title, description, body, active='', schema=None, canonical_path=None, exclude=False):
        prefix = '..' if '/' in path else '.'
        canonical_path = canonical_path or path
        canonical = site['url'] + ('/' if canonical_path == 'index.html' else '/'+canonical_path)
        nav = ''.join(f'<a href="{href(p,prefix)}"'+(' aria-current="page"' if active==label else '')+f'>{label}</a>' for label,p in [('Demonstrations','study-packs.html'),('How it works','how-to-order.html'),('About','about.html')])
        if args.preview:
            notice='<div class="dev-notice"><strong>Design preview.</strong> Educational demonstrations only. Full packs are not listed or delivered on this website.</div>'
        elif not args.release:
            notice='<div class="dev-notice"><strong>Development review.</strong> Demonstration library and policy drafts await final approval.</div>'
        else: notice=''
        base_schema=[{'@type':'Organization','@id':site['url']+'/#organization','name':site['name'],'url':site['url']+'/','sameAs':[TG]}]
        if path=='index.html':base_schema.append({'@type':'WebSite','name':site['name'],'url':site['url']+'/'})
        else:
            crumbs=[{'@type':'ListItem','position':1,'name':'Home','item':site['url']+'/'}]
            if path.startswith(('packs/','categories/')):crumbs.append({'@type':'ListItem','position':2,'name':'Study packs','item':site['url']+'/study-packs.html'})
            crumbs.append({'@type':'ListItem','position':len(crumbs)+1,'name':title,'item':canonical})
            base_schema.append({'@type':'BreadcrumbList','itemListElement':crumbs})
        if schema:base_schema.append(schema)
        jsonld=json.dumps({'@context':'https://schema.org','@graph':base_schema},ensure_ascii=False).replace('<','\\u003c')
        doc=layout.substitute(title=esc(title+' | InsightAcademia'), description=esc(description), robots=('noindex, follow' if exclude else robots), canonical=esc(canonical), social_image=esc(site['url']+'/assets/social-card.png'), og_type='website', prefix=prefix, schema=jsonld, notice=notice, nav=nav, telegram=TG, body=body)
        target=(output/path).resolve()
        if not target.is_relative_to(output):raise ValueError('Generated path must stay inside output.')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(doc)
        written.add(path)
        if not exclude:
            sitemap.append(canonical)
    def hero(eyebrow,title,desc):
        return f'<section class="page-hero"><div class="container"><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1><p class="lead">{esc(desc)}</p></div></section>'
    art='''<div class="hero-art" role="img" aria-label="Illustrative green and ivory study-pack covers"><div class="book book-back" aria-hidden="true"><span class="book-brand">INSIGHTACADEMIA</span><div class="book-lines"></div><span class="book-kicker">THE STUDY COLLECTION</span><span class="book-title">A clearer way to learn.</span><span class="book-foot">REFERENCE · REFLECT · UNDERSTAND</span></div><div class="book book-front" aria-hidden="true"><span class="book-brand">INSIGHTACADEMIA</span><div class="book-lines"></div><span class="book-kicker">INDEPENDENT LEARNING</span><span class="book-title">Make room for understanding.</span><span class="book-foot">THE STUDY COLLECTION</span></div><span class="art-caption">Illustrative covers · the study collection</span></div>'''
    label='Demonstration material — not a complete commercial study pack.'
    home=f'''<section class="hero"><div class="container hero-grid"><div><p class="eyebrow">The demonstration library</p><h1>Study with purpose.<br><em>Learn with clarity.</em></h1><p class="lead">Explore educational samples, practical frameworks and worksheets that show how our study resources are structured.</p><div class="actions"><a class="button" href="./study-packs.html">Explore the demonstrations →</a><a class="text-link" href="./how-to-order.html">How it works ↗</a></div><div class="hero-note"><span>Independent learning</span><span>Downloadable educational samples</span></div></div>{art}</div></section><section class="section section-white"><div class="container"><div class="section-heading"><div><p class="eyebrow">Explore the approach</p><h2>A useful starting point.</h2></div><p>Each demonstration includes a teaching example and space to practise. Full commercial packs are developed separately.</p></div>{cards(visible,'.')}</div></section><section class="section"><div class="container"><p class="eyebrow">Learning purposes</p><h2>What are you exploring?</h2>{categories('.')}</div></section><section class="section section-white"><div class="container"><h2>From a first look to a clearer understanding.</h2>{process('.')}</div></section><section class="section"><div class="container dark-panel"><div><p class="eyebrow">A direct conversation</p><h2>Questions are welcome.</h2><p>Ask us about full-pack availability, contents, formats and terms before deciding whether a resource suits your learning.</p></div><div>{telegram()}<p class="fine-print">@InsightAcademiaPacks</p></div></div></section>'''
    page('index.html','Academic study-pack demonstrations','Explore educational demonstration PDFs, example worksheets and learning frameworks from InsightAcademia.',home)
    def catalogue(path,cat=None):
        prefix='..' if '/' in path else '.'
        items=[p for p in visible if not cat or p['category']==cat['id']]
        title=cat['name'] if cat else 'Explore the demonstration library.'
        desc=cat['description'] if cat else 'Educational samples that show the structure and approach of our independent study resources.'
        body=hero('Demonstration study packs',title,desc)+f'<section class="section"><div class="container"><p class="policy-draft">{label}</p>'
        if items:
            options=''.join(f'<option value="{esc(c["id"])}">{esc(c["name"])}</option>' for c in site['categories'] if not cat or cat['id']==c['id'])
            body+=f'<div class="catalogue-tools" data-catalogue-tools data-demo="true" hidden><div class="field"><label for="pack-search">Find a demonstration</label><input id="pack-search" type="search" placeholder="Search by title or topic" autocomplete="off"></div><div class="field"><label for="pack-category">Learning category</label><select id="pack-category"><option value="">All categories</option>{options}</select></div><button class="button button-light" type="button">Clear filters</button></div><p class="results-count" data-result-count role="status" aria-live="polite">{len(items)} educational demonstrations</p>{cards(items,prefix)}<div class="empty-state" data-no-results hidden><h2>No matching demonstrations.</h2><p>Try another topic or clear the filters.</p></div>'
        else:body+=empty(prefix,True)
        body+='</div></section>'
        page(path,'Demonstration study packs' if not cat else title,desc,body,active='Demonstrations')
    catalogue('study-packs.html')
    for cat in site['categories']:catalogue('categories/'+cat['id']+'.html',cat)
    for p in visible:
        values={key:esc(p[key]) for key in ['id','title','summary','description','audience','cover']}
        values.update(prefix='..',telegram=TG,category=esc(cats[p['category']]['name']),pages=p['samplePages'],sample_pdf='../'+p['samplePdf'],contents=''.join(f'<li><span aria-hidden="true">{i:02d}</span>{esc(c)}</li>' for i,c in enumerate(p['contents'],1)),preview=f'<figure class="sample-preview"><img src="../{esc(p["preview"])}" alt="{esc(p["previewAlt"])}" width="900" height="660" loading="lazy"><figcaption>{label}</figcaption></figure>',process=process('..'),related=cards([q for q in visible if q['id']!=p['id']],'..'))
        schema={'@type':'LearningResource','name':p['title'],'description':p['summary'],'learningResourceType':'Educational demonstration','url':site['url']+'/packs/'+p['slug']+'.html','encoding':{'@type':'MediaObject','contentUrl':site['url']+'/'+p['samplePdf'],'encodingFormat':'application/pdf'}}
        page('packs/'+p['slug']+'.html',p['title']+' — demonstration',p['summary'],product_layout.substitute(values),active='Demonstrations',schema=schema)
    works=hero('How it works','Explore. Reflect. Get in touch.','The website is a demonstration library. Full-pack availability and any purchase arrangements are discussed privately through Telegram.')+f'<section class="section"><div class="container">{process(".")}</div></section><section class="section section-white"><div class="container prose"><h2>Clarify the details before payment</h2><p>Ask about contents, formats, device compatibility, updates, licence terms and any other questions. All material information and applicable conditions should be provided before payment.</p><h2>Pay what you think is fair</h2><p>For available full packs, discuss an amount that feels fair and comfortable for your budget through Telegram. We agree the final purchase amount privately before sending a PayPal payment link.</p><h2>Private payment and delivery</h2><p>If you decide to purchase an available full pack, we manually send a PayPal payment link through Telegram. After verifying payment, we manually deliver the files through Telegram. The website does not process payment or deliver full commercial packs.</p>{telegram()}</div></section>'
    page('how-to-order.html','How it works','Explore demonstrations and discuss full study-pack availability and terms privately through Telegram.',works,active='How it works')
    page('about.html','About InsightAcademia','Independent educational samples and thoughtfully structured academic learning resources.',hero('About the library','A little more structure for independent learning.','Our demonstrations show how explanations, frameworks and worksheets can support individual study.')+'<section class="section"><div class="container prose"><h2>Learn through an example</h2><p>A practical example can make an unfamiliar idea easier to approach. Read through the teaching notes, consider the questions and try the worksheet yourself.</p><h2>A sample of the approach</h2><p>The public library contains educational demonstrations. Full study packs are developed separately. Contact InsightAcademia through Telegram to discuss whether an available resource suits your learning needs.</p><h2>Your own understanding</h2><p>Use the materials for independent learning and reference. You are responsible for your use of them and for following your institution’s academic rules.</p></div></section>',active='About')
    page('contact.html','Contact on Telegram','Reach InsightAcademia through the official Telegram account @InsightAcademiaPacks.',hero('Contact InsightAcademia','Get in touch on Telegram.','Questions about a demonstration or a full pack? Ask about availability, contents, formats, compatibility, updates and licence terms.')+f'<section class="section"><div class="container detail-layout"><div class="contact-card"><p class="eyebrow">Our official account</p><h2>Start a conversation.</h2><p class="handle">@InsightAcademiaPacks</p>{telegram()}<p class="fine-print">Include the sample code if you are referring to a demonstration.</p></div><div class="prose"><h2>A considered approach to privacy.</h2><p>Manage phone-number visibility in Telegram’s settings. Ordinary Telegram cloud chats are not end-to-end encrypted; Secret Chats are a separate feature.</p><p>Deleting a conversation does not erase downloaded copies or PayPal transaction records.</p><a class="text-link" href="./privacy.html">Read the privacy policy →</a></div></div></section>')
    faqs=[('What can I explore here?', 'Educational demonstration packs, sample pages and downloadable sample PDFs. Each sample is clearly labelled and is not a complete commercial study pack.'),('How do I enquire about a full pack?', 'Contact @InsightAcademiaPacks on Telegram. Ask about availability, contents, formats, compatibility, pricing and applicable terms before deciding.'),('What does “Pay what you think is fair” mean?', 'Discuss an amount you consider fair and affordable privately through Telegram. Any final purchase amount is agreed before a PayPal payment link is sent.'),('How are full packs delivered?', 'For an agreed private purchase, we send a PayPal link manually through Telegram, verify payment and manually deliver files through Telegram.'),('Can I change my mind after delivery?', 'Purchases of delivered digital study packs are final. We do not provide discretionary change-of-mind refunds after delivery. Applicable statutory rights and payment-provider protections remain unaffected.'),('What updates are included?', 'The original purchaser can request updates released for the specific purchased product during the six months beginning on the confirmed payment date, without additional payment. No particular number or frequency is guaranteed; separately sold or unrelated products are not included.'),('May I share a full pack?', 'Full packs are licensed to the original purchaser for personal educational use. Unauthorized copying, resale, redistribution, uploading and public sharing are prohibited, subject to applicable law. Recipients of unauthorized copies do not receive purchaser benefits or complimentary updates.'),('Are outcomes guaranteed?', 'We do not guarantee grades, examination results, assignment acceptance, university approval, or academic, professional or career outcomes. Students are responsible for appropriate use and institutional compliance.')]
    page('faq.html','Common questions','Questions about demonstrations, private enquiries, updates and use of study materials.',hero('Common questions','A few useful details.','Explore the library and clarify your questions through Telegram.')+'<section class="section"><div class="container faq-list">'+''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q,a in faqs)+'</div></section>')
    draft='<div class="policy-draft"><strong>Policy draft for review.</strong> Seller details and legal wording must be reviewed for the relevant seller and customer jurisdictions before launch.</div>' if not site['policiesApproved'] else ''
    policies={
      'privacy.html':('Privacy policy','Website information, private conversations and purchase records.', '''<h2>Website data</h2><p>This static demonstration library uses no analytics trackers, advertising scripts, enquiry forms, customer accounts, mailing lists, cookies or browser storage in its own code. Fonts and visual assets are local. The hosting provider may process technical request data, including IP addresses and logs, to deliver and secure the site.</p><h2>Telegram and PayPal</h2><p>Telegram is our ordinary customer communication and product-delivery channel. Messages and profile information you share are visible to the receiving account. Telegram processes information under its own policies. Ordinary cloud chats are not end-to-end encrypted; Secret Chats are separate. Phone-number visibility is controlled through Telegram settings.</p><p>Any agreed purchase is handled privately. Payment details are entered on PayPal, which processes them independently and supplies transaction information to the seller. Chat deletion does not erase downloaded files, independent copies or transaction records.</p><h2>Minimal purchase records</h2><p>For private purchases we retain the product identifier and version, confirmed payment date and transaction reference, agreed amount/currency, a minimal contact reference, delivery confirmation, the applicable terms version and the six-month update eligibility dates. Records may also include necessary update requests or dispute information.</p><p>These records are used to verify purchases, supply eligible updates, address payment disputes and meet legal recordkeeping obligations. They are held privately with restricted access, not published in the website repository. We do not request card details or identity documents for routine verification.</p><h2>Retention and privacy requests</h2><p>Before launch, the seller must confirm the applicable retention periods, legal requirements and request-handling procedure. Records required for a legal obligation or an active dispute may need to be retained. Contact the official Telegram account with privacy questions.</p><p>See <a href="https://telegram.org/privacy">Telegram’s privacy policy</a> and <a href="https://www.paypal.com/webapps/mpp/ua/privacy-full">PayPal’s privacy policy</a>.</p>'''),
      'terms.html':('Terms and conditions','Educational use, personal licensing and clear expectations.', '''<h2>Demonstrations and full packs</h2><p>The website presents educational demonstration materials, not full commercial study packs. Full-pack availability, contents, price and applicable conditions are communicated privately through Telegram before payment.</p><h2>Personal educational licence</h2><p>Purchased full packs are licensed to the original purchaser for personal educational study and reference. Unauthorized copying, resale, redistribution, uploading or public sharing is prohibited, subject to applicable law. This licence does not transfer copyright.</p><p>Recipients of unauthorized copies do not receive complimentary updates, official update eligibility or purchaser benefits. Licensing restrictions are terms of use; they are not a claim that technical prevention of copying is possible.</p><h2>Educational responsibility</h2><p>Resources are independent educational materials. No specific grades, examination results, assignment acceptance, university approval, or academic, professional or career outcomes are guaranteed. Students are responsible for their use of the materials and for complying with their institution’s academic rules.</p><h2>Demonstration use</h2><p>Public samples may be downloaded for individual study and reference. Unauthorized resale or redistribution of the samples is prohibited, subject to applicable law. A sample download does not confer full-pack purchaser benefits.</p><h2>Reasonable liability limits</h2><p>To the extent permitted by applicable law, InsightAcademia is not responsible for losses resulting from unauthorized or inappropriate use of the materials, or a user’s failure to follow applicable academic rules. Nothing in these terms excludes or limits liability, remedies or consumer rights that cannot legally be excluded or limited.</p><h2>Seller and jurisdiction</h2><p>Seller identity, contact particulars, governing-law wording and customer-jurisdiction requirements must be finalized and legally reviewed before launch. The digital product policy explains delivery, refunds and six-month update eligibility.</p>'''),
      'digital-products.html':('Digital product policy','Purchase clarifications, delivery, finality and six-month updates.', '''<h2>Clarify before paying</h2><p>Ask on Telegram about contents, formats, device compatibility, updates, licence terms and any uncertainty. Material product information and applicable conditions must be provided before payment. Any purchase amount is agreed privately under our “Pay what you think is fair” approach.</p><h2>Private payment and delivery</h2><p>For an agreed available full pack we manually send a PayPal payment link through Telegram. After confirming payment, we manually deliver the files through Telegram. Expected delivery timing is confirmed before payment.</p><h2>Final purchases and refunds</h2><p>Purchases of delivered digital study packs are final. We do not provide discretionary refunds for changes of mind after delivery. Applicable statutory consumer rights, remedies and payment-provider protections remain unaffected. This policy does not prevent an eligible dispute or chargeback.</p><p>For missing, inaccessible, incorrect or materially misdescribed files, contact us on Telegram with the product code and a minimal transaction reference so the issue can be reviewed and any applicable remedy addressed.</p><h2>Six months of complimentary updates</h2><p>Every purchased full study pack includes six months of complimentary updates, starting on the confirmed payment date. Updates released for that specific purchased product during the eligibility period are available to the original purchaser without additional payment.</p><p>Newly developed, separately sold products and unrelated study packs are not automatically included. No particular number or frequency of updates is guaranteed. Contact us through Telegram to request eligible updates and verify the original purchase.</p><h2>Original purchaser eligibility</h2><p>Purchased materials are licensed for the original purchaser’s personal educational use. Unauthorized recipients do not receive complimentary updates or purchaser benefits. Refer to the terms and conditions for the licence.</p>''')}
    for path,(title,description,body) in policies.items():
        page(path,title,description,hero('The details',title,description)+f'<section class="section"><div class="container prose">{draft}{body}<p>{telegram()}</p></div></section>')
    page('services.html','Demonstration library','Explore educational demonstration study packs.',hero('The library','Explore the demonstrations.','Educational examples and practice worksheets for independent learning.')+'<section class="section"><div class="container"><a class="button" href="./study-packs.html">Explore the library →</a></div></section>',canonical_path='study-packs.html',exclude=True)
    page('404.html','Page not found','Return to the InsightAcademia demonstration library.',hero('Page not found','Let’s find your starting point.','Explore educational demonstrations or contact us through Telegram.')+'<section class="section"><div class="container"><a class="button" href="./study-packs.html">Explore the library →</a></div></section>',exclude=True)
    # Use origin-relative links for custom 404 pages, even when requested at a nested missing URL.
    error=output/'404.html';error.write_text(error.read_text().replace('href="./','href="/').replace('src="./','src="/'))
    (output/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+site['url']+'/sitemap.xml\n')
    (output/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{esc(u)}</loc></url>\n' for u in sorted(set(sitemap)))+'</urlset>\n')
    # Remove only previously generated pages, so withdrawn products do not linger.
    manifest=output/'.generated-pages.json'
    old=json.loads(manifest.read_text()) if manifest.exists() else []
    for path in set(old)-written:
        target=(output/path).resolve()
        if target.is_relative_to(output) and target.suffix=='.html':target.unlink(missing_ok=True)
    manifest.write_text(json.dumps(sorted(written),indent=2)+'\n')
    print(f'Built {len(written)} pages; {len(visible)} products; {"release" if args.release else "preview" if args.preview else "staging"}; output: {output}')

if __name__ == '__main__': main()
