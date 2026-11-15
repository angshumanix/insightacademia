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

    def test_demos_cannot_appear_as_available_products(self):
        pages=json.loads((ROOT/'.generated-pages.json').read_text())
        self.assertFalse(any(p.startswith('packs/') for p in pages))
        for file in (ROOT/'.preview/packs').glob('*.html'):
            text=file.read_text()
            self.assertIn('Demonstration only',text)
            self.assertIn('Sample price for layout review',text)
            self.assertNotIn('"@type": "Product"',text)
            self.assertNotIn('"@type": "Offer"',text)
        self.assertNotIn('/packs/',(ROOT/'.preview/sitemap.xml').read_text())

    def test_sitemap_is_valid_and_pages_exist(self):
        for output in [ROOT,ROOT/'.preview']:
            tree=ET.parse(output/'sitemap.xml');urls=[n.text for n in tree.findall('.//{*}loc')]
            self.assertEqual(len(urls),len(set(urls)))
            self.assertNotIn(builder.TG,urls)
            for url in urls:
                self.assertEqual(urlsplit(url).hostname,'insightacademia.org')
                self.assertTrue((output/(urlsplit(url).path.lstrip('/') or 'index.html')).is_file())

    def test_release_stops_without_approval(self):
        result=subprocess.run(['python','scripts/build.py','--release'],cwd=ROOT,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Release blocked',result.stderr)

    def test_approved_fixture_generates_static_product_and_offer(self):
        # Isolated fixture exercises future publication without promoting any real demo record.
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            fixture=Path(temp)
            for name in ['scripts','data','templates','css','js','assets']:
                shutil.copytree(ROOT/name,fixture/name)
            site=json.loads((fixture/'data/site.json').read_text())
            site.update(sellerName='QA fixture seller',policiesApproved=True)
            (fixture/'data/site.json').write_text(json.dumps(site))
            product=json.loads((fixture/'data/products.json').read_text())[0]
            product.update(id='QA-001',status='ready',version='1.0',title='Approved QA fixture',preview='assets/qa-approved.svg')
            product['readiness']={k:True for k in product['readiness']}
            (fixture/'data/products.json').write_text(json.dumps([product]))
            shutil.copy(fixture/'assets/sample-case.svg',fixture/'assets/qa-approved.svg')
            subprocess.run(['python','scripts/build.py','--release','--out','export'],cwd=fixture,check=True,capture_output=True)
            page=fixture/'export/packs/case-analysis-workbook.html'
            text=page.read_text()
            self.assertIn('content="index, follow"',text)
            self.assertIn('"@type": "Product"',text)
            self.assertIn('"priceCurrency": "USD"',text)
            self.assertIn('Ask about this study pack',text)
            self.assertNotIn('Policy draft for development review',text)
            self.assertIn('/packs/case-analysis-workbook.html',(fixture/'export/sitemap.xml').read_text())

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
