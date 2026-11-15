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
        try:
            price = Decimal(p['price'])
            if not price.is_finite() or price <= 0 or price.as_tuple().exponent < -2:
                raise ValueError('Price must be a positive amount with at most two decimal places.')
        except InvalidOperation as exc:
            raise ValueError('Invalid price.') from exc
        if not re.fullmatch(r'[A-Z]{3}', p['currency']):
            raise ValueError('Use an explicit three-letter currency code.')
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

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--preview', action='store_true', help='Include labelled demo products; always noindex.')
    mode.add_argument('--release', action='store_true', help='Indexable output; requires approved policies and ready products. Does not deploy.')
    parser.add_argument('--out', default='.', help='Output directory relative to repository root.')
    args = parser.parse_args(argv)
    site = json.loads((ROOT/'data/site.json').read_text())
    products = json.loads((ROOT/'data/products.json').read_text())
    validate(site, products)
    ready = [p for p in products if p['status'] == 'ready']
    if args.release and (not site['policiesApproved'] or not site['sellerName'].strip() or not ready):
        parser.error('Release blocked: approve policies, seller identity and at least one real product first.')
    output = (ROOT/args.out).resolve()
    if not output.is_relative_to(ROOT) or output == ROOT/'.git' or '.git' in output.relative_to(ROOT).parts:
        parser.error('Output must stay inside the repository and outside .git.')
    output.mkdir(parents=True, exist_ok=True)
    if output != ROOT:
        import shutil
        for folder in ['css', 'js', 'assets']:
            shutil.copytree(ROOT/folder, output/folder, dirs_exist_ok=True)
    visible = [p for p in products if p['status'] == 'ready' or (args.preview and p['status'] == 'demo')]
    cats = {c['id']:c for c in site['categories']}
    layout = Template((ROOT/'templates/page.html').read_text())
    product_layout = Template((ROOT/'templates/product.html').read_text())
    written, sitemap = set(), []
    robots = 'index, follow' if args.release else 'noindex, nofollow'
    def href(path, prefix): return f'{prefix}/{path}'
    def telegram(label='Get in touch on Telegram', extra=''):
        return f'<a class="button {extra}" href="{TG}">{esc(label)} <span aria-hidden="true">↗</span></a>'
    def process(prefix):
        steps = [('Choose your study pack','Browse the contents, specifications, preview and listed price. Note the product code.'),('Get in touch on Telegram','Tell us the product code. We send a PayPal payment link directly in the conversation.'),('Receive your files','After you pay through PayPal, we verify the payment and manually deliver your files through Telegram.')]
        return '<div class="process-grid">'+''.join(f'<div class="process-step"><span>0{i}</span><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for i,(t,d) in enumerate(steps,1))+'</div>'
    def empty(prefix, category=False):
        return f'<div class="empty-state"><p class="eyebrow">The collection is taking shape</p><h2>{"New resources are being prepared." if category else "Good learning starts with a clear resource."}</h2><p>Our first study packs are being developed. Approved packs will appear here with their contents, a preview and a clear price.</p>{telegram()}<p class="fine-print">Follow up with us on Telegram for collection updates.</p></div>'
    def cards(items, prefix):
        if not items: return empty(prefix)
        result = '<div class="product-grid">'
        for p in items:
            demo = p['status'] == 'demo'
            url = href('packs/'+p['slug']+'.html',prefix)
            price = f"{p['currency']} {Decimal(p['price']):.2f}"
            result += f'''<article class="product-card" data-product data-category="{esc(p['category'])}"><a href="{url}" class="card-art" aria-label="View {esc(p['title'])}{' demonstration' if demo else ''}"><div class="book book-{esc(p['cover'])}" aria-hidden="true"><span class="book-brand">INSIGHTACADEMIA</span><div class="book-lines"></div><span class="book-kicker">THE STUDY COLLECTION</span><span class="book-title">{esc(p['title'])}</span><span class="book-foot">{'DEMONSTRATION COVER' if demo else esc(' · '.join(p['formats']))}</span></div></a><div class="card-body"><p class="eyebrow">{esc(cats[p['category']]['name'])}</p><h3><a href="{url}">{esc(p['title'])}</a></h3><p>{esc(p['summary'])}</p><div class="card-bottom"><span class="price">{esc(price)}{'<span class="sample-tag">Sample price</span>' if demo else ''}</span><a class="text-link" href="{url}">{'View demo' if demo else 'View pack'} <span aria-hidden="true">→</span></a></div>{'<p class="card-status">Demonstration only · not available</p>' if demo else ''}</div></article>'''
        return result+'</div>'
    def categories(prefix):
        return '<div class="category-grid">'+''.join(f'<a class="category-card" href="{href("categories/"+c["id"]+".html",prefix)}"><span class="category-number">{esc(c["number"])}</span><h3>{esc(c["name"])}</h3><p>{esc(c["description"])}</p><span class="category-link">Explore category <span aria-hidden="true">↗</span></span></a>' for c in site['categories'])+'</div>'
    def page(path, title, description, body, active='', schema=None, canonical_path=None, exclude=False):
        prefix = '..' if '/' in path else '.'
        canonical_path = canonical_path or path
        canonical = site['url'] + ('/' if canonical_path == 'index.html' else '/'+canonical_path)
        nav = ''.join(f'<a href="{href(p,prefix)}"'+(' aria-current="page"' if active==label else '')+f'>{label}</a>' for label,p in [('Study packs','study-packs.html'),('How to order','how-to-order.html'),('About','about.html')])
        if args.preview:
            notice='<div class="dev-notice"><strong>Design preview.</strong> Demonstration packs, specifications and prices are illustrative. Products are not available.</div>'
        elif not args.release:
            notice='<div class="dev-notice"><strong>Development review.</strong> The collection is in preparation. Product availability and policy details await approval.</div>'
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
        if not exclude and not (path.startswith('packs/') and any(p['status']=='demo' and p['slug']+'.html'==Path(path).name for p in visible)):
            sitemap.append(canonical)
    def hero(eyebrow,title,desc):
        return f'<section class="page-hero"><div class="container"><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1><p class="lead">{esc(desc)}</p></div></section>'
    art='''<div class="hero-art" role="img" aria-label="Illustrative green and ivory study-pack covers"><div class="book book-back" aria-hidden="true"><span class="book-brand">INSIGHTACADEMIA</span><div class="book-lines"></div><span class="book-kicker">THE STUDY COLLECTION</span><span class="book-title">A clearer way to learn.</span><span class="book-foot">REFERENCE · REFLECT · UNDERSTAND</span></div><div class="book book-front" aria-hidden="true"><span class="book-brand">INSIGHTACADEMIA</span><div class="book-lines"></div><span class="book-kicker">INDEPENDENT LEARNING</span><span class="book-title">Make room for understanding.</span><span class="book-foot">THE STUDY COLLECTION</span></div><span class="art-caption">Illustrative covers · the study collection</span></div>'''
    home=f'''<section class="hero"><div class="container hero-grid"><div><p class="eyebrow">A little structure. A clearer starting point.</p><h1>Study with purpose.<br><em>Learn with clarity.</em></h1><p class="lead">Thoughtfully structured study packs for independent learning. Explore practical frameworks, worked examples and resources you can return to.</p><div class="actions"><a class="button" href="./study-packs.html">Explore the study packs <span aria-hidden="true">→</span></a><a class="text-link" href="./how-to-order.html">How it works <span aria-hidden="true">↗</span></a></div><div class="hero-note"><span>Digital learning resources</span><span>Clear contents &amp; pricing</span></div></div>{art}</div></section><div class="principles"><div class="container"><p><span aria-hidden="true">01</span> Ready-made study materials</p><p><span aria-hidden="true">02</span> A direct conversation on Telegram</p><p><span aria-hidden="true">03</span> Files delivered after payment</p></div></div><section class="section"><div class="container"><div class="section-heading"><div><p class="eyebrow">Find your starting point</p><h2>What are you learning?</h2></div><p>Browse by learning purpose. Find a resource that fits the way you want to study.</p></div>{categories('.')}</div></section><section class="section section-white"><div class="container"><div class="section-heading"><div><p class="eyebrow">{'A look at the layout' if args.preview else 'The study collection'}</p><h2>{'A few ways to find clarity.' if visible else 'Thoughtful resources, taking shape.'}</h2></div><a class="text-link" href="./study-packs.html">Explore the collection <span aria-hidden="true">→</span></a></div>{cards(visible[:3],'.')}</div></section><section class="section"><div class="container"><div class="section-heading"><div><p class="eyebrow">From browsing to your files</p><h2>Keep it simple.</h2></div><p>Choose a pack, get in touch on Telegram, and receive your files after payment is verified.</p></div>{process('.')}<a class="text-link margin-top" href="./how-to-order.html">The ordering process, explained <span aria-hidden="true">→</span></a></div></section><section class="section section-white"><div class="container dark-panel"><div><p class="eyebrow">Your learning, your pace</p><h2>A useful reference.<br>A clearer next step.</h2><p>Study packs bring a little more structure to unfamiliar topics. Read through an example, work with a framework and develop your own understanding.</p></div><div><p>Have a question about the collection? Start a conversation with InsightAcademia.</p>{telegram()}<p class="fine-print">Our official account: @InsightAcademiaPacks</p></div></div></section>'''
    page('index.html','Downloadable study packs for independent learning','Explore structured digital study packs, worked examples and learning frameworks from InsightAcademia. Contact us through our official Telegram account.',home)
    def catalogue(path, cat=None):
        prefix='..' if '/' in path else '.'
        items=[p for p in visible if not cat or p['category']==cat['id']]
        title=cat['name'] if cat else 'Find your next starting point.'
        intro=cat['description'] if cat else 'Study resources organized around the way you learn. Explore the contents, check the details and get in touch on Telegram.'
        body=hero('The study collection',title,intro)
        body+=f'<section class="section"><div class="container">'
        if items:
            if args.preview:body+='<p class="policy-draft"><strong>Demonstration catalogue.</strong> These examples show the page layouts. Contents, file formats, page counts and prices are illustrative.</p>'
            options=''.join(f'<option value="{esc(c["id"])}">{esc(c["name"])}</option>' for c in site['categories'] if not cat or c['id']==cat['id'])
            body+=f'<div class="catalogue-tools" data-catalogue-tools data-demo="{str(args.preview).lower()}" hidden><div class="field"><label for="pack-search">Find a study pack</label><input id="pack-search" type="search" placeholder="Search by title or topic" autocomplete="off"></div><div class="field"><label for="pack-category">Learning category</label><select id="pack-category"><option value="">All categories</option>{options}</select></div><button class="button button-light" type="button">Clear filters</button></div><p class="results-count" data-result-count role="status" aria-live="polite">{len(items)} packs{' · demonstration layouts only' if args.preview else ''}</p>{cards(items,prefix)}<div class="empty-state" data-no-results hidden><h2>No matching study packs.</h2><p>Try another title or topic, or clear the filters to see the collection again.</p></div>'
        else:body+=empty(prefix, bool(cat))
        body+='</div></section>'
        if not cat:body+=f'<section class="section section-white"><div class="container"><p class="eyebrow">Explore by learning purpose</p><h2>Four places to begin.</h2>{categories(prefix)}</div></section>'
        page(path,title if cat else 'Study packs',intro,body,active='Study packs')
    catalogue('study-packs.html')
    for cat in site['categories']:catalogue('categories/'+cat['id']+'.html',cat)
    for p in visible:
        demo=p['status']=='demo';prefix='..'
        values={k:esc(p[k]) for k in ['id','title','summary','description','audience','pages','version','cover']}
        values.update(prefix=prefix,telegram=TG,category=esc(cats[p['category']]['name']),category_url='../categories/'+p['category']+'.html',status='Demonstration only · not available' if demo else 'Digital study pack',price=esc(f"{p['currency']} {Decimal(p['price']):.2f}")+('<span class="sample-tag">Sample price for layout review</span>' if demo else ''),formats=esc(' + '.join(p['formats'])),availability='<p class="policy-draft">Illustrative product page. This pack and its specifications are a demonstration, not an available download.</p>' if demo else '',cta='Get in touch on Telegram' if demo else 'Ask about this study pack',order_note='This code identifies a demonstration layout.' if demo else 'Include this code in your Telegram message.',contents_heading='Illustrative contents' if demo else 'What you will receive',contents=''.join(f'<li><span aria-hidden="true">{i:02d}</span>{esc(c)}</li>' for i,c in enumerate(p['contents'],1)),cover_note='Demonstration cover' if demo else ' · '.join(p['formats']),preview_heading='An illustrative worksheet' if demo else 'Preview the study pack',preview_note='A sample layout for design review. This is not an extract from a finished product.' if demo else 'An approved extract from this study pack.',preview=f'<figure class="sample-preview"><img src="../{esc(p["preview"])}" alt="{esc(p["previewAlt"])}" width="900" height="660" loading="lazy"><figcaption>{"DEMONSTRATION SAMPLE · ILLUSTRATIVE CONTENT" if demo else esc(p["title"])+" · preview extract"}</figcaption></figure>',process=process(prefix),related=cards([q for q in visible if q['id']!=p['id']][:3],prefix))
        schema=None
        if not demo:
            schema={'@type':'Product','name':p['title'],'description':p['summary'],'sku':p['id'],'image':site['url']+'/'+p['preview'],'brand':{'@type':'Brand','name':site['name']},'offers':{'@type':'Offer','price':p['price'],'priceCurrency':p['currency'],'url':site['url']+'/packs/'+p['slug']+'.html','availability':'https://schema.org/InStock','seller':{'@type':'Organization','name':site['sellerName']}}}
        page('packs/'+p['slug']+'.html',p['title'],p['summary'],product_layout.substitute(values),active='Study packs',schema=schema,exclude=demo)
    ordering=hero('A direct, simple process','From your first look to your files.','Browse at your own pace. When a study pack is available, its page will explain exactly what is included and what it costs.')+f'<section class="section"><div class="container">{process(".")}</div></section><section class="section section-white"><div class="container detail-layout"><div class="prose"><h2>What to send on Telegram</h2><p>Send the study pack’s name or product code to <strong>@InsightAcademiaPacks</strong>. We will confirm the pack and listed price, then send a PayPal payment link in the conversation.</p><h2>Payment and delivery</h2><p>Complete payment on PayPal. Once we verify it, we manually send the downloadable files through Telegram. Delivery timing will be confirmed in the conversation before payment.</p><p>Save your files to a device you control so you can return to them when you study.</p></div><aside class="detail-note"><h2>One official account.</h2><p>Use the link below to contact InsightAcademia directly.</p>{telegram()}<p class="fine-print">@InsightAcademiaPacks</p></aside></div></section>'
    page('how-to-order.html','How to order a study pack','Choose a study pack, contact InsightAcademia on Telegram, receive a PayPal link and get your files after payment verification.',ordering,active='How to order')
    about=hero('About InsightAcademia','A little more structure for independent learning.','We are building a collection of ready-made digital study packs that make academic learning easier to navigate.')+'''<section class="section"><div class="container detail-layout"><div class="prose"><h2>Useful resources start with a clear purpose.</h2><p>A helpful study resource makes a topic easier to approach. It lays out the ideas, explains a framework and gives you something practical to work through.</p><p>Our collection is organized around familiar learning tasks: revising a topic, understanding a case, organizing research and presenting ideas. Each approved product will have a clear description, contents, specifications, preview and listed price.</p><h2>Something you can return to.</h2><p>Digital study packs give you room to learn at your own pace. Read an example, revisit an explanation and reflect on how the ideas connect with your own learning.</p></div><aside class="detail-note"><span class="tiny-label">The approach</span><h2>Clear contents.<br>Practical structure.<br>Your own understanding.</h2><p>The collection will grow progressively as new resources are created, reviewed and approved.</p></aside></div></section>'''
    page('about.html','About the study collection','Learn about InsightAcademia’s collection of ready-made digital resources for independent academic learning.',about,active='About')
    contact=hero('Let’s talk about learning','Get in touch on Telegram.','Questions about a study pack, its contents or the ordering process? Reach InsightAcademia through our official account.')+f'<section class="section"><div class="container detail-layout"><div class="contact-card"><p class="eyebrow">The official InsightAcademia account</p><h2>Start a conversation.</h2><p class="handle">@InsightAcademiaPacks</p><p>Include the product name or code if your question is about a particular pack.</p>{telegram()}<p class="fine-print">The link opens Telegram. You choose what to send.</p></div><div class="prose"><h2>A considered approach to privacy.</h2><p>You can contact a Telegram username and control your phone-number visibility in Telegram’s privacy settings. Ordinary Telegram cloud chats use client–server encryption. End-to-end encryption is available through the separate Secret Chats feature.</p><p>Telegram lets you delete one-to-one conversations for both parties. Downloaded files and PayPal records are managed separately.</p><a class="text-link" href="./privacy.html">Read the privacy details <span aria-hidden="true">→</span></a></div></div></section>'
    page('contact.html','Contact on Telegram','Contact InsightAcademia through the official Telegram account @InsightAcademiaPacks for questions about downloadable study packs.',contact)
    faqs=[('What is a study pack?','A ready-made digital learning resource. A pack may include explanations, frameworks, worksheets and worked examples. The individual product page will describe its exact contents.'),('Are any study packs available yet?','The first collection is in preparation. Available products will be listed with approved contents, previews, file specifications and prices. Demonstration products in the design preview are illustrative.'),('How do I order a pack?','Choose an available pack and send its name or code to @InsightAcademiaPacks on Telegram. We send a PayPal payment link, verify the completed payment and manually deliver the files through Telegram.'),('What file formats will I receive?','The product page will list the included formats, such as PDF or editable document files. Check those specifications before ordering.'),('How soon will my files arrive?','Delivery is manual. We confirm the expected timeframe on Telegram before you pay, then send the files after verifying payment.'),('How can I use the materials?','Use them for independent learning and personal academic reference. Product-specific licence details will be shown before purchase. Follow the academic rules that apply to your course.'),('What if I have a problem with a file?','Contact @InsightAcademiaPacks on Telegram with the product code and a description of the issue. The digital-product policy explains the details to be finalized before launch.'),('How does privacy work?','The website uses a simple static catalogue. Conversations take place on Telegram and payments on PayPal. Read the privacy page for the distinctions between these platforms and their data handling.')]
    if ready:
        faqs[1]=('Which study packs are available?','Browse the catalogue for the current approved collection. Each available pack has its own contents, preview, specifications and price. Demonstration layouts are labelled separately in development previews.')
    faq=hero('Common questions','A few useful details.','The collection, the files and the process, explained in plain language.')+'<section class="section"><div class="container faq-list">'+''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q,a in faqs)+'</div></section>'
    page('faq.html','Study pack questions','Answers about digital study packs, file formats, Telegram enquiries, PayPal payment and manual delivery.',faq)
    draft='<div class="policy-draft"><strong>Policy draft for development review.</strong> Operational details and seller information require approval before this website is launched.</div>' if not site['policiesApproved'] else ''
    policies={
      'privacy.html':('Privacy','A simple catalogue. A clear view of your data.','Privacy information for the InsightAcademia website, Telegram conversations and PayPal payments.', '''<h2>Using the website</h2><p>This static website presents study-pack information. Its own code uses no analytics trackers, advertising tags, cookies or local storage. Fonts and visual assets are served with the site. The hosting provider may process technical request data, such as IP addresses and server logs, to deliver and secure the website.</p><h2>Contact through Telegram</h2><p>Customer communication takes place through @InsightAcademiaPacks. Messages and any profile details you share are visible to the account receiving them. Telegram processes conversations under its own policies. You can manage phone-number visibility and other privacy settings in Telegram.</p><p>Ordinary cloud chats are not end-to-end encrypted. Telegram’s separate Secret Chats feature provides end-to-end encryption. You can delete one-to-one messages for both parties, but downloaded copies and payment records are separate.</p><h2>Paying through PayPal</h2><p>Payment links are sent manually in Telegram. Payment details are entered on PayPal. PayPal processes payment data under its own policies and provides transaction information to the seller.</p><h2>Order records and retention</h2><p>The final policy will identify the seller, specify the minimum order information retained, explain the retention period and describe how privacy requests are handled. These operational details are awaiting approval before launch.</p><h2>Questions about privacy</h2><p>Contact InsightAcademia through the official Telegram account. See also <a href="https://telegram.org/privacy">Telegram’s privacy policy</a> and <a href="https://www.paypal.com/webapps/mpp/ua/privacy-full">PayPal’s privacy policy</a>.</p>'''),
      'terms.html':('Terms & permitted use','Clear expectations for the study collection.','Terms framework and permitted-use guidance for InsightAcademia digital learning materials.', '''<h2>About the collection</h2><p>InsightAcademia provides ready-made downloadable resources for independent learning and academic reference. Each product page will identify its contents, formats, listed price and any product-specific conditions.</p><h2>Personal learning and reference</h2><p>Use learning materials to understand concepts, explore examples and develop your own work. Follow your institution’s academic rules and acknowledgement requirements.</p><h2>Product licence</h2><p>The final licence will specify personal-use permissions, editable-file permissions, sharing restrictions and any group-use options. Those details will be displayed before purchase. Copyright in third-party material remains with its respective owners.</p><h2>Ordering and payment</h2><p>Orders begin through the official Telegram account. A PayPal payment link is sent manually, and downloadable files are delivered through Telegram after payment verification.</p><h2>Information to finalize</h2><p>Seller identity, applicable jurisdiction, product licensing, order acceptance and any statutory consumer-rights wording require approval before launch. The digital-product policy will explain delivery and issue resolution.</p>'''),
      'digital-products.html':('Digital-product policy','The details behind your download.','Delivery and digital-product policy framework for InsightAcademia downloadable study packs.', '''<h2>Product information</h2><p>Review the pack contents, preview, file formats, price and currency before ordering. A product code identifies the selected pack. Any compatibility requirements will be included in the product specifications.</p><h2>Manual digital delivery</h2><p>We confirm the expected delivery timeframe through Telegram before payment. Once payment has been verified, we manually send the files through the same official account.</p><h2>File access and incorrect files</h2><p>If a file is inaccessible, incomplete or different from the confirmed product, contact @InsightAcademiaPacks with the product code and a description of the issue so it can be reviewed.</p><h2>Refunds, cancellation and duplicate payments</h2><p>The final policy will explain how refund requests, cancellation, duplicate payments and delivery problems are handled. These terms require approval before sales begin and will reflect the rights applicable to the transaction.</p><h2>Versions and updates</h2><p>Each product will identify the version being supplied. Any included update entitlement will be stated on its page. Update commitments and replacement-file availability are awaiting approval.</p>''')}
    for path,(title,headline,desc,body) in policies.items():
        page(path,title,desc,hero('The details',headline,desc)+f'<section class="section"><div class="container prose">{draft}{body}<p>{telegram()}</p></div></section>')
    page('services.html','Explore the study-pack catalogue','Explore InsightAcademia’s study-pack collection.',hero('The study collection','The catalogue has a new home.','Explore learning resources by category and see the latest approved study packs.')+'<section class="section"><div class="container"><a class="button" href="./study-packs.html">Explore study packs <span aria-hidden="true">→</span></a></div></section>',canonical_path='study-packs.html',exclude=True)
    page('404.html','Page not found','Find your way back to the InsightAcademia study collection.',hero('Page not found','Let’s find your starting point.','This page could not be found. Explore the study collection or contact us on Telegram.')+'<section class="section"><div class="container actions"><a class="button" href="./study-packs.html">Explore the catalogue <span aria-hidden="true">→</span></a>'+telegram(extra='button-light')+'</div></section>',exclude=True)
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
