/* Genuine local Chromium checks. Requires Playwright + Chromium in the QA environment only. */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs');const assert=require('node:assert/strict');
(async()=>{
 const dir='.preview/qa';fs.mkdirSync(dir,{recursive:true});
 const base=(process.env.SITE_BASE||'http://127.0.0.1:8876').replace(/\/$/,'');
 const server=process.env.SITE_BASE?null:spawn('python',['-m','http.server','8876','--bind','127.0.0.1','--directory','.preview'],{stdio:'ignore'});
 let browser;
 try{
 browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});
 const results=[];const errors=[];
  for(let i=0;i<30;i++){try{await fetch(base+'/');break}catch{await new Promise(r=>setTimeout(r,100));}}
  const context=await browser.newContext();const page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  const paths=['index.html','study-packs.html','packs/case-analysis-workbook.html','faq.html','contact.html','how-to-order.html'];
  for(const width of [1440,768,390,320]){
   await page.setViewportSize({width,height:900});
   for(const path of paths){
    await page.goto(base+'/'+path);await page.locator('h1').waitFor();
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
    assert.equal(overflow,false,`${width} ${path}: horizontal overflow`);
    const wrong=await page.locator('a[href*="t.me"]').evaluateAll(as=>as.filter(a=>a.href!=='https://t.me/InsightAcademiaPacks').length);assert.equal(wrong,0);
    if(path.startsWith('packs/')){assert.equal(await page.locator('.product-price').count(),0);assert.match(await page.locator('.status-label').innerText(),/not a complete commercial study pack/);await page.locator('.sample-preview img').scrollIntoViewIfNeeded();await page.waitForFunction(()=>{const i=document.querySelector('.sample-preview img');return i&&i.complete&&i.naturalWidth>0;});}
    results.push(`${width}px ${path}: loaded, no horizontal overflow, exact Telegram destinations`);
    if((width===1440||width===390)&&['index.html','study-packs.html','packs/case-analysis-workbook.html'].includes(path))await page.screenshot({path:`${dir}/${width}-${path.replaceAll('/','-')}.png`,fullPage:true});
   }
   await page.goto(base+'/study-packs.html');
   await page.locator('#pack-search').fill('planner');assert.equal(await page.locator('[data-product]:visible').count(),2);
   await page.locator('#pack-category').selectOption('research-literature');assert.equal(await page.locator('[data-product]:visible').count(),1);
   await page.locator('#pack-search').fill('no-match-xyz');assert.equal(await page.locator('[data-no-results]').isVisible(),true);
   await page.getByRole('button',{name:'Clear filters'}).click();assert.equal(await page.locator('[data-product]:visible').count(),3);
   if(width<=900){const menu=page.locator('.menu-toggle');await menu.click();assert.equal(await menu.getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');assert.equal(await menu.getAttribute('aria-expanded'),'false');assert.equal(await menu.evaluate(e=>e===document.activeElement),true);await menu.click();await menu.click();assert.equal(await page.locator('#site-nav').isVisible(),false);}
   await page.goto(base+'/faq.html');const summary=page.locator('summary').first();await summary.focus();await page.keyboard.press('Enter');assert.equal(await page.locator('details').first().getAttribute('open'),'');
   results.push(`${width}px: search, category, zero results, reset, FAQ keyboard${width<=900?', menu close/Escape/focus return':''} passed`);
  }
  await page.goto(base+'/');await page.keyboard.press('Tab');assert.equal(await page.locator('.skip-link').evaluate(e=>e===document.activeElement),true);await page.keyboard.press('Enter');assert.equal(await page.locator('main').evaluate(e=>e===document.activeElement),true);
  const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:320,height:900}});const nj=await nojs.newPage();
  await nj.goto(base+'/study-packs.html');assert.equal(await nj.locator('#site-nav').isVisible(),true);assert.equal(await nj.locator('[data-product]').count(),3);assert.equal(await nj.locator('[data-catalogue-tools]').isVisible(),false);await nj.locator('.card-body h3 a').first().click();assert.match(await nj.locator('h1').innerText(),/case analysis/);await nj.locator('.sample-preview img').scrollIntoViewIfNeeded();await nj.waitForFunction(()=>{const i=document.querySelector('.sample-preview img');return i&&i.complete&&i.naturalWidth>0;});await nj.goto(base+'/faq.html');await nj.locator('summary').first().click();assert.equal(await nj.locator('details').first().getAttribute('open'),'');
  results.push('320px JavaScript disabled: navigation, catalogue, product link, preview image and native FAQ passed');
  assert.deepEqual(errors,[]);fs.writeFileSync(`${dir}/results.json`,JSON.stringify({browser:await browser.version(),results,errors},null,2));console.log(JSON.stringify({browser:await browser.version(),checks:results.length,errors,screenshots:dir}));
 }finally{if(browser)await browser.close();if(server)server.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
