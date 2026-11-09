#!/usr/bin/env python3
"""Static fail-closed checks for the paused Sintonia client (not browser tests)."""
from pathlib import Path
import re

html = Path(__file__).with_name('index.html').read_text()
checks = {
    'real chat remains paused': 'const CHAT_PAUSED=true' in html,
    'private epoch guard exists': 'function viewIsCurrent(epoch,user)' in html,
    'opt-out invalidates old requests': "if(!value){resultEpoch=++privateViewEpoch" in html,
    'logout invalidates private, photo and consent operations': "privateViewEpoch++;photoOperationEpoch++;photoStateEpoch++;setPhotoBusy(false);consentFlight=null" in html,
    'generic REST requests disable cache': "cache:'no-store'" in re.search(r'async function request\([^\n]+', html).group(0),
    'password update disables cache': "'/auth/v1/user'" in html and "body:JSON.stringify({password:a}),cache:'no-store'" in html,
    'photo load disables cache': "'/storage/v1/object/authenticated/sintonia-fotos/'" in html and "cache:'no-store'" in html,
    'photo upload has operation/session guard after image processing': 'const blob=await cleanImage(file);if(!viewIsCurrent(epoch,user)||photoEpoch!==photoOperationEpoch||photoState!==photoStateEpoch)return;' in html,
    'photo upload response has operation/session guard': "if(!viewIsCurrent(epoch,user)||photoEpoch!==photoOperationEpoch||photoState!==photoStateEpoch)return;if(!r.ok)throw Error();$('photoFile').value=''" in html,
    'photo delete response has operation/session guard': "prefixes:[user+'/perfil']}),cache:'no-store'});if(!viewIsCurrent(epoch,user)||photoEpoch!==photoOperationEpoch)return;" in html,
    'login attempts clear/invalidate previous private session': "const previousToken=session?.token;const epoch=++privateViewEpoch;photoOperationEpoch++;photoStateEpoch++;setPhotoBusy(false);consentFlight=null;session=null;clearPrivateView();view()" in html,
    'stale login token is revoked': "if(epoch!==privateViewEpoch){if(x?.access_token)request('/auth/v1/logout','POST',{},x.access_token).catch(()=>{});return}" in html,
    'issued login token is revoked if post-auth profile setup fails': "let issuedToken=null;try{const x=await request('/auth/v1/token?grant_type=password'" in html and "if(issuedToken)request('/auth/v1/logout','POST',{},issuedToken).catch(()=>{});session=null;clearPrivateView()" in html,
    'birth date check rejects impossible dates and pre-1900 values': 'function isAdultBirthDate(value,today=new Date())' in html and 'year<1900' in html and 'check.getUTCDate()!==day' in html,
    'adult boundary uses calendar date and requires 18th birthday reached': 'const cutoffYear=today.getFullYear()-18' in html and 'day<=cutoffDay' in html and "if(!isAdultBirthDate(birth))" in html,
    'likes/messages remain explicitly demo-only': 'curtidas e mensagens não são enviadas, não ficam salvas' in html,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL') + ' — ' + name)
print(f'\n{len(checks)-len(failed)}/{len(checks)} static checks passed')
raise SystemExit(bool(failed))
