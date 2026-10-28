const normalize=value=>value.toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ı/g,'i');
const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatPrice=value=>Number(value).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})+' ₺';
let records=[],filtered=[],page=0,manifest={},loadToken=0,lastFocus=null;
const size=25;
const form=document.querySelector('#search');
const input=document.querySelector('#q');
const institution=document.querySelector('#institution');
const year=document.querySelector('#year');
const results=document.querySelector('#results');
const modal=document.querySelector('#poz-modal');
const modalTitle=document.querySelector('#modal-title');
const modalContent=document.querySelector('#modal-content');
const modalClose=document.querySelector('#modal-close');

function render(){
 const visible=filtered.slice(page*size,(page+1)*size);
 if(!visible.length){
  results.innerHTML='<div class="empty"><strong>Sonuç bulunamadı</strong><span>Daha kısa bir kelime veya farklı bir poz numarası deneyin.</span></div>';
 }else{
  const rows=visible.map(r=>{
   const detail=encodeURIComponent(r.detailId||r.id);
   const price=r.price===null?(r.recordType==='group'?'Grup tarifi':'Tarife bağlı'):formatPrice(r.price);
   const installation=r.installationPrice!=null?`<small>Montaj: ${formatPrice(r.installationPrice)}</small>`:'';
   return `<tr><td class="code-cell"><button class="table-link row-open" type="button" data-detail="${detail}" data-code="${esc(r.code)}">${esc(r.code)}</button></td><td class="title-cell"><button class="title-link row-open" type="button" data-detail="${detail}" data-code="${esc(r.code)}">${esc(r.title)}</button>${r.contextLabel?`<small>${esc(r.contextLabel)}</small>`:''}</td><td>${esc(r.unit)}</td><td class="price-cell"><strong>${price}</strong>${installation}</td><td class="source-cell"><strong>${esc(r.institution)}</strong><span>${esc(r.year)}</span></td><td><button class="inspect row-open" type="button" data-detail="${detail}" data-code="${esc(r.code)}" aria-label="${esc(r.code)} pozunu incele">İncele</button></td></tr>`;
  }).join('');
  results.innerHTML=`<div class="table-shell"><table class="results-table"><thead><tr><th>Poz No</th><th>Poz Tanımı</th><th>Birim</th><th>Birim Fiyat</th><th>Kurum / Yıl</th><th><span class="sr-only">İşlem</span></th></tr></thead><tbody>${rows}</tbody></table></div>`;
 }
 document.querySelector('#count').textContent=`${filtered.length.toLocaleString('tr-TR')} poz bulundu`;
 document.querySelector('#page').textContent=`${page+1} / ${Math.max(1,Math.ceil(filtered.length/size))}`;
 document.querySelector('#prev').disabled=page===0;
 document.querySelector('#next').disabled=(page+1)*size>=filtered.length;
}

function search(){
 const terms=normalize(input.value.trim()).split(/\s+/).filter(Boolean);
 filtered=records.filter(r=>(!institution.value||r.institution===institution.value)&&(!year.value||String(r.year)===year.value)&&terms.every(t=>r.search.includes(t)||r.code.replace(/[^a-z0-9]/gi,'').toLowerCase().includes(t.replace(/[./-]/g,''))));
 document.body?.classList?.toggle('has-search',terms.length>0);
 page=0;
 render();
 const params=new URLSearchParams();
 if(input.value)params.set('q',input.value);
 if(institution.value)params.set('kurum',institution.value);
 if(year.value)params.set('yil',year.value);
 history.replaceState(null,'',location.pathname+(params.size?'?'+params:''));
}

const prepare=data=>{
 const lookup=new Map(data.map(r=>[r.institution+'|'+r.year+'|'+r.code,r]));
 return data.map(r=>{
  const contexts=r.contexts||((r.contextCodes||[]).map(code=>lookup.get(r.institution+'|'+r.year+'|'+code)).filter(Boolean));
  return {...r,contextLabel:contexts.at(-1)?.title.slice(0,140)||'',search:normalize(r.code+' '+r.title+' '+r.institution+' '+r.year+' '+(r.tariff?.text||'')+' '+contexts.map(c=>c.title).join(' '))};
 });
};
const cache=new Map();

