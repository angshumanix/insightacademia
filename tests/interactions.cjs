/* Unit-level behavior checks against the shipped script. Not a browser layout test. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('js/main.js', 'utf8');
function element(props = {}) {
  return Object.assign({ hidden: false, attrs: {}, listeners: {}, firstChild: { textContent: '' },
    setAttribute(k,v) { this.attrs[k]=v; }, getAttribute(k) { return this.attrs[k]; },
    addEventListener(type,fn) { this.listeners[type]=fn; }, focus() { this.focused=true; }
  }, props);
}
const toggle=element(),nav=element(),query=element({value:''}),category=element({value:''}),clear=element(),count=element(),empty=element();
const cards=[element({dataset:{category:'research-literature'},textContent:'Literature review planner'}),element({dataset:{category:'study-skills'},textContent:'Revision planner'}),element({dataset:{category:'essays-reports'},textContent:'Case analysis workbook'})];
const tools=element({dataset:{demo:'true'},querySelector:s=>({'input':query,'select':category,'button':clear}[s])});
const media=element({matches:true});
const document=element({querySelector:s=>({'.menu-toggle':toggle,'#site-nav':nav,'[data-catalogue-tools]':tools,'[data-result-count]':count,'[data-no-results]':empty}[s]),querySelectorAll:()=>cards});
vm.runInNewContext(source,{document,window:{matchMedia:()=>media}});
assert.equal(nav.hidden,true);
toggle.listeners.click();assert.equal(toggle.getAttribute('aria-expanded'),'true');assert.equal(nav.hidden,false);
document.listeners.keydown({key:'Escape'});assert.equal(nav.hidden,true);assert.equal(toggle.focused,true);
toggle.listeners.click();document.listeners.click({target:{closest:()=>null}});assert.equal(nav.hidden,true);
media.matches=false;media.listeners.change();assert.equal(nav.hidden,false);
media.matches=true;media.listeners.change();assert.equal(nav.hidden,true);
query.value='   PLANNER ';query.listeners.input();assert.equal(cards.filter(c=>!c.hidden).length,2);
category.value='research-literature';category.listeners.change();assert.equal(cards.filter(c=>!c.hidden).length,1);
query.value='unmatched';query.listeners.input();assert.equal(empty.hidden,false);assert.match(count.textContent,/0 packs/);
clear.listeners.click();assert.equal(cards.filter(c=>!c.hidden).length,3);assert.equal(empty.hidden,true);assert.equal(query.focused,true);
console.log('Passed menu toggle, Escape/focus, outside click, breakpoint state, search, category, empty state and reset behavior checks.');
