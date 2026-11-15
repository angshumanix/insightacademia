#!/usr/bin/env python3
"""Create an offline, self-contained review of actual generated pages. Never deploys."""
import argparse
import base64
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='.preview/InsightAcademia_Design_Preview.html')
    args=parser.parse_args()
    subprocess.run(['python','scripts/build.py','--preview','--out','.preview'],cwd=ROOT,check=True)
    folder=ROOT/'.preview';pages=json.loads((folder/'.generated-pages.json').read_text());documents={}
    css=(ROOT/'css/style.css').read_text();js=(ROOT/'js/main.js').read_text()
    for route in pages:
        text=(folder/route).read_text()
        # Review-only packaging: inline the same assets, preserving the site source.
        text=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',text)
        text=re.sub(r'<link rel="stylesheet"[^>]*>',lambda _: '<style>'+css+'</style>',text)
        text=re.sub(r'<link rel="icon"[^>]*>','',text)
        text=re.sub(r'<script src="[^"]+" defer></script>',lambda _: '<script>document.addEventListener("DOMContentLoaded", function(){\n'+js+'\n});</script>',text)
        def embed(match):
            asset=(Path(route).parent/match.group(1)).as_posix()
            # Resolve known local image references against the generated output.
            target=(folder/asset).resolve()
            if not target.is_relative_to(folder.resolve()) or not target.is_file():raise ValueError(asset)
            mime='image/svg+xml' if target.suffix=='.svg' else 'image/png'
            return 'src="data:'+mime+';base64,'+base64.b64encode(target.read_bytes()).decode()+'"'
        text=re.sub(r'src="([^\"]+\.(?:svg|png))"',embed,text)
        bridge='''\n<script>
document.addEventListener('click',function(e){const a=e.target.closest('a');if(!a)return;const raw=a.getAttribute('href');if(!raw||raw.startsWith('#'))return;if(/^https?:/.test(raw)){a.target='_blank';a.rel='noopener noreferrer';return;}e.preventDefault();const route=new URL(raw,'https://review.invalid/'+ROUTE).pathname.slice(1);parent.postMessage({type:'insightacademia-preview-route',route},'*');});
</script>'''.replace('ROUTE',json.dumps(route))
        text=text.replace('</body>',bridge+'</body>')
        documents[route]=text
    encoded=json.dumps(documents,ensure_ascii=False).replace('<','\\u003c')
    body='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>InsightAcademia — design review</title><style>
*{box-sizing:border-box}body{margin:0;background:#dde3db;color:#15392d;font:14px/1.5 system-ui,sans-serif}.review-bar{display:flex;gap:16px;flex-wrap:wrap;align-items:center;padding:13px 20px;background:#fff;border-bottom:1px solid #bcc8bb}.review-bar strong{margin-right:auto}.review-bar select,.review-bar button{font:inherit;padding:9px 12px;min-height:42px;border:1px solid #9eae9e;border-radius:3px;background:#fff;color:#15392d}.review-bar button[aria-pressed=true]{background:#123e32;color:white}.review-bar label{display:flex;align-items:center;gap:8px}.review-note{padding:9px 20px;font-size:12px;margin:0;background:#eee4c9}.frame-wrap{padding:20px;display:flex;justify-content:center;align-items:start}iframe{display:block;width:100%;height:1000px;max-width:1440px;border:1px solid #b7c3b2;background:#f7f5ef}iframe.mobile{max-width:390px;height:844px}button:focus-visible,select:focus-visible{outline:3px solid #956e16;outline-offset:3px}@media(max-width:600px){.review-bar{gap:8px;padding:10px}.review-bar strong{width:100%}.frame-wrap{padding:0}iframe{border:0;height:850px}.review-note{padding:10px}}
</style></head><body><div class="review-bar"><strong>InsightAcademia · design review</strong><label>Page <select id="page"><option value="index.html">Homepage</option><option value="study-packs.html">Catalogue</option><option value="packs/case-analysis-workbook.html">Product detail</option><option value="how-to-order.html">How to order</option><option value="about.html">About</option><option value="contact.html">Contact</option><option value="faq.html">FAQ</option><option value="privacy.html">Privacy draft</option><option value="terms.html">Terms draft</option><option value="digital-products.html">Digital-product policy draft</option></select></label><button id="desktop" type="button" aria-pressed="true">Desktop</button><button id="mobile" type="button" aria-pressed="false">Mobile</button></div><p class="review-note">Offline review of the generated pages. Demonstration packs and prices are illustrative. This preview has not been deployed. Desktop/mobile controls change the frame width; this is not a completed browser-QA report.</p><div class="frame-wrap"><iframe id="preview" title="InsightAcademia development preview" sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"></iframe></div><script>
const documents=DOCUMENTS;
const frame=document.getElementById('preview'),picker=document.getElementById('page');
function show(route){if(!Object.prototype.hasOwnProperty.call(documents,route))return;frame.srcdoc=documents[route];if([...picker.options].some(o=>o.value===route))picker.value=route;}
picker.addEventListener('change',()=>show(picker.value));
document.getElementById('mobile').addEventListener('click',()=>{frame.classList.add('mobile');document.getElementById('mobile').setAttribute('aria-pressed','true');document.getElementById('desktop').setAttribute('aria-pressed','false');});
document.getElementById('desktop').addEventListener('click',()=>{frame.classList.remove('mobile');document.getElementById('mobile').setAttribute('aria-pressed','false');document.getElementById('desktop').setAttribute('aria-pressed','true');});
window.addEventListener('message',event=>{if(event.source===frame.contentWindow&&event.data&&event.data.type==='insightacademia-preview-route')show(event.data.route);});
show('index.html');
</script></body></html>'''.replace('DOCUMENTS',encoded)
    target=Path(args.output)
    if not target.is_absolute():target=ROOT/target
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body)
    print(f'Created offline design review: {target} ({target.stat().st_size:,} bytes)')

if __name__=='__main__':main()
