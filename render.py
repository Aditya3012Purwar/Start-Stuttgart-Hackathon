#!/usr/bin/env python3
"""Render the SOCX dashboard - data-less by design.

The page ships with NO precomputed numbers, problems, or answers. It loads to an
empty assistant. Every question hits /api/ask, which reruns the whole 4-agent
system live against the real database, and the result (trace, plain verdict,
evidence, contacts) is rendered here. Design language: the Beyond Records
finance-intelligence look, in English.
"""

from __future__ import annotations

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SOCX - Finance Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#f6f8fb;--surface:#fff;--surface2:#f0f4f8;--ink:#10212f;--muted:#677786;
  --line:#dce5ec;--navy:#102c3b;--navy2:#173f51;--teal:#20a286;--mint:#e7f7f2;
  --amber:#f0a13a;--red:#d75a5a;--shadow:0 12px 35px rgba(16,44,59,.08);--r:18px}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg);color:var(--ink)}
a{color:inherit;text-decoration:none}button,input,textarea{font:inherit}
.app{min-height:100vh;display:grid;grid-template-columns:248px 1fr}
.sidebar{position:sticky;top:0;height:100vh;padding:24px 18px;background:var(--navy);color:#fff;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:11px;padding:4px 8px 24px}
.brand-mark{width:36px;height:36px;border-radius:12px;background:linear-gradient(135deg,#6ce0c1,#20a286);display:grid;place-items:center;font-weight:800;color:var(--navy)}
.brand-name{font-weight:800;letter-spacing:-.02em}
.brand-sub{font-size:11px;color:#a9bbc4;margin-top:2px}
.nav{display:grid;gap:7px}
.nav a{padding:12px 13px;border-radius:12px;display:flex;align-items:center;gap:10px;color:#bed0d8;font-size:14px;cursor:pointer;user-select:none}
.nav a:hover,.nav a.active{background:rgba(255,255,255,.1);color:#fff}
.nav-icon{width:20px;text-align:center}
.sidebar-foot{margin-top:auto;padding:16px 10px;border-top:1px solid rgba(255,255,255,.1);font-size:12px;color:#9db2bc}
.main{min-width:0}
.topbar{height:72px;display:flex;align-items:center;justify-content:space-between;padding:0 34px;
  background:rgba(246,248,251,.92);backdrop-filter:blur(12px);border-bottom:1px solid rgba(220,229,236,.8);position:sticky;top:0;z-index:20}
.top-title{font-weight:700}
.top-actions{display:flex;align-items:center;gap:10px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:8px 11px;border-radius:999px;border:1px solid var(--line);background:#fff;font-size:12px;color:var(--muted)}
.status-dot{width:8px;height:8px;border-radius:50%;background:var(--teal)}
.avatar{width:34px;height:34px;border-radius:50%;background:var(--navy);color:#fff;display:grid;place-items:center;font-size:12px;font-weight:700}
.content{padding:34px;max-width:1200px;margin:0 auto}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:11px;font-weight:800;color:var(--teal)}
h1{font-size:34px;line-height:1.1;letter-spacing:-.04em;margin:8px 0 12px}
h2{font-size:22px;letter-spacing:-.025em;margin:0}h3{font-size:16px;margin:0}
.lead{font-size:15px;line-height:1.6;color:var(--muted);max-width:760px}
.btn{border:0;border-radius:12px;padding:11px 16px;cursor:pointer;font-weight:700;display:inline-flex;align-items:center;justify-content:center;gap:8px}
.btn-primary{background:var(--teal);color:#fff}.btn-ghost{background:transparent;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:20px;box-shadow:0 4px 16px rgba(16,44,59,.035)}
.section{margin-top:24px}
.section-sub{color:var(--muted);font-size:13px;margin-top:5px}
.badge{font-size:11px;font-weight:700;padding:5px 8px;border-radius:999px;background:var(--mint);color:#0d7e67}
.badge.warn{background:#fff0dd;color:#a66815}.badge.danger{background:#fdeaea;color:#b33b3b}.badge.muted{background:var(--surface2);color:var(--muted)}
.assistant-shell{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:18px}
.chat-card{display:flex;flex-direction:column}
.composer{display:flex;gap:8px;align-items:center}
.mic{width:48px;height:48px;border-radius:50%;flex:0 0 auto;border:0;cursor:pointer;background:linear-gradient(135deg,#6ce0c1,var(--teal));color:#fff;font-size:20px;display:grid;place-items:center;transition:transform .1s}
.mic:active{transform:scale(.94)}.mic.listening{animation:pulse 1.3s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(32,162,134,.5)}70%{box-shadow:0 0 0 15px rgba(32,162,134,0)}100%{box-shadow:0 0 0 0 rgba(32,162,134,0)}}
.composer input{flex:1;border:1px solid var(--line);border-radius:13px;padding:12px 14px;outline:none;background:#fff}
.iconbtn{width:42px;height:42px;border-radius:12px;border:1px solid var(--line);background:#fff;color:var(--muted);cursor:pointer;flex:0 0 auto}
.status-line{color:var(--muted);font-size:12.5px;margin:12px 2px 0;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pill{font-size:10px;font-weight:800;padding:3px 8px;border-radius:999px;text-transform:uppercase;letter-spacing:.5px}
.pill.on{background:var(--mint);color:#0d7e67}.pill.off{background:var(--surface2);color:var(--muted)}
.empty{margin-top:18px;padding:34px;border:1px dashed var(--line);border-radius:16px;text-align:center;color:var(--muted)}
.empty .big{font-size:40px}
.resp{margin-top:16px;display:none}.resp.show{display:block}
.heard{color:var(--muted);font-size:12.5px;margin-bottom:12px}.heard b{color:var(--ink)}
.trace{display:flex;flex-direction:column;gap:2px;margin-bottom:14px}
.tstep{display:flex;gap:12px;align-items:flex-start;padding:11px 0;border-bottom:1px solid var(--line);opacity:0;transform:translateY(4px);transition:opacity .35s,transform .35s}
.tstep:last-child{border-bottom:0}.tstep.in{opacity:1;transform:none}
.tnum{width:26px;height:26px;border-radius:50%;flex:0 0 auto;display:grid;place-items:center;font-size:12px;font-weight:800;color:#fff;background:#b9c6cf}
.tstep.done .tnum{background:linear-gradient(135deg,#6ce0c1,var(--teal))}
.tstep .who{font-weight:800;font-size:12.5px}
.tstep .did{color:var(--muted);font-size:12.5px;line-height:1.45;word-break:break-word}
.tstep .did code{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;background:var(--surface2);padding:1px 5px;border-radius:5px}
.tstep .spin{width:14px;height:14px;border:2px solid var(--line);border-top-color:var(--teal);border-radius:50%;animation:spin .7s linear infinite;margin-top:5px}
@keyframes spin{to{transform:rotate(360deg)}}
.verdictcard{border-radius:16px;padding:18px 20px;border:1px solid var(--line);background:var(--surface2)}
.verdictcard.problem{border-left:4px solid var(--red)}.verdictcard.info,.verdictcard.ok{border-left:4px solid var(--teal)}
.verdictcard .hl{font-size:19px;font-weight:800;line-height:1.35;letter-spacing:-.02em}
.block{margin-top:14px}.block .lab{font-size:10.5px;font-weight:800;text-transform:uppercase;letter-spacing:.6px}
.block.prob .lab{color:var(--red)}.block.fix .lab{color:var(--teal)}
.block p{margin:4px 0 0;font-size:13.5px;line-height:1.6}
.contacts{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
.ccard{flex:1;min-width:220px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.ccard .cn{font-weight:800}.ccard .cd{color:var(--muted);font-size:12px}
.ccard .cw{color:var(--muted);font-size:11.5px;margin-top:4px;line-height:1.4}
.ccard .cbtns{margin-top:10px}
.ccard button{font-size:11px;border-radius:8px;padding:6px 10px;border:1px solid var(--line);background:var(--surface2);color:var(--ink);cursor:pointer}
.meta{margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.speakbtn{background:#fff;border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:5px 10px;font-size:11px;cursor:pointer}
.callout{border-left:4px solid var(--teal);background:var(--mint);border-radius:0 14px 14px 0;padding:15px 17px;color:#20594d;font-size:13px;line-height:1.55}
.trace-item{padding:12px 0;border-bottom:1px solid var(--line)}.trace-item:last-child{border-bottom:0}
.trace-item b{display:block;font-size:12.5px}.trace-item span{font-size:12px;color:var(--muted);line-height:1.45}
.table-wrap{overflow:auto;margin-top:14px}
.table{width:100%;border-collapse:collapse;min-width:420px}
.table th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:10px;border-bottom:1px solid var(--line)}
.table td{padding:11px 10px;border-bottom:1px solid #edf2f5;font-size:13px}
.table td.num,.table th.num{text-align:right;font-variant-numeric:tabular-nums}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0 4px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.kpi .kv{font-size:22px;font-weight:800;letter-spacing:-.03em;color:var(--navy);font-variant-numeric:tabular-nums}
.kpi .kl{font-size:12px;font-weight:700;margin-top:4px}
.kpi .kh{font-size:11px;color:var(--muted);margin-top:3px;line-height:1.35}
.viz-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:14px}
.chart-card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.chart-card h3{font-size:14px;margin:0 0 4px}
.chart-box{position:relative;height:240px;margin-top:8px}
.chart-box.tall{height:280px}
.ov-kpis{margin-top:18px}
.ov-note{margin-top:16px;font-size:12.5px;color:var(--muted);line-height:1.5}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}
.chips button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 12px;font-size:12px;cursor:pointer;color:var(--ink)}
.chips button:hover{border-color:var(--teal);color:var(--teal)}
pre{background:var(--surface2);border:1px solid var(--line);border-radius:10px;padding:12px;overflow:auto;font-size:11.5px;white-space:pre-wrap;color:var(--ink)}
details summary{cursor:pointer;color:var(--muted);font-size:12px;font-weight:700}
.panel{display:none}.panel.active{display:block}
.mobile-menu{display:none}
.footer-note{font-size:11px;color:var(--muted);margin-top:28px}
@media(max-width:1100px){.assistant-shell{grid-template-columns:1fr}}
@media(max-width:760px){.app{display:block}.sidebar{position:fixed;z-index:50;transform:translateX(-100%);transition:.2s;width:250px}
  .sidebar.open{transform:none}.topbar{padding:0 18px}.mobile-menu{display:inline-flex}.content{padding:22px 16px}h1{font-size:28px}.chip.hide-mobile{display:none}}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar" id="sidebar">
    <div class="brand"><div class="brand-mark">SC</div>
      <div><div class="brand-name">SOCX</div><div class="brand-sub">System of Context</div></div></div>
    <nav class="nav" id="nav">
      <a data-p="ask" data-title="Finance Assistant" class="active"><span class="nav-icon">&#10022;</span>Ask</a>
      <a data-p="overview" data-title="Live picture"><span class="nav-icon">&#128202;</span>Overview</a>
      <a data-p="how" data-title="How it works"><span class="nav-icon">&#9781;</span>How it works</a>
      <a data-p="src" data-title="Data sources"><span class="nav-icon">&#9783;</span>Data sources</a>
    </nav>
    <div class="sidebar-foot">Purchase-to-Pay<br>Live &middot; no cached answers</div>
  </aside>
  <main class="main">
    <header class="topbar">
      <button class="btn btn-ghost mobile-menu" onclick="document.getElementById('sidebar').classList.toggle('open')">&#9776;</button>
      <div class="top-title" id="topTitle">Finance Assistant</div>
      <div class="top-actions"><div class="chip hide-mobile"><span class="status-dot"></span>Live &middot; reruns per question</div><div class="avatar">AP</div></div>
    </header>
    <div class="content">
      <section class="panel active" id="ask">
        <div class="eyebrow">Ask your data</div>
        <h1>Finance Assistant</h1>
        <p class="lead">Ask any Purchase-to-Pay question in plain words - by voice or text. SOCX reruns its four agents live against the real database, then shows the answer as a briefing <b>and as charts</b> a finance team can scan. Nothing is pre-answered.</p>
        <div class="chips">
          <button type="button" data-q="Which supplier invoices are currently stuck, how much money is tied up, and why?">North star</button>
          <button type="button" data-q="Which five vendors have the highest value tied up in stuck invoices?">Top vendors</button>
          <button type="button" data-q="How many invoices failed the three-way match?">Failed match</button>
          <button type="button" data-q="Which vendors are blocked?">Blocked vendors</button>
        </div>
        <div class="assistant-shell">
          <article class="card chat-card">
            <div class="composer">
              <button class="mic" id="mic" title="Ask by voice">&#127908;</button>
              <input id="dockq" placeholder="e.g. How many invoices are stuck in checking?">
              <button class="btn btn-primary" id="dockask">Ask</button>
              <button class="iconbtn" id="stopspk" title="Stop speaking">&#128266;</button>
            </div>
            <div class="status-line" id="status">Tap the mic and ask, or type. <span class="pill off" id="llmpill">checking&hellip;</span></div>
            <div class="empty" id="empty"><div class="big">&#128173;</div>Ask a question to start. The four agents run only when you ask - there is nothing pre-loaded here.</div>
            <div class="resp" id="resp"></div>
          </article>
          <aside class="card">
            <h3>How the answer forms</h3>
            <div class="trace-item"><b>1 &middot; Context Miner</b><span>Reads the emails, tickets and dictionary for your topic.</span></div>
            <div class="trace-item"><b>2 &middot; Analyst</b><span>Writes SQL for your question and runs it live on the real database.</span></div>
            <div class="trace-item"><b>3 &middot; Anomaly Sentinel</b><span>Checks recent documents against what history says is normal.</span></div>
            <div class="trace-item"><b>4 &middot; Advisor</b><span>Explains it plainly and names who to contact.</span></div>
            <div class="callout" style="margin-top:16px">A good finance answer is a glass box: you see not just the result, but how it was reached.</div>
          </aside>
        </div>
      </section>

      <section class="panel" id="overview">
        <div class="eyebrow">Live picture</div>
        <h1>What the books look like right now</h1>
        <p class="lead">A snapshot computed live from the ERP replica — not a cached slide. Status meanings come from the change log, not the 2018 catalogue. Open any chart’s question on Ask if you want the agents to walk you through it.</p>
        <div id="ovroot"><div class="empty"><div class="big">&#128202;</div>Loading the live picture…</div></div>
      </section>

      <section class="panel" id="how">
        <div class="eyebrow">Method</div><h1>How it works</h1>
        <p class="lead">SOCX is a team of four LLM agents that coordinate on every question - they are not a set of canned answers and they are not trained on any fixed list of questions. Each agent reads the real documents itself (starting with the DATABASE.md data model) and they talk to each other: when one needs more information, it asks a teammate, who gathers it, and only then do they converge on a detailed answer.</p>
        <div class="section card"><h3>The four agents coordinate, every time you ask</h3>
          <div class="trace-item"><b>Agent 1 &middot; Context Miner</b><span>Reads DATABASE.md, the glossary, the process notes, the emails and the tickets, and briefs the team on what the question means and which rules and traps apply.</span></div>
          <div class="trace-item"><b>Agent 2 &middot; Data Analyst</b><span>Writes and runs read-only SQL live, in a loop - exploring and drilling in across all tables. If a term is unclear it asks Agent 1 to clarify before it trusts a number.</span></div>
          <div class="trace-item"><b>Agent 3 &middot; Verifier</b><span>Stress-tests Agent 2's result - right set? a known trap? anything anomalous versus history? - and can request further queries and have them run.</span></div>
          <div class="trace-item"><b>Agent 4 &middot; Advisor</b><span>Synthesises the team's work into a detailed, plain-English explanation: what the number means, how it was derived, why it matters, the fix, and who to contact.</span></div>
        </div>
        <div class="callout section">Every number is computed live from the real production database and shown with the exact queries that produced it. The whole chain - reading the documents, writing the SQL, verifying, explaining - is done by the LLM agents themselves. If a question has no problem behind it, the team simply answers; it does not invent one.</div>
      </section>

      <section class="panel" id="src">
        <div class="eyebrow">Provenance</div><h1>Data sources</h1>
        <p class="lead">Everything the agents reason over is the company's own real material. No mock data.</p>
        <div class="section card">
          <div class="trace-item"><b>data/erp_legacy.db</b><span>The real production extract - 1,274 tables - opened read-only.</span></div>
          <div class="trace-item"><b>data/incoming_documents.jsonl</b><span>31 real recent documents with their processing history (for the anomaly check).</span></div>
          <div class="trace-item"><b>context/emails.md &middot; tickets.jsonl</b><span>Accounts Payable / Procurement correspondence and support tickets - where the trap-rules and the real contacts come from.</span></div>
          <div class="trace-item"><b>context/GLOSSARY.md &middot; PROCESS.md</b><span>The data dictionary (partly outdated) and the process description.</span></div>
        </div>
      </section>
      <div class="footer-note">SOCX &middot; live, provenance-first. Nothing on this page is pre-computed - it all comes from the agents running on your question.</div>
    </div>
  </main>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
const $ = (s,el=document)=>el.querySelector(s);
const esc = s => String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function activateTab(pid){
  document.querySelectorAll('#nav a').forEach(a=>{const on=a.dataset.p===pid;a.classList.toggle('active',on);if(on)$('#topTitle').textContent=a.dataset.title;});
  document.querySelectorAll('.panel').forEach(x=>x.classList.toggle('active',x.id===pid));
  document.getElementById('sidebar').classList.remove('open');window.scrollTo({top:0,behavior:'smooth'});
}
document.querySelectorAll('#nav a').forEach(a=>a.onclick=()=>activateTab(a.dataset.p));
function tableHTML(cols,rows){
  const num=i=>rows.every(r=>r[i]===null||!isNaN(r[i]));
  let h='<div class="table-wrap"><table class="table"><thead><tr>'+cols.map((c,i)=>`<th class="${num(i)?'num':''}">${esc(c)}</th>`).join('')+'</tr></thead><tbody>';
  h+=rows.map(r=>'<tr>'+r.map((v,i)=>`<td class="${num(i)?'num':''}">${v===null?'-':esc(typeof v==='number'&&!Number.isInteger(v)?v.toLocaleString(undefined,{maximumFractionDigits:2}):v)}</td>`).join('')+'</tr>').join('');
  return h+'</tbody></table></div>';}

// ---- voice + live reasoning ----
const mic=$('#mic'),statusEl=$('#status'),resp=$('#resp'),empty=$('#empty');
fetch('/api/health').then(r=>r.json()).then(d=>{const p=$('#llmpill');
  p.className='pill '+(d.llm?'on':'off');
  p.textContent=d.llm?('agent team live: '+d.model):'agents idle - add OpenAI key to .env';
}).catch(()=>{const p=$('#llmpill');p.className='pill off';p.textContent='server offline';});

let voices=[];function loadVoices(){voices=window.speechSynthesis?speechSynthesis.getVoices():[];}
if(window.speechSynthesis){loadVoices();speechSynthesis.onvoiceschanged=loadVoices;}
function speak(t){if(!window.speechSynthesis||!t)return;speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(String(t).replace(/EUR/g,'euros'));u.rate=1.03;
  const v=voices.find(v=>/en-GB|en-US/.test(v.lang))||voices[0];if(v)u.voice=v;speechSynthesis.speak(u);}
$('#stopspk').onclick=()=>window.speechSynthesis&&speechSynthesis.cancel();

let timers=[];
function render(P,q){
  timers.forEach(clearTimeout);timers=[];empty.style.display='none';resp.classList.add('show');
  const trace=P.trace||[];
  let h='<div class="heard">You asked: <b>'+esc(q)+'</b></div><div class="trace">';
  trace.forEach((s,i)=>{const isSql=/SELECT|WITH/i.test(s.detail)&&s.detail.length>40;
    h+=`<div class="tstep" id="ts${i}"><div class="tnum">${i+1}</div>
      <div style="flex:1"><div class="who">${esc(s.agent)}</div>
      <div class="did">${esc(s.action)} &mdash; ${isSql?('<code>'+esc(s.detail)+'</code>'):esc(s.detail)}</div></div>
      <div class="spin" id="sp${i}"></div></div>`;});
  h+='</div><div id="verdict"></div>';resp.innerHTML=h;
  trace.forEach((s,i)=>{timers.push(setTimeout(()=>{const el=$('#ts'+i);el.classList.add('in');
    timers.push(setTimeout(()=>{el.classList.add('done');const sp=$('#sp'+i);if(sp)sp.remove();
      if(i===trace.length-1)showVerdict(P,q);},480));},i*560));});
  if(!trace.length)showVerdict(P,q);}

function contactCard(c){const src=c.source?`<div class="cw" style="opacity:.85">Source: ${esc(c.source)}</div>`:'';
  return `<div class="ccard"><div class="cn">${esc(c.person)}</div><div class="cd">${esc(c.dept)}</div>
    <div class="cw">${esc(c.why||'')}</div>${src}<div class="cbtns"><button onclick='window.__copyBrief()'>Copy briefing</button></div></div>`;}

function anomalyCards(list){
  return list.map(d=>`<div class="card section"><div style="display:flex;justify-content:space-between;gap:10px">
    <div><b>${esc(d.doc_id)}</b> &middot; <span class="section-sub" style="display:inline">${esc(d.vendor||'')}</span></div>
    <span class="badge ${d.verdict==='critical'?'danger':d.verdict==='high'?'warn':'muted'}">${esc(d.verdict)}</span></div>
    ${d.flags.map(f=>`<div class="trace-item"><b>${esc(f.message)}</b><span>Why: ${esc(f.base_rate)}</span></div>`).join('')}</div>`).join('');}

function paras(t){return String(t||'').split(/\n\n+/).map(p=>`<p>${esc(p)}</p>`).join('');}

const PAL=['#20a286','#173f51','#f0a13a','#d75a5a','#4c8dff','#7c5cbf','#5aa7a7','#102c3b'];
window.__charts=window.__charts||[];
function killCharts(prefix){
  window.__charts=window.__charts.filter(c=>{
    const id=c.canvas&&c.canvas.id||'';
    if(!prefix||id.startsWith(prefix)){try{c.destroy();}catch(e){} return false;}
    return true;
  });
}
function kpiHTML(list){
  if(!list||!list.length)return '';
  return '<div class="kpi-grid">'+list.map(k=>`<div class="kpi"><div class="kv">${esc(k.display)}</div><div class="kl">${esc(k.label)}</div>${k.hint?`<div class="kh">${esc(k.hint)}</div>`:''}</div>`).join('')+'</div>';
}
function chartShell(charts,prefix){
  if(!charts||!charts.length)return '';
  return '<div class="viz-grid">'+charts.map(c=>{
    const id=prefix+c.id;
    const tall=c.type==='hbar'?' tall':'';
    return `<div class="chart-card"><h3>${esc(c.title)}</h3><div class="section-sub">${esc(c.subtitle||'')}</div><div class="chart-box${tall}"><canvas id="${esc(id)}"></canvas></div></div>`;
  }).join('')+'</div>';
}
function tickFmt(v){
  const n=Number(v); if(!isFinite(n))return v;
  if(Math.abs(n)>=1e6)return (n/1e6).toFixed(1)+'M';
  if(Math.abs(n)>=1e4)return (n/1e3).toFixed(0)+'k';
  return n.toLocaleString();
}
function paintCharts(charts,prefix){
  if(!window.Chart||!charts)return;
  charts.forEach(c=>{
    const el=document.getElementById(prefix+c.id);
    if(!el)return;
    const ds=c.datasets||[{label:'Value',data:[]}];
    const horiz=c.type==='hbar';
    const doughnut=c.type==='doughnut';
    const cfg={
      type:doughnut?'doughnut':horiz?'bar':'bar',
      data:{labels:c.labels,datasets:ds.map((d,j)=>({
        label:d.label||'Value',data:d.data,
        backgroundColor:doughnut?PAL:PAL[j%PAL.length],
        borderWidth:0,borderRadius:doughnut?0:6,maxBarThickness:36
      }))},
      options:{
        indexAxis:horiz?'y':'x',
        responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:doughnut||ds.length>1,position:'bottom',labels:{boxWidth:10,font:{size:11}}},
          tooltip:{callbacks:{label:ctx=>{
            const v=ctx.raw; const lab=ctx.dataset.label||'';
            const n=Number(v);
            if(/eur|value|amount|cash/i.test(lab+c.title)&&Math.abs(n)>=1000)
              return lab+': '+(Math.abs(n)>=1e6?(n/1e6).toFixed(1)+'M EUR':n.toLocaleString(undefined,{maximumFractionDigits:0})+' EUR');
            return lab+': '+(Number.isInteger(n)?n.toLocaleString():n.toLocaleString(undefined,{maximumFractionDigits:2}));
          }}}},
        scales:doughnut?{}:{
          x:{grid:{color:'#edf2f5'},ticks:{font:{size:11},maxRotation:0,callback:function(v){return horiz?tickFmt(v):this.getLabelForValue(v);}}},
          y:{grid:{color:'#edf2f5'},beginAtZero:true,ticks:{font:{size:11},callback:function(v){return horiz?this.getLabelForValue(v):tickFmt(v);}}}
        }
      }
    };
    window.__charts.push(new Chart(el,cfg));
  });
}
function visualsHTML(V,prefix){
  if(!V||(!(V.kpis&&V.kpis.length)&&!(V.charts&&V.charts.length)))return '';
  return '<div class="block"><div class="lab" style="color:var(--teal)">The picture</div>'+kpiHTML(V.kpis)+chartShell(V.charts,prefix)+'</div>';
}

function showVerdict(P,q){
  const st=P.status||'info';
  killCharts('ans-');
  let h=`<div class="verdictcard ${st}"><div class="hl">${esc(P.headline||'')}</div>`;
  if(P.explanation)h+=`<div class="block"><div class="lab" style="color:var(--muted)">What this means &amp; how we got it</div>${paras(P.explanation)}</div>`;
  h+=visualsHTML(P.visuals,'ans-');
  if(P.table&&P.table.rows&&P.table.rows.length)h+=tableHTML(P.table.columns,P.table.rows);
  if(P.anomalies&&P.anomalies.length)h+='<div class="section">'+anomalyCards(P.anomalies)+'</div>';
  if(P.problem)h+=`<div class="block prob"><div class="lab">The problem</div>${paras(P.problem)}</div>`;
  if(P.fix)h+=`<div class="block fix"><div class="lab">How to fix it</div>${paras(P.fix)}</div>`;
  if(P.contacts&&P.contacts.length)h+=`<div class="block"><div class="lab" style="color:var(--teal)">Who to contact</div><div class="contacts">${P.contacts.map(contactCard).join('')}</div></div>`;
  const mode=P.mode||'grounded';
  h+=`<div class="meta"><span class="pill ${mode==='llm'?'on':'off'}">${mode==='llm'?'AI reasoning':'schema engine'}</span>`;
  if(P.evidence&&P.evidence.length)h+=`<button class="speakbtn" onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden">Show the proof</button><div hidden style="width:100%;margin-top:8px"><pre>${esc(P.evidence.map(e=>(e.label?e.label+': ':'')+(e.note||'')+(e.sql?'\n'+e.sql:'')).join('\n\n'))}</pre></div>`;
  h+=`<button class="speakbtn" onclick='window.__replay()'>&#128266; Replay</button></div></div>`;
  $('#verdict').innerHTML=h;
  paintCharts((P.visuals&&P.visuals.charts)||[],'ans-');
  window.__replay=()=>speak(P.spoken||P.headline||'');
  window.__copyBrief=()=>{const t='SOCX briefing\nQuestion: '+q+'\n\n'+(P.headline||'')+'\n\n'+(P.problem?('Problem: '+P.problem+'\n\n'):'')+(P.fix?('Fix: '+P.fix):'');navigator.clipboard&&navigator.clipboard.writeText(t);};
  speak(P.spoken||P.headline||'');}

function handle(q){
  if(!q||!q.trim())return;$('#dockq').value='';window.speechSynthesis&&speechSynthesis.cancel();
  empty.style.display='none';resp.classList.add('show');
  statusEl.innerHTML='The four agents are working on it&hellip;';
  resp.innerHTML='<div class="heard">You asked: <b>'+esc(q)+'</b></div><div class="did" style="color:var(--muted)">Thinking&hellip; (running SQL live)</div>';
  fetch('/api/ask?q='+encodeURIComponent(q)).then(r=>r.json())
    .then(P=>{statusEl.textContent='Ask me anything else - tap the mic or type.';render(P,q);})
    .catch(()=>{resp.innerHTML='<div class="verdictcard problem"><div class="hl">The server is not reachable.</div><p class="block">Start it with <code>PORT=8123 python serve.py</code> and reload.</p></div>';});}
$('#dockask').onclick=()=>handle($('#dockq').value);
$('#dockq').onkeydown=e=>{if(e.key==='Enter')handle($('#dockq').value);};
document.querySelectorAll('.chips button').forEach(b=>b.onclick=()=>{activateTab('ask');handle(b.dataset.q);});

let ovLoaded=false;
function loadOverview(){
  if(ovLoaded)return;
  const root=$('#ovroot');
  fetch('/api/overview').then(r=>r.json()).then(V=>{
    ovLoaded=true;
    killCharts('ov-');
    root.innerHTML='<div class="ov-kpis">'+kpiHTML(V.kpis)+'</div>'+chartShell(V.charts,'ov-')+
      (V.note?`<p class="ov-note">${esc(V.note)}</p>`:'');
    paintCharts(V.charts,'ov-');
  }).catch(()=>{root.innerHTML='<div class="empty">Could not load the live picture. Is the server running?</div>';});
}
const _activate=activateTab;
activateTab=function(pid){
  _activate(pid);
  if(history.replaceState)history.replaceState(null,'','#'+pid);
  if(pid==='overview')loadOverview();
};
if(/^#(ask|overview|how|src)$/.test(location.hash))activateTab(location.hash.slice(1));

const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!SR){mic.style.opacity=.6;mic.onclick=()=>{statusEl.textContent='This browser has no speech recognition - please type. (Chrome supports voice.)';$('#dockq').focus();};}
else{const rec=new SR();rec.lang='en-US';rec.interimResults=true;rec.continuous=false;let listening=false,finalq='';
  mic.onclick=()=>{if(listening){rec.stop();return;}window.speechSynthesis&&speechSynthesis.cancel();finalq='';try{rec.start();}catch(e){}};
  rec.onstart=()=>{listening=true;mic.classList.add('listening');statusEl.textContent='Listening... ask your question.';};
  rec.onerror=e=>{statusEl.textContent='Microphone error: '+e.error+'. You can type instead.';};
  rec.onend=()=>{listening=false;mic.classList.remove('listening');if(finalq.trim()){$('#dockq').value=finalq.trim();handle(finalq.trim());}};
  rec.onresult=e=>{let t='';for(let i=0;i<e.results.length;i++)t+=e.results[i][0].transcript;finalq=t;statusEl.textContent='Heard: "'+t+'"';};}
</script>
</body>
</html>
"""


def build_dashboard(path: str) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(TEMPLATE)
    return path
