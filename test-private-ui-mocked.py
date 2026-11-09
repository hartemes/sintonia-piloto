#!/usr/bin/env python3
"""Mock DOM/HTTP JS regression, synthetic data only. Requires quickjs-ng. NOT a browser/E2E test."""
from pathlib import Path
import re
import quickjs

html = Path(__file__).with_name('index.html').read_text()
m = re.search(r'<script>(.*?)</script>', html, re.S)
if not m: raise SystemExit('Missing application script')
ctx = quickjs.Context()
ctx.eval(r'''
const elements={};
class FakeElement {
 constructor(id){this.id=id;this.hidden=false;this.disabled=false;this.value='';this.textContent='';this.files=[];this.listeners={};this.children=[];}
 addEventListener(ev,handler){(this.listeners[ev]??=[]).push(handler)}
 click(){for(const f of this.listeners.click||[])f({preventDefault(){}})}
 submit(){for(const f of this.listeners.submit||[])f({preventDefault(){}})}
 replaceChildren(...xs){this.children=xs;this.textContent=xs.map(x=>x.textContent||'').join('')}
 appendChild(x){this.children.push(x);this.textContent+=x.textContent||''}
 append(...xs){xs.forEach(x=>this.appendChild(x))}
 removeAttribute(){} reset(){if(this.id==='profileForm'){for(const id of ['name','birth','city','about','lookingFor','interests','minAge','maxAge'])if(elements[id])elements[id].value=''}}
}
const document={getElementById(id){return elements[id]??=new FakeElement(id)},createElement(tag){return new FakeElement(tag)}};
const URL={createObjectURL(){return 'blob:fake'},revokeObjectURL(){}};
function confirm(){return true}
let requests=[], pendingDiscovery, pendingImage, pendingPassword, pendingDelete, pendingLogin, pendingUpload, pendingProfile;
let mode='';
function response(data,status=200){return {ok:status>=200&&status<300,status,json:async()=>data,blob:async()=>({fake:true})}}
async function fetch(url,options={}){
 requests.push({url,options});
 if(url.includes('/auth/v1/token?grant_type=password')) return new Promise(r=>pendingLogin=r);
 if(url.includes('/storage/v1/object/sintonia-fotos/') && options.method==='POST') return new Promise(r=>pendingUpload=r);
 if(url.includes('sintonia_listar_descoberta')) return new Promise(r=>pendingDiscovery=r);
 if(url.includes('sintonia_definir_visibilidade')) return response(true);
 if(url.includes('sintonia_ler_minha_visibilidade')) return response(false);
 if(url.includes('/rest/v1/sintonia_perfis')) {if(mode==='hold-profile-fail')return new Promise(r=>pendingProfile=r);return response([{usuario_id:'synthetic-a'}])};
 if(url.includes('/auth/v1/user')) return new Promise(r=>pendingPassword=r);
 if(url.includes('/auth/v1/logout')) return response(null,204);
 if(url.endsWith('/storage/v1/object/sintonia-fotos') && options.method==='DELETE')return new Promise(r=>pendingDelete=r);
 throw Error('Unexpected request in network mock: '+url);
}
''')
try:
 ctx.eval(m.group(1))
except Exception as e:
 raise SystemExit('Application JavaScript failed to initialize: '+str(e))
