#!/usr/bin/env python3
"""Assemble web/triage_explorer.html from the template + data/designs.json."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data" / "designs.json").read_text())
DATA_JSON = json.dumps(data, separators=(",", ":"))

HTML = r'''<title>Binder Triage Explorer</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Layout: instrument panel — a control rail drives a live readout (funnel, landscape, shortlist). */
:root{
  --bg:#f4f5f3; --panel:#ffffff; --ink:#15201d; --muted:#5d6b66; --line:#dde3df;
  --accent:#0f8a7e;      /* binding teal */
  --select:#1f6feb;      /* plate-selection blue */
  --pass:#2d8f6f; --reject:#c0523f; --warn:#d98c2b;
  --grid:#e7ece9;
  --font-sans:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  --font-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#10161a; --panel:#182127; --ink:#e7eeeb; --muted:#9aa8a2; --line:#28343a;
  --accent:#36c9b8; --select:#5a9bff; --pass:#4bbd94; --reject:#e0775f; --warn:#e7ad57;
  --grid:#222d33; color-scheme:dark;
}}
:root[data-theme="dark"]{
  --bg:#10161a; --panel:#182127; --ink:#e7eeeb; --muted:#9aa8a2; --line:#28343a;
  --accent:#36c9b8; --select:#5a9bff; --pass:#4bbd94; --reject:#e0775f; --warn:#e7ad57;
  --grid:#222d33; color-scheme:dark;
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--font-sans);line-height:1.5}
.wrap{max-width:1180px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:clamp(20px,4vw,40px)}
h1,h2,h3{text-wrap:balance;line-height:1.15;margin:0}
.eyebrow{font-family:var(--font-mono);font-size:.72rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent);font-weight:600}
h1{font-size:clamp(1.7rem,4.5vw,2.5rem);font-weight:600;letter-spacing:-.01em;margin:.3rem 0 .5rem}
.lede{color:var(--muted);max-width:68ch;font-size:1.02rem}
.tag{font-family:var(--font-mono);font-size:.7rem;color:var(--muted)}

/* funnel pipeline strip */
.pipe{display:flex;flex-wrap:wrap;gap:.5rem;align-items:stretch;margin:1.6rem 0 .4rem}
.stage{flex:1 1 150px;min-width:0;background:var(--panel);border:1px solid var(--line);
  border-radius:12px;padding:.85rem 1rem;position:relative}
.stage .k{font-family:var(--font-mono);font-size:.68rem;letter-spacing:.08em;
  text-transform:uppercase;color:var(--muted)}
.stage .v{font-family:var(--font-mono);font-size:1.9rem;font-weight:600;
  font-variant-numeric:tabular-nums;line-height:1.1;margin-top:.2rem}
.stage .pct{font-family:var(--font-mono);font-size:.76rem;color:var(--muted)}
.stage.s1{border-left:3px solid var(--muted)}
.stage.s2{border-left:3px solid var(--pass)}
.stage.s3{border-left:3px solid var(--select)}
.arrow{display:flex;align-items:center;color:var(--muted);font-size:1.3rem;padding:0 .1rem}
@media (max-width:620px){.arrow{display:none}}

/* two-column: controls + readout */
.cols{display:grid;grid-template-columns:300px 1fr;gap:18px;margin-top:1.4rem;align-items:start}
@media (max-width:820px){.cols{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.15rem}
.card h3{font-size:.96rem;font-weight:600;display:flex;justify-content:space-between;align-items:baseline;gap:.5rem}
.card h3 .sub{font-family:var(--font-mono);font-size:.68rem;color:var(--muted);font-weight:400;letter-spacing:.04em}
.rail{position:sticky;top:max(12px,env(safe-area-inset-top,0px))}
@media (max-width:820px){.rail{position:static}}

.ctl{margin-top:1rem}
.ctl:first-of-type{margin-top:.6rem}
.ctl label{display:flex;justify-content:space-between;align-items:baseline;
  font-size:.82rem;gap:.5rem;margin-bottom:.28rem}
.ctl label .nm{font-weight:500}
.ctl label .val{font-family:var(--font-mono);font-size:.8rem;color:var(--accent);
  font-variant-numeric:tabular-nums}
.ctl .hint{font-size:.7rem;color:var(--muted);margin-top:.18rem}
input[type=range]{width:100%;accent-color:var(--accent);height:1.1rem;margin:0}
.group-h{font-family:var(--font-mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);margin:1.3rem 0 .2rem;border-top:1px dashed var(--line);padding-top:.9rem}
.group-h:first-child{border-top:none;padding-top:0;margin-top:.2rem}
.switch{display:flex;align-items:center;gap:.55rem;margin-top:.9rem;font-size:.82rem}
.switch input{width:2.3rem;height:1.25rem;accent-color:var(--accent)}
.btn{margin-top:1.1rem;width:100%;font-family:var(--font-mono);font-size:.78rem;
  letter-spacing:.03em;padding:.55rem;border:1px solid var(--line);border-radius:9px;
  background:transparent;color:var(--ink);cursor:pointer}
.btn:hover{border-color:var(--accent);color:var(--accent)}

/* landscape canvas */
.plot-wrap{position:relative}
canvas{width:100%;height:auto;display:block;border-radius:8px}
.legend{display:flex;flex-wrap:wrap;gap:.9rem;margin-top:.7rem;font-size:.76rem;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:.4rem}
.dot{width:.7rem;height:.7rem;border-radius:50%;flex:none}
.dot.ring{background:transparent;border:2px solid var(--select);width:.75rem;height:.75rem}

/* shortlist table */
.tbl-scroll{overflow-x:auto;margin-top:.4rem}
table{border-collapse:collapse;width:100%;font-size:.8rem}
th,td{text-align:right;padding:.4rem .55rem;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{font-family:var(--font-mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);border-bottom:1px solid var(--line);font-weight:500}
td{font-variant-numeric:tabular-nums;border-bottom:1px solid var(--grid)}
td.id{font-family:var(--font-mono);color:var(--ink)}
td.sc{font-family:var(--font-mono);font-weight:600;color:var(--accent)}
tr.sel td{background:color-mix(in srgb,var(--select) 8%,transparent)}
.chip{font-family:var(--font-mono);font-size:.7rem;padding:.05rem .35rem;border-radius:5px;
  background:var(--grid);color:var(--muted)}

/* reject breakdown bars */
.rej{margin-top:.5rem;display:flex;flex-direction:column;gap:.4rem}
.rej-row{display:grid;grid-template-columns:120px 1fr 2.5rem;gap:.5rem;align-items:center;font-size:.76rem}
.rej-row .nm{font-family:var(--font-mono);color:var(--muted);overflow:hidden;text-overflow:ellipsis}
.bar{height:.6rem;border-radius:4px;background:var(--reject);opacity:.85}
.rej-row .ct{font-family:var(--font-mono);text-align:right;color:var(--muted)}

.note{font-size:.78rem;color:var(--muted);margin-top:1.3rem;border-top:1px solid var(--line);padding-top:1rem;max-width:72ch}
.note b{color:var(--ink);font-weight:600}
a{color:var(--accent)}
</style>

<div class="wrap">
  <div class="eyebrow">Adaptyv&nbsp;/&nbsp;EGFR&nbsp;&middot;&nbsp;in-silico triage</div>
  <h1>Binder Triage Explorer</h1>
  <p class="lede">Thousands of designed binders go in; one 96-well plate comes out. Drag the
  gate thresholds and metric weights to see how a biotech turns model scores into the shortlist
  it sends to the wet lab. <span class="tag">600 synthetic designs · live</span></p>

  <div class="pipe" id="pipe">
    <div class="stage s1"><div class="k">Designs in</div><div class="v" id="v-in">0</div><div class="pct">from the design models</div></div>
    <div class="arrow">&rarr;</div>
    <div class="stage s2"><div class="k">Passed gates</div><div class="v" id="v-pass">0</div><div class="pct" id="p-pass">&mdash;</div></div>
    <div class="arrow">&rarr;</div>
    <div class="stage s3"><div class="k">On the plate</div><div class="v" id="v-sel">0</div><div class="pct" id="p-sel">&mdash;</div></div>
  </div>

  <div class="cols">
    <!-- CONTROL RAIL -->
    <div class="card rail">
      <h3>Triage controls <span class="sub">gates &amp; weights</span></h3>

      <div class="group-h">Hard gates &mdash; reject if outside</div>
      <div class="ctl">
        <label><span class="nm">pae_interaction &le;</span><span class="val" id="l-pae">10.0 Å</span></label>
        <input type="range" id="g-pae" min="4" max="20" step="0.5" value="10">
        <div class="hint">Interface error. The single most predictive metric.</div>
      </div>
      <div class="ctl">
        <label><span class="nm">ddG &le;</span><span class="val" id="l-ddg">-20 REU</span></label>
        <input type="range" id="g-ddg" min="-45" max="-5" step="1" value="-20">
        <div class="hint">Predicted binding energy. More negative = tighter.</div>
      </div>
      <div class="ctl">
        <label><span class="nm">pLDDT &ge;</span><span class="val" id="l-plddt">80</span></label>
        <input type="range" id="g-plddt" min="60" max="92" step="1" value="80">
        <div class="hint">Does the binder fold confidently?</div>
      </div>
      <div class="ctl">
        <label><span class="nm">ipTM &ge;</span><span class="val" id="l-iptm">0.50</span></label>
        <input type="range" id="g-iptm" min="0.3" max="0.85" step="0.01" value="0.50">
        <div class="hint">Are the two chains docked correctly?</div>
      </div>
      <label class="switch"><input type="checkbox" id="g-liab" checked>
        <span>Reject developability liabilities</span></label>

      <div class="group-h">Scoring weights &mdash; metric trust</div>
      <div class="ctl">
        <label><span class="nm">pae_interaction</span><span class="val" id="l-wpae">2.5</span></label>
        <input type="range" id="w-pae" min="0" max="4" step="0.5" value="2.5">
      </div>
      <div class="ctl">
        <label><span class="nm">ddG</span><span class="val" id="l-wddg">2.0</span></label>
        <input type="range" id="w-ddg" min="0" max="4" step="0.5" value="2.0">
      </div>
      <div class="ctl">
        <label><span class="nm">ipTM</span><span class="val" id="l-wiptm">1.5</span></label>
        <input type="range" id="w-iptm" min="0" max="4" step="0.5" value="1.5">
      </div>

      <div class="group-h">Plate</div>
      <div class="ctl">
        <label><span class="nm">plate size</span><span class="val" id="l-plate">96</span></label>
        <input type="range" id="s-plate" min="8" max="96" step="8" value="96">
      </div>
      <button class="btn" id="reset">Reset to EGFR defaults</button>
    </div>

    <!-- READOUT -->
    <div style="display:flex;flex-direction:column;gap:18px">
      <div class="card">
        <h3>Design landscape <span class="sub">interface confidence &times; predicted binding</span></h3>
        <div class="plot-wrap"><canvas id="plot" width="820" height="560"></canvas></div>
        <div class="legend">
          <span><span class="dot" style="background:var(--muted);opacity:.45"></span>failed a gate</span>
          <span><span class="dot" style="background:var(--accent)"></span>passed gates</span>
          <span><span class="dot ring"></span>selected for plate</span>
          <span class="tag">x: pae_interaction (Å) &middot; y: ddG (REU)</span>
        </div>
      </div>

      <div class="card">
        <h3>Shortlist <span class="sub">top of the plate, by composite score</span></h3>
        <div class="tbl-scroll"><table id="tbl">
          <thead><tr><th>design</th><th>score</th><th>pae</th><th>ddG</th><th>pLDDT</th><th>ipTM</th><th>method</th></tr></thead>
          <tbody id="tbody"></tbody>
        </table></div>
      </div>

      <div class="card">
        <h3>Why designs were rejected <span class="sub">per failing gate</span></h3>
        <div class="rej" id="rej"></div>
      </div>
    </div>
  </div>

  <p class="note"><b>How to read this.</b> Gates are binary admissibility: tighten <span class="tag">pae</span>
  and watch the funnel narrow and the rejection bars shift. Weights set how the admissible designs are
  ranked &mdash; push <span class="tag">ddG</span> to 0 and the shortlist reorders around interface
  confidence instead. The real craft is calibrating these from wet-lab results: score each metric on how
  well it separated real binders, reweight, repeat. Numbers here are synthetic, modelled on the spread a
  real RFdiffusion&nbsp;/&nbsp;BindCraft&nbsp;&rarr;&nbsp;AlphaFold2&nbsp;&rarr;&nbsp;Rosetta pipeline
  produces &mdash; no wet-lab data is implied. The code that does this for real lives in the
  <span class="tag">binder_triage</span> repo.</p>
</div>

<script>
const DESIGNS = __DATA__;

const els = id => document.getElementById(id);
const state = {
  gpae:10, gddg:-20, gplddt:80, giptm:0.50, liab:true,
  wpae:2.5, wddg:2.0, wiptm:1.5, plate:96
};

// --- robust z-score (median / MAD), matching the Python engine ---
function median(a){const s=[...a].sort((x,y)=>x-y);const n=s.length;if(!n)return 0;
  return n%2?s[(n-1)/2]:(s[n/2-1]+s[n/2])/2;}
function robustZ(vals){
  const med=median(vals);
  const mad=median(vals.map(v=>Math.abs(v-med)));
  if(mad===0){const m=vals.reduce((a,b)=>a+b,0)/vals.length;
    const sd=Math.sqrt(vals.reduce((a,b)=>a+(b-m)**2,0)/vals.length);
    return sd===0?vals.map(()=>0):vals.map(v=>(v-m)/sd);}
  return vals.map(v=>(v-med)/(1.4826*mad));
}

function triage(){
  const gated = DESIGNS.map(d=>{
    const fails=[];
    if(d.pae>state.gpae)fails.push("pae_interaction");
    if(d.ddg>state.gddg)fails.push("ddg");
    if(d.plddt<state.gplddt)fails.push("plddt");
    if(d.iptm<state.giptm)fails.push("iptm");
    if(state.liab && d.liab>0)fails.push("liability");
    return {d,pass:fails.length===0,fails};
  });
  const survivors = gated.filter(g=>g.pass).map(g=>g.d);

  // oriented values: larger = better. pae & ddg are "lower better" -> negate.
  let ranked=[];
  if(survivors.length){
    const zpae=robustZ(survivors.map(d=>-d.pae));
    const zddg=robustZ(survivors.map(d=>-d.ddg));
    const ziptm=robustZ(survivors.map(d=>d.iptm));
    ranked=survivors.map((d,i)=>({
      d, score: state.wpae*zpae[i] + state.wddg*zddg[i] + state.wiptm*ziptm[i]
    })).sort((a,b)=>b.score-a.score);
  }
  const selected = new Set(ranked.slice(0,state.plate).map(r=>r.d.id));

  // rejection breakdown
  const rej={};
  gated.forEach(g=>{if(!g.pass)g.fails.forEach(f=>rej[f]=(rej[f]||0)+1);});
  return {gated,ranked,selected,rej,nPass:survivors.length};
}

function render(){
  const r=triage();
  const N=DESIGNS.length;
  els("v-in").textContent=N;
  els("v-pass").textContent=r.nPass;
  els("v-sel").textContent=r.selected.size;
  els("p-pass").textContent=(100*r.nPass/N).toFixed(0)+"% admissible";
  els("p-sel").textContent=r.ranked.length+" ranked";
  drawPlot(r);
  drawTable(r);
  drawRej(r);
}

// --- landscape scatter on canvas ---
const cv=els("plot"), ctx=cv.getContext("2d");
function cssVar(n){return getComputedStyle(document.body).getPropertyValue(n).trim();}
function drawPlot(r){
  const W=cv.width,H=cv.height, pad={l:62,r:18,t:16,b:46};
  ctx.clearRect(0,0,W,H);
  const paes=DESIGNS.map(d=>d.pae), ddgs=DESIGNS.map(d=>d.ddg);
  const xmin=1,xmax=Math.max(...paes)+1, ymin=Math.min(...ddgs)-2, ymax=Math.max(...ddgs)+2;
  const X=v=>pad.l+(v-xmin)/(xmax-xmin)*(W-pad.l-pad.r);
  // y: ddG, more negative (better) at TOP -> invert
  const Y=v=>pad.t+(v-ymin)/(ymax-ymin)*(H-pad.t-pad.b);
  const grid=cssVar("--grid"), muted=cssVar("--muted"), line=cssVar("--line");
  const mono='12px '+cssVar("--font-mono");

  // grid + axes
  ctx.strokeStyle=grid; ctx.lineWidth=1; ctx.fillStyle=muted; ctx.font=mono;
  ctx.textAlign="center"; ctx.textBaseline="top";
  for(let gx=Math.ceil(xmin/5)*5; gx<=xmax; gx+=5){
    ctx.beginPath();ctx.moveTo(X(gx),pad.t);ctx.lineTo(X(gx),H-pad.b);ctx.stroke();
    ctx.fillText(gx,X(gx),H-pad.b+6);
  }
  ctx.textAlign="right"; ctx.textBaseline="middle";
  for(let gy=Math.ceil(ymin/10)*10; gy<=ymax; gy+=10){
    ctx.beginPath();ctx.moveTo(pad.l,Y(gy));ctx.lineTo(W-pad.r,Y(gy));ctx.stroke();
    ctx.fillText(gy,pad.l-8,Y(gy));
  }
  // gate threshold lines
  ctx.strokeStyle=cssVar("--reject"); ctx.setLineDash([5,4]); ctx.lineWidth=1.3;
  ctx.beginPath();ctx.moveTo(X(state.gpae),pad.t);ctx.lineTo(X(state.gpae),H-pad.b);ctx.stroke();
  ctx.beginPath();ctx.moveTo(pad.l,Y(state.gddg));ctx.lineTo(W-pad.r,Y(state.gddg));ctx.stroke();
  ctx.setLineDash([]);

  // axis titles
  ctx.fillStyle=muted; ctx.font=mono; ctx.textAlign="center"; ctx.textBaseline="alphabetic";
  ctx.fillText("pae_interaction (Å)  — lower better →", (pad.l+W-pad.r)/2, H-8);
  ctx.save();ctx.translate(16,(pad.t+H-pad.b)/2);ctx.rotate(-Math.PI/2);
  ctx.fillText("ddG (REU)  — lower better ↑",0,0);ctx.restore();

  const passSet=new Set(r.ranked.map(x=>x.d.id));
  // failed first (behind)
  DESIGNS.forEach(d=>{ if(passSet.has(d.id))return;
    ctx.fillStyle=muted; ctx.globalAlpha=.32;
    ctx.beginPath();ctx.arc(X(d.pae),Y(d.ddg),3,0,7);ctx.fill();
  });
  ctx.globalAlpha=1;
  // passed
  const acc=cssVar("--accent");
  r.ranked.forEach(x=>{ const d=x.d;
    ctx.fillStyle=acc; ctx.globalAlpha=.9;
    ctx.beginPath();ctx.arc(X(d.pae),Y(d.ddg),4.4,0,7);ctx.fill();
  });
  ctx.globalAlpha=1;
  // selected rings
  ctx.strokeStyle=cssVar("--select"); ctx.lineWidth=2;
  r.selected.forEach(id=>{ const d=DESIGNS.find(z=>z.id===id);
    ctx.beginPath();ctx.arc(X(d.pae),Y(d.ddg),7,0,7);ctx.stroke();
  });
}

function drawTable(r){
  const tb=els("tbody"); tb.innerHTML="";
  r.ranked.slice(0,12).forEach(x=>{
    const d=x.d, sel=r.selected.has(d.id);
    const tr=document.createElement("tr"); if(sel)tr.className="sel";
    tr.innerHTML=`<td class="id">${d.id}</td><td class="sc">${x.score.toFixed(2)}</td>`+
      `<td>${d.pae.toFixed(1)}</td><td>${d.ddg.toFixed(0)}</td>`+
      `<td>${d.plddt.toFixed(0)}</td><td>${d.iptm.toFixed(2)}</td>`+
      `<td style="text-align:left"><span class="chip">${d.m}</span></td>`;
    tb.appendChild(tr);
  });
  if(!r.ranked.length){
    tb.innerHTML=`<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:1.2rem">No design clears every gate — loosen a threshold.</td></tr>`;
  }
}

function drawRej(r){
  const box=els("rej"); box.innerHTML="";
  const entries=Object.entries(r.rej).sort((a,b)=>b[1]-a[1]);
  if(!entries.length){box.innerHTML=`<div class="tag">Nothing rejected at these settings.</div>`;return;}
  const max=Math.max(...entries.map(e=>e[1]));
  entries.forEach(([k,v])=>{
    const row=document.createElement("div"); row.className="rej-row";
    const bar=document.createElement("div"); bar.className="bar"; bar.style.width=(100*v/max)+"%";
    const nm=document.createElement("div"); nm.className="nm"; nm.textContent=k;
    const ct=document.createElement("div"); ct.className="ct"; ct.textContent=v;
    row.appendChild(nm);const w=document.createElement("div");w.appendChild(bar);row.appendChild(w);row.appendChild(ct);
    box.appendChild(row);
  });
}

// --- wire up controls ---
function fmt(){
  els("l-pae").textContent=state.gpae.toFixed(1)+" Å";
  els("l-ddg").textContent=state.gddg+" REU";
  els("l-plddt").textContent=state.gplddt;
  els("l-iptm").textContent=state.giptm.toFixed(2);
  els("l-wpae").textContent=state.wpae.toFixed(1);
  els("l-wddg").textContent=state.wddg.toFixed(1);
  els("l-wiptm").textContent=state.wiptm.toFixed(1);
  els("l-plate").textContent=state.plate;
}
const bind=(id,key,parse)=>{const e=els(id);e.addEventListener("input",()=>{
  state[key]=parse(e.value);fmt();render();});};
bind("g-pae","gpae",parseFloat); bind("g-ddg","gddg",parseFloat);
bind("g-plddt","gplddt",parseFloat); bind("g-iptm","giptm",parseFloat);
bind("w-pae","wpae",parseFloat); bind("w-ddg","wddg",parseFloat);
bind("w-iptm","wiptm",parseFloat); bind("s-plate","plate",v=>parseInt(v));
els("g-liab").addEventListener("change",e=>{state.liab=e.target.checked;render();});
els("reset").addEventListener("click",()=>{
  const d={gpae:10,gddg:-20,gplddt:80,giptm:0.50,liab:true,wpae:2.5,wddg:2.0,wiptm:1.5,plate:96};
  Object.assign(state,d);
  els("g-pae").value=10;els("g-ddg").value=-20;els("g-plddt").value=80;els("g-iptm").value=0.50;
  els("w-pae").value=2.5;els("w-ddg").value=2.0;els("w-iptm").value=1.5;els("s-plate").value=96;
  els("g-liab").checked=true; fmt();render();
});

fmt(); render();
window.addEventListener("resize",()=>render());
</script>'''

out = HTML.replace("__DATA__", DATA_JSON)
dest = ROOT / "web" / "triage_explorer.html"
dest.write_text(out)
print("wrote", dest, len(out), "bytes")
