const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const real=JSON.parse(readFileSync('data/records.json','utf8')).map(({contexts,...r})=>({...r,contextCodes:(contexts||[]).map(c=>c.code)}));
const elements=new Map();
function element(selector){
 if(!elements.has(selector))elements.set(selector,{value:'',innerHTML:'',textContent:'',disabled:false,events:{},addEventListener(name,fn){this.events[name]=fn}});
 return elements.get(selector);
}
const context={document:{querySelector:element},URLSearchParams,location:{search:'',pathname:'/'},history:{replaceState(){}},fetch:async url=>({ok:true,json:async()=>url==='records-manifest.json'?{years:{'2026':'records-2026.json'}}:real}),setTimeout,clearTimeout};
vm.createContext(context);
vm.runInContext(readFileSync('web/app.js','utf8'),context);
const submit=()=>element('#search').events.submit({preventDefault(){}});
async function main(){
 await new Promise(resolve=>setTimeout(resolve,10));
 assert(element('#results').innerHTML.includes('class="card"'));
 element('#q').value='502051001';submit();
 assert(element('#results').innerHTML.includes('50.205.1001'));
 assert(element('#results').innerHTML.includes('117,00'));
 element('#q').value='yukleme';element('#institution').value='DSİ';submit();
 assert(element('#results').innerHTML.includes('class="card"'));
 assert(!element('#results').innerHTML.includes('KGM ·'));
 element('#q').value='ZZZZZ-bulunmayan-poz';submit();
 assert(element('#results').innerHTML.includes('Sonuç bulunamadı'));
 assert(element('#next').disabled);
 element('#q').value='';element('#institution').value='';element('#year').value='2026';submit();
 assert(element('#results').innerHTML.includes('· 2026'));
 element('#q').value='25.170.1101';element('#institution').value='ÇŞB';submit();
 assert(element('#results').innerHTML.includes('1.159,35'));
 assert(element('#results').innerHTML.includes('481,88'));
 element('#q').value='kollektor 25.170.1101';submit();
 assert(element('#results').innerHTML.includes('25.170.1101'));
 console.log('Search checks passed: initial load, compact code, Turkish text, institution filter, empty result.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
