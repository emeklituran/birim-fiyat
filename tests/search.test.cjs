const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const real=JSON.parse(readFileSync('data/records.json','utf8')).map(({contexts,...r})=>({...r,contextCodes:(contexts||[]).map(c=>c.code)}));
const elements=new Map();
function element(selector){
 if(!elements.has(selector))elements.set(selector,{value:'',innerHTML:'',textContent:'',disabled:false,hidden:true,events:{},addEventListener(name,fn){this.events[name]=fn},focus(){}});
 return elements.get(selector);
}
class FakeDOMParser{
 parseFromString(){return {querySelector(){return {innerHTML:'<h1>Test poz tarifi</h1>',querySelector(){return {remove(){}}}}}}}
}
const context={document:{querySelector:element,body:{classList:{add(){},remove(){},toggle(){}}},addEventListener(){}},DOMParser:FakeDOMParser,URLSearchParams,location:{search:'',pathname:'/'},history:{replaceState(){}},fetch:async url=>url.startsWith('poz/')?{ok:true,text:async()=>'<article class="detail"><h1>Test poz tarifi</h1></article>'}:{ok:true,json:async()=>url==='records-manifest.json'?{years:{'2026':'records-2026.json'}}:real},setTimeout,clearTimeout};
vm.createContext(context);
vm.runInContext(readFileSync('web/app.js','utf8'),context);
const submit=()=>element('#search').events.submit({preventDefault(){}});
async function main(){
 await new Promise(resolve=>setTimeout(resolve,10));
 assert(element('#results').innerHTML.includes('class="results-table"'));
 element('#q').value='502051001';submit();
 assert(element('#results').innerHTML.includes('50.205.1001'));
 assert(element('#results').innerHTML.includes('117,00'));
 element('#q').value='yukleme';element('#institution').value='DSİ';submit();
 assert(element('#results').innerHTML.includes('class="results-table"'));
 assert(!element('#results').innerHTML.includes('<strong>KGM</strong>'));
 element('#q').value='ZZZZZ-bulunmayan-poz';submit();
 assert(element('#results').innerHTML.includes('Sonuç bulunamadı'));
 assert(element('#next').disabled);
 element('#q').value='';element('#institution').value='';element('#year').value='2026';submit();
 assert(element('#results').innerHTML.includes('<span>2026</span>'));
 element('#q').value='25.170.1101';element('#institution').value='ÇŞB';submit();
 assert(element('#results').innerHTML.includes('1.159,35'));
 assert(element('#results').innerHTML.includes('481,88'));
 element('#q').value='kollektor 25.170.1101';submit();
 assert(element('#results').innerHTML.includes('25.170.1101'));
 const trigger={dataset:{detail:'csb-2026-25-170-1101',code:'25.170.1101'},closest(){return this}};
 element('#results').events.click({target:trigger});
 await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(element('#poz-modal').hidden,false);
 assert(element('#modal-content').innerHTML.includes('Test poz tarifi'));
 element('#modal-close').events.click();
 assert.equal(element('#poz-modal').hidden,true);
 console.log('Search checks passed: table results, filters, Turkish text and popup detail.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
