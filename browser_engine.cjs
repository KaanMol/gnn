// Isolated website runtime. Only fixed sensory/control commands cross this boundary.
const {chromium}=require(process.env.GRAPH_PLAYWRIGHT || 'playwright');
const fs=require('fs');const readline=require('readline');const dns=require('dns').promises;const net=require('net');
let browser,context,page,nodes=new Map();
const shot=process.env.GRAPH_BROWSER_SHOT;
function publicIP(ip){if(net.isIP(ip)===4){const a=ip.split('.').map(Number);return !(a[0]===0||a[0]===10||a[0]===127||a[0]>=224||(a[0]===169&&a[1]===254)||(a[0]===172&&a[1]>=16&&a[1]<=31)||(a[0]===192&&a[1]===168)||(a[0]===100&&a[1]>=64&&a[1]<=127)||(a[0]===198&&[18,19].includes(a[1])))}return net.isIP(ip)===6&&!/^(::|fc|fd|fe[89ab])/i.test(ip)}
async function allowed(url){try{const u=new URL(url);if(!['http:','https:'].includes(u.protocol)||u.username||u.password||u.port&&!['80','443'].includes(u.port))return false;const addresses=await dns.lookup(u.hostname,{all:true});return addresses.length>0&&addresses.every(a=>publicIP(a.address));}catch{return false}}
async function start(){if(page)return page;browser=await chromium.launch({headless:true,executablePath:process.env.GRAPH_BROWSER_EXECUTABLE||undefined});context=await browser.newContext({viewport:{width:1100,height:750},acceptDownloads:false,serviceWorkers:'block'});
 await context.route('**/*',async route=>{if(await allowed(route.request().url()))await route.continue();else await route.abort()});
 if(context.routeWebSocket)await context.routeWebSocket('**/*',ws=>ws.close());
 page=await context.newPage();page.setDefaultTimeout(12000);page.on('dialog',d=>d.dismiss());context.on('page',p=>{if(p!==page)p.close()});return page;}
async function observe(){
 // IDs refer to this observation. The agent receives data, never evaluate access.
 const result=await page.evaluate(()=>{const out=[];const refs=[];const skip=new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);let truncated=false;
 function visit(n,parent,ancestors){if(out.length>=1800){truncated=true;return}if(n.nodeType===1&&skip.has(n.tagName))return;if(n.nodeType===3&&!n.textContent.trim())return;if(n.nodeType!==1&&n.nodeType!==3)return;
 const id=out.length;const attrs={};if(n.nodeType===1){for(const a of Array.from(n.attributes).slice(0,30))if(!a.name.startsWith('on'))attrs[a.name]=a.value.slice(0,2000);for(const k of ['href','action'])if(attrs[k]){try{attrs[k]=new URL(attrs[k],document.baseURI).href}catch{}}}
 const raw=n.nodeType===3?n.textContent.slice(0,6000):'';out.push({id,parent,ancestors:ancestors.slice(-40),tag:n.nodeType===3?'#text':n.tagName.toLowerCase(),attrs,text:raw.replace(/\s+/g,' ').trim().slice(0,2000),raw_text:raw});refs.push(n);for(const c of n.childNodes)visit(c,id,[...ancestors,id]);}
 visit(document.documentElement,-1,[]);window.__graphBrowserNodes=refs;return {url:location.href,title:document.title,nodes:out,truncated,mode:'rendered-dom'};});
 result.retrieved_at=new Date().toISOString();await page.screenshot({path:shot+'.tmp',type:'png'});fs.renameSync(shot+'.tmp',shot);return result;
}
async function element(id){if(!Number.isInteger(id)||id<0)throw Error('Choose a node from the current DOM observation.');const h=await page.evaluateHandle(id=>window.__graphBrowserNodes?.[id],id);const e=h.asElement();if(!e)throw Error('This node is no longer an element on the page. Observe again.');return e;}
async function command(c){await start();const a=c.args||{};
 if(c.action==='open'){if(!await allowed(a.url))throw Error('Use a public HTTP(S) page.');await page.goto(a.url,{waitUntil:'domcontentloaded',timeout:20000});}
 else if(c.action==='click')await(await element(a.id)).click();
 else if(c.action==='type')await(await element(a.id)).fill(a.text);
 else if(c.action==='submit'){const e=await element(a.id);await e.evaluate(n=>{if(n.tagName!=='FORM')throw Error('Choose a form node.');n.requestSubmit()});}
 else if(c.action==='back')await page.goBack({waitUntil:'domcontentloaded'});
 else if(c.action==='forward')await page.goForward({waitUntil:'domcontentloaded'});
 else if(c.action==='scroll')await page.mouse.wheel(0,Math.max(-1500,Math.min(1500,a.dy)));
 else if(c.action==='click_at')await page.mouse.click(a.x,a.y);
 else if(c.action==='type_text')await page.keyboard.insertText(a.text);
 else if(c.action==='press'){if(!['Enter','Tab','Backspace','Escape','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(a.key))throw Error('Unsupported key.');await page.keyboard.press(a.key);}
 else if(c.action!=='observe')throw Error('Unknown browser control.');
 await new Promise(r=>setTimeout(r,200));return observe();}
module.exports={start,command,close:()=>browser?.close()};
if(require.main===module){
let queue=Promise.resolve();readline.createInterface({input:process.stdin}).on('line',line=>{queue=queue.then(async()=>{try{const c=JSON.parse(line);const result=await command(c);process.stdout.write(JSON.stringify({ok:true,result})+'\n')}catch(e){process.stdout.write(JSON.stringify({ok:false,error:String(e.message||e)})+'\n')}})});
process.on('SIGTERM',()=>{if(browser)browser.close().finally(()=>process.exit());else process.exit()});process.stdin.on('end',()=>{if(browser)browser.close().finally(()=>process.exit())});

}
