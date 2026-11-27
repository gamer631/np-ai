const $=id=>document.getElementById(id);
let tableData=null, datasetName='Sample dataset';
const sample=`month,temperature,rainfall
Jan,12,4
Feb,14,8
Mar,18,20
Apr,22,35
May,25,90
Jun,27,180
Jul,28,260
Aug,27,220
Sep,25,150
Oct,21,45
Nov,17,10
Dec,13,5`;
function parseCSV(text){
  const rows=[];let row=[],cell='',quoted=false,afterQuote=false;
  for(let i=0;i<text.length;i++){
    const ch=text[i];
    if(quoted){
      if(ch==='"'&&text[i+1]==='"'){cell+='"';i++;}
      else if(ch==='"'){quoted=false;afterQuote=true;}
      else cell+=ch;
      continue;
    }
    if(afterQuote){
      if(ch===',' ){row.push(cell);cell='';afterQuote=false;}
      else if(ch==='\\n'||ch==='\\r'){if(ch==='\\r'&&text[i+1]==='\\n')i++;row.push(cell);cell='';afterQuote=false;if(row.some(v=>v.trim()!==''))rows.push(row);row=[];}
      else if(ch===' '||ch==='\\t'){/* tolerate whitespace after closing quote */}
      else throw Error('Unexpected character after a quoted CSV cell.');
      continue;
    }
    if(ch==='"'){
      if(cell.length!==0)throw Error('Quote found inside an unquoted CSV cell.');
      quoted=true;
    }else if(ch===','){row.push(cell);cell='';}
    else if(ch==='\\n'||ch==='\\r'){if(ch==='\\r'&&text[i+1]==='\\n')i++;row.push(cell);cell='';if(row.some(v=>v.trim()!==''))rows.push(row);row=[];}
    else cell+=ch;
  }
  if(quoted)throw Error('CSV contains an unfinished quoted cell.');
  row.push(cell);if(row.some(v=>v.trim()!==''))rows.push(row);
  if(rows.length<2)throw Error('CSV needs a header and at least one data row.');
  const headers=rows[0].map(v=>v.trim());
  if(headers.some(v=>!v)||new Set(headers).size!==headers.length)throw Error('Headers must be non-empty and unique.');
  const body=rows.slice(1).map(r=>{if(r.length!==headers.length)throw Error('Rows must have the same number of cells as the header.');return r.map(v=>v.trim());});
  return {headers,body};
}
function numericCol(name){const idx=tableData.headers.indexOf(name);if(idx<0)return null;const vals=tableData.body.map(r=>r[idx].trim()===''?NaN:Number(r[idx]));if(vals.some(v=>!Number.isFinite(v)))return null;return vals;}
function loadDataset(text,name){tableData=parseCSV(text);datasetName=name;renderTable();renderControls();renderChart();renderStats();$('datasetEmpty').classList.add('hidden');$('datasetInfo').classList.remove('hidden');$('rowMetric').textContent=tableData.body.length.toLocaleString();$('colMetric').textContent=tableData.headers.length.toLocaleString();$('fileName').textContent=name;$('fileMeta').textContent=tableData.body.length+' rows · '+tableData.headers.length+' columns';}
function renderTable(){const t=$('dataTable');t.innerHTML='';const h=document.createElement('tr');tableData.headers.forEach(v=>{const th=document.createElement('th');th.textContent=v;h.appendChild(th)});t.appendChild(h);tableData.body.slice(0,100).forEach(row=>{const tr=document.createElement('tr');row.forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.appendChild(td)});t.appendChild(tr)});}
function renderControls(){const sel=$('chartColumn');sel.innerHTML='';const opts=tableData.headers.filter(h=>numericCol(h));opts.forEach(h=>{const op=document.createElement('option');op.value=h;op.textContent=h;sel.appendChild(op)});sel.disabled=!opts.length;if(opts.length){$('chartEmpty').classList.add('hidden');$('legendText').textContent=opts[0];}else{$('chartEmpty').textContent='No numeric columns found in this dataset.';$('chartEmpty').classList.remove('hidden');$('legendText').textContent='No numeric columns';}}
function renderChart(){const canvas=$('chart'),ctx=canvas.getContext('2d'),vals=numericCol($('chartColumn').value);ctx.clearRect(0,0,canvas.width,canvas.height);if(!vals||!vals.length){$('chartEmpty').classList.remove('hidden');return;}const pad={l:42,r:14,t:15,b:28},w=canvas.width-pad.l-pad.r,h=canvas.height-pad.t-pad.b,min=vals.reduce((a,b)=>b<a?b:a,Infinity),max=vals.reduce((a,b)=>b>a?b:a,-Infinity),range=max-min||1;ctx.font='11px DM Sans';ctx.strokeStyle='#26374a';ctx.fillStyle='#8295ac';ctx.lineWidth=1;for(let k=0;k<5;k++){const y=pad.t+h*k/4;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(pad.l+w,y);ctx.stroke();ctx.fillText((max-range*k/4).toFixed(1),4,y+4);}const points=vals.map((v,i)=>({x:pad.l+(vals.length===1?w/2:i*w/(vals.length-1)),y:pad.t+h-(v-min)/range*h}));ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.strokeStyle='#56cfe5';ctx.lineWidth=2;ctx.stroke();ctx.lineTo(points.at(-1).x,pad.t+h);ctx.lineTo(points[0].x,pad.t+h);ctx.closePath();const grad=ctx.createLinearGradient(0,pad.t,0,pad.t+h);grad.addColorStop(0,'#56cfe533');grad.addColorStop(1,'#56cfe500');ctx.fillStyle=grad;ctx.fill();points.forEach(p=>{ctx.beginPath();ctx.arc(p.x,p.y,3,0,Math.PI*2);ctx.fillStyle='#70e0f0';ctx.fill()});$('chartEmpty').classList.add('hidden');$('legendText').textContent=$('chartColumn').value;}
function renderStats(){const numeric=tableData.headers.map(h=>({name:h,vals:numericCol(h)})).filter(o=>o.vals);const container=$('stats');container.innerHTML='';if(!numeric.length){container.innerHTML='<p class="muted">No numeric columns available.</p>';return;}numeric.slice(0,6).forEach(({name,vals})=>{const sum=vals.reduce((a,b)=>a+b,0),mean=sum/vals.length,min=vals.reduce((a,b)=>b<a?b:a,Infinity),max=vals.reduce((a,b)=>b>a?b:a,-Infinity);const card=document.createElement('div');card.className='stat-card';const label=document.createElement('span');label.textContent=name+' · mean';const value=document.createElement('strong');value.textContent=mean.toPrecision(5).replace(/0+$/,'').replace(/\.$/,'');const range=document.createElement('span');range.textContent='min '+min+' / max '+max;range.style.marginTop='5px';card.append(label,value,range);container.appendChild(card)});}
$('sampleBtn').addEventListener('click',()=>loadDataset(sample,'climate_sample.csv'));
$('csvFile').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;if(file.size>2_000_000){alert('CSV exceeds the 2 MB preview limit.');e.target.value='';return;}try{loadDataset(await file.text(),file.name);}catch(err){alert('Could not load CSV: '+err.message);}e.target.value='';});
$('chartColumn').addEventListener('change',renderChart);
$('clearBtn').addEventListener('click',()=>{tableData=null;$('datasetInfo').classList.add('hidden');$('datasetEmpty').classList.remove('hidden');$('rowMetric').textContent='—';$('colMetric').textContent='—';$('chartColumn').innerHTML='<option>Numeric column</option>';$('chartColumn').disabled=true;$('chartEmpty').textContent='Load a dataset to visualize a numeric column.';$('chartEmpty').classList.remove('hidden');$('chart').getContext('2d').clearRect(0,0,600,250);$('stats').innerHTML='<p class="muted">Statistics appear after loading a numeric dataset.</p>';});