async function loadRecords(){
 const token=++loadToken;
 const years=year.value?[year.value]:Object.keys(manifest);
 document.querySelector('#count').textContent='Pozlar yükleniyor…';
 const chunks=await Promise.all(years.map(async key=>{
  if(cache.has(key))return cache.get(key);
  const response=await fetch(manifest[key]);
  if(!response.ok)throw Error('Veri yüklenemedi');
  const data=prepare(await response.json());
  cache.set(key,data);
  return data;
 }));
 if(token!==loadToken)return;
 records=chunks.flat();
 search();
}

async function openDetail(id,code,trigger){
 lastFocus=trigger||null;
 modal.hidden=false;
 document.body?.classList?.add('modal-open');
 modalTitle.textContent=code?`${code} · Poz detayı`:'Poz detayı';
 modalContent.innerHTML='<div class="modal-loading">Poz bilgisi yükleniyor…</div>';
 modalClose.focus?.();
 try{
  const response=await fetch('poz/'+id+'/');
  if(!response.ok)throw Error('Poz detayı yüklenemedi');
  const parsed=new DOMParser().parseFromString(await response.text(),'text/html');
  const article=parsed.querySelector('article.detail');
  if(!article)throw Error('Poz detayı bulunamadı');
  article.querySelector(':scope > a')?.remove();
  modalContent.innerHTML='<article class="detail modal-detail">'+article.innerHTML+'</article>';
 }catch(error){
  modalContent.innerHTML='<div class="empty"><strong>Poz bilgisi yüklenemedi</strong><span>Bağlantıyı kontrol edip yeniden deneyin.</span></div>';
 }
}

function closeDetail(){
 modal.hidden=true;
 document.body?.classList?.remove('modal-open');
 lastFocus?.focus?.();
}

if(form){
 const params=new URLSearchParams(location.search);
 input.value=params.get('q')||'';
 institution.value=params.get('kurum')||'';
 year.value=params.get('yil')||'2026';
 fetch('records-manifest.json').then(r=>{
  if(!r.ok)throw Error('Veri yüklenemedi');
  return r.json();
 }).then(data=>{
  manifest=data.years;
  if(year.value&&!manifest[year.value])year.value='2026';
  return loadRecords();
 }).catch(()=>{
  document.querySelector('#count').textContent='Veri yüklenemedi';
  results.innerHTML='<div class="empty"><strong>Veri yüklenemedi</strong><span>Bağlantıyı kontrol edip sayfayı yenileyin.</span></div>';
 });
 form.addEventListener('submit',event=>{event.preventDefault();search()});
 let timer;
 input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,180)});
 institution.addEventListener('change',search);
 year.addEventListener('change',()=>loadRecords().catch(()=>{document.querySelector('#count').textContent='Veri yüklenemedi'}));
 document.querySelector('#prev').addEventListener('click',()=>{page--;render();document.querySelector('.result-section')?.scrollIntoView?.({behavior:'smooth'})});
 document.querySelector('#next').addEventListener('click',()=>{page++;render();document.querySelector('.result-section')?.scrollIntoView?.({behavior:'smooth'})});
 results.addEventListener('click',event=>{
  const trigger=event.target.closest?.('[data-detail]');
  if(!trigger)return;
  openDetail(trigger.dataset.detail,trigger.dataset.code,trigger);
 });
 modalClose.addEventListener('click',closeDetail);
 modal.addEventListener('click',event=>{if(event.target.hasAttribute?.('data-modal-close'))closeDetail()});
 document.addEventListener?.('keydown',event=>{if(event.key==='Escape'&&!modal.hidden)closeDetail()});
}
