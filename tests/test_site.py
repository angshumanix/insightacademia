"""Contract checks for generated pages and product publication safeguards."""
import copy
import importlib.util
import json
import re
import subprocess
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT/'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.tags=[]; self.feed(text)
    def handle_starttag(self, tag, attrs): self.tags.append((tag,dict(attrs)))
    def get(self, tag): return [a for t,a in self.tags if t==tag]

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['python','scripts/build.py'],cwd=ROOT,check=True)
        subprocess.run(['python','scripts/build.py','--preview','--out','.preview'],cwd=ROOT,check=True)

    def test_page_contracts_and_links(self):
        for output in [ROOT,ROOT/'.preview']:
            pages=json.loads((output/'.generated-pages.json').read_text())
            for path in pages:
                file=output/path;text=file.read_text();doc=Document(text)
                with self.subTest(output=output.name,page=path):
                    self.assertEqual(len(doc.get('h1')),1)
                    self.assertEqual(len(doc.get('main')),1)
                    self.assertTrue(any(a.get('name')=='description' and a.get('content') for a in doc.get('meta')))
                    self.assertTrue(any(a.get('name')=='robots' and 'noindex' in a.get('content','') for a in doc.get('meta')))
                    self.assertEqual(len([a for a in doc.get('link') if a.get('rel')=='canonical']),1)
                    self.assertFalse(doc.get('form'))
                    self.assertFalse(re.search(r'whatsapp|wa\.me|mailto:|formspree|ghostwrit|bespoke|tutoring|consulting|buy now|pay now|add to cart|purchase now',text,re.I))
                    ids=[a['id'] for _,a in doc.tags if 'id' in a]
                    self.assertEqual(len(ids),len(set(ids)))
                    for tag,a in doc.tags:
                        if tag=='img':self.assertTrue(a.get('alt'))
                        for key in ['href','src']:
                            if key not in a:continue
                            u=urlsplit(a[key])
                            if u.scheme:
                                self.assertIn(u.scheme,['https'])
                                if u.hostname in ['t.me','wa.me']:
                                    self.assertEqual(a[key],builder.TG)
                                continue
                            target=(output/unquote(u.path).lstrip('/')) if u.path.startswith('/') else file.parent/unquote(u.path)
                            if not u.path:target=file
                            self.assertTrue(target.is_file(),f'{path}: missing {a[key]}')
                            if u.fragment:
                                target_doc=Document(target.read_text())
                                self.assertIn(u.fragment,[v['id'] for _,v in target_doc.tags if 'id' in v])
                    for data in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S):
                        self.assertTrue(json.loads(data)['@graph'])

    def test_public_output_is_demonstrations_only(self):
        pages=json.loads((ROOT/'.generated-pages.json').read_text())
        self.assertEqual(len([p for p in pages if p.startswith('packs/')]),3)
        for output in [ROOT,ROOT/'.preview']:
            for file in (output/'packs').glob('*.html'):
                text=file.read_text()
                self.assertIn('Demonstration material — not a complete commercial study pack.',text)
                self.assertIn('Download sample PDF',text)
                self.assertNotIn('USD',text)
                self.assertNotIn('Sample suggested range',text)
                self.assertNotIn('"@type": "Product"',text)
                self.assertNotIn('"@type": "Offer"',text)
                self.assertIn('"@type": "LearningResource"',text)

    def test_sitemap_is_valid_and_pages_exist(self):
        for output in [ROOT,ROOT/'.preview']:
            tree=ET.parse(output/'sitemap.xml');urls=[n.text for n in tree.findall('.//{*}loc')]
            self.assertEqual(len(urls),len(set(urls)))
            self.assertNotIn(builder.TG,urls)
            for url in urls:
                self.assertEqual(urlsplit(url).hostname,'insightacademia.org')
                self.assertTrue((output/(urlsplit(url).path.lstrip('/') or 'index.html')).is_file())

    def test_release_stops_without_approval(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            fixture=Path(temp)
            for folder in ['scripts','data','templates','css','js','assets']:shutil.copytree(ROOT/folder,fixture/folder)
            site=json.loads((fixture/'data/site.json').read_text());site['deploymentApproved']=False
            (fixture/'data/site.json').write_text(json.dumps(site))
            result=subprocess.run(['python','scripts/build.py','--release','--out','export'],cwd=fixture,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('Release blocked',result.stderr)

    def test_approved_demonstration_release_without_full_products(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            fixture=Path(temp)
            for name in ['scripts','data','templates','css','js','assets']:
                shutil.copytree(ROOT/name,fixture/name)
            site=json.loads((fixture/'data/site.json').read_text())
            site.update(sellerName='QA fixture seller',policiesApproved=True,sellerDetailsApproved=True,demonstrationsApproved=True,deploymentApproved=True)
            (fixture/'data/site.json').write_text(json.dumps(site))
            demos=json.loads((fixture/'data/demonstrations.json').read_text())
            for d in demos:d['approved']=True
            (fixture/'data/demonstrations.json').write_text(json.dumps(demos))
            # Public generation must never read private/full-product metadata.
            (fixture/'data/products.json').write_text('[{"title":"CONFIDENTIAL FULL PRODUCT"}]')
            subprocess.run(['python','scripts/build.py','--release','--out','export'],cwd=fixture,check=True,capture_output=True)
            page=fixture/'export/packs/case-analysis-workbook.html';text=page.read_text()
            self.assertIn('content="index, follow"',text)
            self.assertNotIn('"offers"',text)
            self.assertNotIn('"@type": "Product"',text)
            for html in (fixture/'export').rglob('*.html'):
                self.assertNotIn('CONFIDENTIAL FULL PRODUCT',html.read_text())
            for gate in ['sellerDetailsApproved','policiesApproved','demonstrationsApproved','deploymentApproved']:
                modified=dict(site);modified[gate]=False
                (fixture/'data/site.json').write_text(json.dumps(modified))
                result=subprocess.run(['python','scripts/build.py','--release','--out','export'],cwd=fixture,capture_output=True)
                self.assertNotEqual(result.returncode,0,gate)

    def test_inventory_safeguards(self):
        site=json.loads((ROOT/'data/site.json').read_text())
        products=json.loads((ROOT/'data/products.json').read_text())
        p=copy.deepcopy(products[0]);p['status']='ready'
        with self.assertRaises(ValueError):builder.validate(site,[p])
        p['readiness']={k:True for k in p['readiness']}
        with self.assertRaises(ValueError):builder.validate(site,[p])
        for bad in ['../escape','Upper_Case','name/escape']:
            p=copy.deepcopy(products[0]);p['slug']=bad
            with self.assertRaises(ValueError):builder.validate(site,[p])
        p=copy.deepcopy(products[0]);p['preview']='../CNAME'
        with self.assertRaises(ValueError):builder.validate(site,[p])
        with self.assertRaises(ValueError):builder.validate(site,products+products[:1])

    def test_flexible_price_ranges_and_classification(self):
        site=json.loads((ROOT/'data/site.json').read_text())
        product=json.loads((ROOT/'data/products.json').read_text())[0]
        bands=json.loads((ROOT/'data/pricing-bands.json').read_text())
        self.assertEqual([(b['id'],b['name'],b['suggestedLower'],b['suggestedUpper']) for b in bands], [
            (1,'Entry','10.00','99.99'),(2,'Standard','100.00','199.99'),(3,'Professional','200.00','349.99'),
            (4,'Advanced','350.00','549.99'),(5,'Premium','550.00','899.99'),(6,'Comprehensive','900.00','1499.99'),(7,'Complete Collection','1500.00','2499.99')])
        for band in range(1,8):
            p=copy.deepcopy(product);p['pricingBand']=band;builder.validate(site,[p])
        for changes in [{'suggestedLower':'30.01','suggestedUpper':'30.00'}, {'suggestedLower':'NaN'}, {'suggestedUpper':'Infinity'}, {'suggestedUpper':'-1'}, {'suggestedLower':'1.001'}, {'pricingBand':8}, {'pricingBand':True}, {'currency':'EUR'}, {'price':'19.00'}]:
            p=copy.deepcopy(product);p.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):builder.validate(site,[p])
        # Internal classification never forces a customer's amount or dictates the product range.
        p=copy.deepcopy(product);p.update(suggestedLower='1.00',suggestedUpper='4.00');builder.validate(site,[p])
        self.assertEqual(builder.price_range(p),'USD 1.00–4.00')
        p.update(suggestedLower='1500.00',suggestedUpper='2499.99')
        self.assertEqual(builder.price_range(p),'USD 1,500.00–2,499.99')
        for file in (ROOT/'.preview/packs').glob('*.html'):
            text=file.read_text()
            self.assertNotIn('USD',text)
            self.assertNotIn('Complete Collection',text)
            self.assertNotIn('"offers"',text)
        for name in ['how-to-order.html','faq.html']:
            self.assertNotIn('Pay what you think is fair',(ROOT/name).read_text())

    def test_free_launch_scope_and_samples(self):
        from pypdf import PdfReader
        for d in json.loads((ROOT/'data/demonstrations.json').read_text()):
            pdf=PdfReader(ROOT/d['samplePdf']);self.assertEqual(len(pdf.pages),2)
            self.assertIn('not a complete commercial study pack',pdf.pages[0].extract_text())
        for file in [ROOT/p for p in json.loads((ROOT/'.generated-pages.json').read_text())]:
            text=file.read_text()
            self.assertNotRegex(text.lower(),r'paypal|pay what|payment link|purchase|price negotiation|full-pack availability')
            self.assertNotRegex(text,r'\b[A-Z]{5}[0-9]{4}[A-Z]\b')
        for name in ['index.html','about.html','contact.html']:
            self.assertNotIn('Angshuman Banerjee',(ROOT/name).read_text())
        self.assertIn('Angshuman Banerjee',(ROOT/'privacy.html').read_text())
        for asset in ['logo-dark.svg','logo-light.svg','emblem.svg','favicon.svg']:ET.parse(ROOT/'assets'/asset)

    def test_regeneration_is_deterministic_and_cleans_retired_pages(self):
        target=ROOT/'.preview/packs/retired-test.html';target.write_text('retired')
        manifest=ROOT/'.preview/.generated-pages.json';old=json.loads(manifest.read_text());manifest.write_text(json.dumps(old+['packs/retired-test.html']))
        home=(ROOT/'.preview/index.html').read_bytes()
        subprocess.run(['python','scripts/build.py','--preview','--out','.preview'],cwd=ROOT,check=True,capture_output=True)
        self.assertFalse(target.exists())
        self.assertEqual(home,(ROOT/'.preview/index.html').read_bytes())

    def test_accessible_palette(self):
        def luminance(hexcode):
            vals=[int(hexcode[i:i+2],16)/255 for i in (0,2,4)]
            return sum(w*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for w,v in zip([.2126,.7152,.0722],vals))
        for foreground,background in [('ffffff','123e32'),('54645b','f7f5ef'),('755b24','f7f5ef'),('d5bc80','0b2b23'),('bdccc0','0b2b23'),('624a1d','fbf5e5')]:
            a,b=sorted([luminance(foreground),luminance(background)])
            self.assertGreaterEqual((b+.05)/(a+.05),4.5)

if __name__=='__main__':unittest.main(verbosity=2)
