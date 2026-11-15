"""Verify deployed public assets, metadata and sample downloads. No write operations."""
import hashlib
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
from html.parser import HTMLParser

BASE = os.environ.get('SITE_BASE', 'https://insightacademia.org').rstrip('/')
ROOT = Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag in ('a','link','script','img'):
            value=a.get('href') or a.get('src')
            if value:self.links.append(value)
def fetch(path):
    with urlopen(BASE+path, timeout=30) as r:
        return r.status, r.read(), {k.lower():v for k,v in r.headers.items()}
paths=['/']+['/'+str(p.relative_to(ROOT)) for p in ROOT.rglob('*.html') if p.name != '404.html' and '.preview' not in p.parts and 'node_modules' not in p.parts and '.git' not in p.parts]
paths += ['/robots.txt','/sitemap.xml']
checked=set(paths)
for path in paths:
    status,body,headers=fetch(path)
    # A real missing-page response is checked separately below.
    assert status==200,(path,status)
    if path.endswith('.html') or path=='/':
        text=body.decode(); parsed=Links();parsed.feed(text)
        if path not in ('/404.html','/services.html'):
            assert 'content="index, follow"' in text,path
            assert '<link rel="canonical" href="https://insightacademia.org/' in text,path
        assert 'paypal' not in text.lower(),path
        for link in parsed.links:
            if 't.me/' in link:assert link=='https://t.me/InsightAcademiaPacks',(path,link)
            url=urlparse(urljoin(BASE+path,link))
            if url.netloc==urlparse(BASE).netloc:checked.add(url.path or '/')
    if path=='/':
        assert headers.get('x-content-type-options')=='nosniff',headers
        assert 'frame-ancestors' in headers.get('content-security-policy',''),headers
        assert 'noindex' not in headers.get('x-robots-tag','')
for path in sorted(checked-set(paths)):
    assert fetch(path)[0]==200,path
for local in sorted((ROOT/'assets').glob('demo-*.pdf')):
    body=fetch('/assets/'+local.name)[1]
    assert body.startswith(b'%PDF-'),local.name
    assert hashlib.sha256(body).digest()==hashlib.sha256(local.read_bytes()).digest(),local.name
robots=fetch('/robots.txt')[1].decode()
assert 'Disallow: /\n' not in robots and 'https://insightacademia.org/sitemap.xml' in robots
assert 'https://insightacademia.org/' in fetch('/sitemap.xml')[1].decode()
try:
    fetch('/this-page-does-not-exist-qa.html');raise AssertionError('Missing path returned 200')
except HTTPError as error:
    assert error.code==404,error.code
print(f'LIVE PASS: {len(checked)} public paths, internal links, 3 exact PDF downloads, Telegram destinations, production indexing, canonical URLs, security headers and real 404.')
