const normalize = value => value.toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ı/g,'i');
let records=[], filtered=[], page=0;
const size=25, form=document.querySelector('#search'), input=document.querySelector('#q'), institution=document.querySelector('#institution');
const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(){
 const results=document.querySelector('#results');
 results.innerHTML=filtered.slice(page*size,(page+1)*size).map(r=>`<article class="card"><div><span class="code">${esc(r.code)}</span><span class="tag">${esc(r.institution)} · ${r.year}</span><h2><a href="poz/${encodeURIComponent(r.id)}/">${esc(r.title)}</a></h2><div class="foot">${esc(r.period)} · ${esc(r.priceBasis)}<br>Tablo tanımı · <a href="poz/${encodeURIComponent(r.id)}/">Detayı ve kaynağı gör →</a></div></div><div class="price">${r.price===null?'Tarife bağlı':Number(r.price).toLocaleString('tr-TR',{minimumFractionDigits:2})+' ₺'}<small>/ ${esc(r.unit)}</small></div></article>`).join('');
 if(!filtered.length)results.innerHTML='<div class="empty">Sonuç bulunamadı. Daha kısa bir kelime veya farklı bir poz numarası deneyin.</div>';
 document.querySelector('#count').textContent=`${filtered.length.toLocaleString('tr-TR')} poz bulundu`;
 document.querySelector('#page').textContent=`${page+1} / ${Math.max(1,Math.ceil(filtered.length/size))}`;
 document.querySelector('#prev').disabled=page===0;
 document.querySelector('#next').disabled=(page+1)*size>=filtered.length;
}
function search(){
 const terms=normalize(input.value.trim()).split(/\s+/).filter(Boolean);
 filtered=records.filter(r=>(!institution.value||r.institution===institution.value)&&terms.every(t=>r.search.includes(t)||r.code.replace(/[^a-z0-9]/gi,'').toLowerCase().includes(t.replace(/[./-]/g,''))));
 page=0;render();const params=new URLSearchParams();if(input.value)params.set('q',input.value);if(institution.value)params.set('kurum',institution.value);history.replaceState(null,'',location.pathname+(params.size?'?'+params:''));
}
if(form){
 const params=new URLSearchParams(location.search);input.value=params.get('q')||'';institution.value=params.get('kurum')||'';
 fetch('records.json').then(r=>{if(!r.ok)throw Error('Veri yüklenemedi');return r.json()}).then(data=>{records=data.map(r=>({...r,search:normalize(r.code+' '+r.title+' '+r.institution+' '+(r.tariff?.text||''))}));search();}).catch(()=>{document.querySelector('#count').textContent='Veri yüklenemedi';document.querySelector('#results').innerHTML='<div class="empty">Bağlantıyı kontrol edip sayfayı yenileyin.</div>';});
 form.addEventListener('submit',e=>{e.preventDefault();search()});let timer;input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,180)});institution.addEventListener('change',search);
 document.querySelector('#prev').addEventListener('click',()=>{page--;render()});document.querySelector('#next').addEventListener('click',()=>{page++;render()});
}
