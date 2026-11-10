import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const [,, listFile, outRoot, workerId, nWorkers, doneFile] = process.argv;
const all = fs.readFileSync(listFile,'utf8').split('\n').filter(Boolean);
const urls = all.filter((_,i)=> i % Number(nWorkers) === Number(workerId));
const done = new Set(fs.existsSync(doneFile) ? fs.readFileSync(doneFile,'utf8').split('\n').filter(Boolean) : []);

const nt = await (await fetch("http://localhost:9222/json/new?url=about:blank", {method:'PUT'})).json();
const ws = new WebSocket(nt.webSocketDebuggerUrl);
let id=0; const pending=new Map();
ws.onmessage = ev => { const m=JSON.parse(ev.data); if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id);} };
const cmd=(method,params={})=>new Promise(res=>{const i=++id;pending.set(i,res);ws.send(JSON.stringify({id:i,method,params}));});
await new Promise(r=>ws.onopen=r);
await cmd("Page.enable"); await cmd("Runtime.enable"); await cmd("Network.enable");
await cmd("Page.navigate",{url:"https://elections.nz/"});
for(let i=0;i<30;i++){await new Promise(r=>setTimeout(r,1000));const t=await cmd("Runtime.evaluate",{expression:"document.title",returnByValue:true});const ti=t.result?.result?.value||"";if(ti&&!/Just a moment|Incapsula/i.test(ti))break;}

async function fetchCdp(url, ms=120000){
  const expr = `(async () => {
    const c = new AbortController(); const t = setTimeout(()=>c.abort(), ${ms-5000});
    try {
      const r = await fetch(${JSON.stringify(url)}, {credentials:'include', signal:c.signal});
      const b = new Uint8Array(await r.arrayBuffer());
      clearTimeout(t);
      let s=''; const chunk=0x8000;
      for (let i=0;i<b.length;i+=chunk) s += String.fromCharCode.apply(null, b.subarray(i,i+chunk));
      return JSON.stringify({status:r.status, ct:r.headers.get('content-type'), len:b.length, b64:btoa(s)});
    } catch(e) { clearTimeout(t); return JSON.stringify({status:0, err:String(e)}); }
  })()`;
  const res = await cmd("Runtime.evaluate",{expression:expr,awaitPromise:true,returnByValue:true});
  const raw = res.result?.result?.value;
  if (typeof raw!=='string') return {status:0, err:'EVALFAIL'};
  try { return JSON.parse(raw); } catch { return {status:0, err:'PARSEFAIL'}; }
}

let ok=0, fail=0;
for (const url of urls) {
  if (done.has(url)) continue;
  const fname = decodeURIComponent(url.split('/').pop());
  let saved=false, lastErr='';
  for (let a=1;a<=2 && !saved;a++){
    const j = await fetchCdp(url);
    if (j.status!==200){ lastErr=`http${j.status} ${j.err||''}`; await new Promise(r=>setTimeout(r,2000)); continue; }
    const buf = Buffer.from(j.b64,'base64');
    if (buf.slice(0,300).toString('latin1').toLowerCase().includes('<html') || buf.length<600){ lastErr=`html/challenge ${buf.length}`; await new Promise(r=>setTimeout(r,3000)); continue; }
    const sha=crypto.createHash('sha256').update(buf).digest('hex');
    const dest=path.join(outRoot,sha.slice(0,2),sha.slice(2,4),`${sha}.bin`);
    fs.mkdirSync(path.dirname(dest),{recursive:true});
    if(!fs.existsSync(dest)) fs.writeFileSync(dest,buf);
    fs.writeFileSync(dest+'.json', JSON.stringify({dataset_name:"NZ election funding returns", resource_name:fname, url, format:(fname.split('.').pop()||'').toUpperCase(), size:buf.length, sha256:sha, content_type:j.ct},null,2));
    fs.appendFileSync(doneFile, url+'\n');
    console.log(`[w${workerId}] OK ${fname} ${buf.length}`);
    ok++; saved=true;
  }
  if(!saved){ console.log(`[w${workerId}] FAIL ${fname} ${lastErr}`); fail++; }
}
console.log(`[w${workerId}] done ok=${ok} fail=${fail}`);
ws.close();
