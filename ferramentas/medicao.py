#!/usr/bin/env python3
"""Acrescenta ao index.html a medição de visitas e de cliques no WhatsApp (Google Analytics 4 com modo de consentimento)
e o aviso de cookies. Só liga quando o build recebe o ID (site.json -> ga_id). Uso: python3 medicao.py /pasta/do/site"""
import sys, os
F = os.path.join(sys.argv[1], 'index.html'); s = open(F, encoding='utf-8').read()
assert 'UC_MEDICAO_V1' not in s
def sub1(a, b):
    global s
    assert s.count(a) == 1, a[:80]; s = s.replace(a, b)
# política de privacidade: texto certo para cada situação (o build mostra um ou outro)
sub1('O site não pede nem guarda dados de cartão. Não usamos cookies de propaganda nem ferramentas de rastreamento.',
     'O site não pede nem guarda dados de cartão. <span data-ga-off>Não usamos cookies de propaganda nem ferramentas de rastreamento.</span>'
     '<span data-ga-on hidden>Não usamos cookies de propaganda. Só com a sua autorização, no aviso que aparece na primeira visita, usamos cookies do Google Analytics '
     'para contar visitas, saber por onde as pessoas chegam e quantas tocam no WhatsApp. Sem autorização, o Google recebe apenas contagens sem cookies. '
     'Você pode mudar a escolha a qualquer momento em <a href="#" data-cookies>preferências de cookies</a>.</span>')
JS = r"""<script>/* UC_MEDICAO_V1: visitas e cliques no WhatsApp (Google Analytics 4, modo de consentimento) + aviso de cookies */
(function(){var GA=window.UC_GA||'',K='uc_cookies';function get(){try{return localStorage.getItem(K)}catch(e){return null}}function put(v){try{localStorage.setItem(K,v)}catch(e){}}
var last=location.pathname;window.ucTrack=function(h){var p=String(h||'').split('#')[0]||'/';if(p==last)return;last=p;if(window.gtag)setTimeout(function(){gtag('event','page_view',{page_location:location.origin+p,page_path:p,page_title:document.title})},700)};
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href*="wa.me/"],a[href*="api.whatsapp.com"]');if(a&&window.gtag)gtag('event','whatsapp_click',{link_url:a.href,page_path:location.pathname,link_text:(a.textContent||'').trim().slice(0,60),transport_type:'beacon'})},true);
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-cookies]');if(!b)return;e.preventDefault();show()});
function decide(v){put(v);if(window.gtag)gtag('consent','update',{analytics_storage:v=='sim'?'granted':'denied'});var c=document.getElementById('ucck');if(c)c.remove()}
function show(){if(!GA||document.getElementById('ucck'))return;var d=document.createElement('div');d.className='cookie';d.id='ucck';d.setAttribute('role','dialog');d.setAttribute('aria-label','Aviso de cookies');
d.innerHTML='<p>Usamos cookies do Google Analytics para contar visitas e melhorar a loja, só se você autorizar. <a href="/privacidade">Política de privacidade</a></p><div><button type="button" data-v="nao">Recusar</button><button type="button" class="ok" data-v="sim">Aceitar</button></div>';
d.addEventListener('click',function(e){var b=e.target.closest('button[data-v]');if(b)decide(b.dataset.v)});document.body.appendChild(d)}
if(GA){var c=get();if(c=='sim'&&window.gtag)gtag('consent','update',{analytics_storage:'granted'});else if(c!='nao')setTimeout(show,1200)}})();
</script>
</body>"""
i = s.rfind('</body>'); s = s[:i] + JS + s[i + len('</body>'):]
open(F, 'w', encoding='utf-8').write(s); print('ok')