ctx.eval(r'''
let checks=[];
function assertTest(label,ok){checks.push({label,ok:!!ok})}
async function ticks(){for(let i=0;i<12;i++)await Promise.resolve()}
async function runTests(){
 session={user:'synthetic-a',token:'synthetic-token'};view();
 $('loadDiscovery').click();await ticks();assertTest('discovery request held',typeof pendingDiscovery==='function');
 await setConsent(false);pendingDiscovery(response([{nome:'SYNTHETIC PRIVATE',idade:30}]));await ticks();
 assertTest('late discovery discarded after opt-out',!$('discoveryResults').textContent.includes('SYNTHETIC PRIVATE'));
 assertTest('opt-out sent with no-store',requests.some(x=>x.url.includes('sintonia_definir_visibilidade')&&x.options.cache==='no-store'));
 cleanImage=()=>new Promise(r=>pendingImage=r);
 $('photoFile').files=[{type:'image/jpeg',size:10}];$('savePhoto').click();await ticks();
 assertTest('image conversion held',typeof pendingImage==='function');
 $('logout').click();await ticks();pendingImage({synthetic:true});await ticks();
 assertTest('logout prevents subsequent photo upload',!requests.some(x=>x.url.includes('/storage/v1/object/sintonia-fotos/')));
 assertTest('stale photo response does not change logout status',$('status').textContent==='Você saiu.');
 session={user:'synthetic-b',token:'synthetic-token-b'};view();
 $('newPassword').value='example-password';$('confirmPassword').value='example-password';$('passwordChangeForm').submit();await ticks();
 assertTest('password request held',typeof pendingPassword==='function');
 $('logout').click();await ticks();pendingPassword(response({}));await ticks();
 assertTest('stale password result does not change logout status',$('status').textContent==='Você saiu.');
 assertTest('password update no-store',requests.some(x=>x.url.includes('/auth/v1/user')&&x.options.cache==='no-store'));
 session={user:'synthetic-c',token:'synthetic-token-c'};view();
 cleanImage=async()=>({synthetic:true});$('photoFile').files=[{type:'image/jpeg',size:10}];$('savePhoto').click();await ticks();
 assertTest('photo upload request held',typeof pendingUpload==='function');
 $('deletePhoto').click();await ticks();assertTest('photo delete cannot race in-flight upload',!requests.some(x=>x.options.method==='DELETE'&&x.url.endsWith('/storage/v1/object/sintonia-fotos')));
 $('logout').click();await ticks();pendingUpload(response({}));await ticks();
 assertTest('late upload response after logout is inert',$('status').textContent==='Você saiu.');
 session={user:'synthetic-d',token:'synthetic-token-d'};view();
 $('deletePhoto').click();await ticks();assertTest('photo deletion request held',typeof pendingDelete==='function');
 $('logout').click();await ticks();pendingDelete(response(null,204));await ticks();
 assertTest('stale delete result does not change logout status',$('status').textContent==='Você saiu.');
 assertTest('chat remains paused',CHAT_PAUSED===true);
 session={user:'synthetic-old',token:'synthetic-old-token'};view();
 $('loginForm').submit();await ticks();assertTest('login request held',typeof pendingLogin==='function');
 $('logout').click();await ticks();pendingLogin(response({access_token:'synthetic-stale-token',user:{id:'synthetic-stale'}}));await ticks();
 assertTest('late login token is revoked after logout',requests.some(x=>x.url.includes('/auth/v1/logout')&&x.options.headers.Authorization==='Bearer synthetic-stale-token'));
 assertTest('late login does not recreate session',session===null);
 mode='normal';session={user:'synthetic-private',token:'synthetic-session'};view();$('name').value='PRIVATE PROFILE';$('consentState').textContent='PRIVATE CONSENT';
 mode='hold-profile-fail';$('email').value='synthetic@example.test';$('password').value='synthetic-password';$('loginForm').submit();await ticks();
 pendingLogin(response({access_token:'synthetic-profile-token',user:{id:'synthetic-profile-user'}}));await ticks();
 assertTest('profile request held after successful auth',typeof pendingProfile==='function');pendingProfile(response({},500));await ticks();
 assertTest('failed profile load clears invalid session',session===null);
 assertTest('failed profile load clears prior private profile fields',$('name').value===''&&$('consentState').textContent==='');
 assertTest('failed profile load hides private sections',$('profileSection').hidden&&$('discoveryConsent').hidden&&$('realChats').hidden);
 assertTest('post-auth profile failure revokes issued token',requests.some(x=>x.url.includes('/auth/v1/logout')&&x.options.headers.Authorization==='Bearer synthetic-profile-token'));
 mode='normal';
 assertTest('all mocked requests use no-store',requests.every(x=>x.options.cache==='no-store'));
 globalThis.testDone=true;
}
runTests().catch(e=>{checks.push({label:'unexpected error: '+e,ok:false});globalThis.testDone=true});
''')
for _ in range(10000):
 if not ctx.execute_pending_job(): break
if not ctx.eval('!!globalThis.testDone'): raise SystemExit('Mock tests did not complete')
import json
checks = json.loads(ctx.eval('JSON.stringify(checks)'))
for item in checks: print(('PASS' if item['ok'] else 'FAIL')+' — '+item['label'])
failed = sum(not x['ok'] for x in checks)
print(f'{len(checks)-failed}/{len(checks)} passed; mocked JS runtime only, no browser/network/database.')
raise SystemExit(bool(failed))
