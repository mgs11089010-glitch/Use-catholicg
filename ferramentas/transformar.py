#!/usr/bin/env python3
"""Transformação única do index.html da Use Catholic (diagnóstico MXC, out/2026):
- fotos embutidas viram arquivos em /img (webp leve, com versão de 400 px para os cartões)
- navegação por endereço real (/camisas, /objetos-3d/santos, ...) no lugar de "#", aceitando os links antigos
- título do topo com marca e serviço; h1 nas páginas; fontes sem travar a pintura; cabeçalho SEO marcado para o build
Uso: python3 transformar.py /home/claude/use-catholicg"""
import re, sys, os, base64, io, hashlib
from PIL import Image
ROOT = sys.argv[1]; F = os.path.join(ROOT, 'index.html')
s = open(F, encoding='utf-8').read()
assert 'UC_ROTAS_V1' not in s, 'já transformado'
def sub1(a, b, cnt=1):
    global s
    n = s.count(a)
    assert n == cnt, f'esperado {cnt}x, achou {n}x: {a[:90]!r}'
    s = s.replace(a, b)

# ---------- 1. fotos para arquivos ----------
os.makedirs(os.path.join(ROOT, 'img/camisas'), exist_ok=True)
def b64(m): return base64.b64decode(m)
# logo (aparece 2x) e ostensório do topo
logo_re = re.compile(r'data:image/png;base64,([A-Za-z0-9+/=]+)')
pngs = logo_re.findall(s); assert len(pngs) == 3
for raw in set(pngs):
    im = Image.open(io.BytesIO(b64(raw))).convert('RGBA')
    if im.size == (260, 396):
        im.resize((122, 186), Image.LANCZOS).save(os.path.join(ROOT, 'img/logo.png'), optimize=True)
        im.resize((122, 186), Image.LANCZOS).save(os.path.join(ROOT, 'img/logo.webp'), quality=92, method=6)
        s = s.replace('data:image/png;base64,' + raw, '/img/logo.png')
    else:
        im.save(os.path.join(ROOT, 'img/ostensorio.webp'), quality=88, method=6)
        s = s.replace('data:image/png;base64,' + raw, '/img/ostensorio.webp')
# camisas: var XX={w:[5 fotos],k:[...],b:[...]}
NOMES = {'SB': 'sao-bento', 'ST': 'santa-teresinha', 'CC': 'corpo-de-cristo', 'VM': 'virgem-da-medalha-milagrosa', 'GP': 'gratia-plena'}
CORES = {'w': 'branca', 'k': 'preta', 'b': 'azul'}
total = 0
for var, nome in NOMES.items():
    m = re.search(r'var ' + var + r'=(\{.*?\});', s, re.S); assert m, var
    bloco = m.group(1); novo = bloco
    for cor, lista in re.findall(r'([wkb]):\[(.*?)\]', bloco, re.S):
        uris = re.findall(r'"(data:image/webp;base64,[^"]+)"', lista); assert len(uris) == 5, (var, cor, len(uris))
        for i, u in enumerate(uris, 1):
            im = Image.open(io.BytesIO(b64(u.split(',', 1)[1])))
            base = f'img/camisas/{nome}-{CORES[cor]}-{i}'
            open(os.path.join(ROOT, base + '.webp'), 'wb').write(b64(u.split(',', 1)[1]))
            im.convert('RGB').resize((400, 400), Image.LANCZOS).save(os.path.join(ROOT, base + '-400.webp'), quality=80, method=6)
            novo = novo.replace(u, '/' + base + '.webp'); total += 1
    s = s.replace(bloco, novo)
assert total == 45, total
assert 'data:image/webp' not in s and 'data:image/png' not in s
print('fotos tiradas da página:', total + 3)

# ---------- 2. cabeçalho: fontes sem travar a pintura + marcadores SEO ----------
sub1('<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;1,500&display=swap" rel="stylesheet">',
     '<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;1,500&display=swap" onload="this.onload=null;this.rel=\'stylesheet\'">'
     '<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;1,500&display=swap"></noscript>')
m = re.search(r'<title>[^<]*</title>', s); s = s.replace(m.group(0), '<!--SEO-->' + m.group(0) + '<!--/SEO-->')
m = re.search(r'<meta name="description"[^>]*>', s); s = s.replace(m.group(0), '')
s = s.replace('<!--/SEO-->', '<meta name="description" content="Camisas básicas católicas com estampas de santos e da Eucaristia, e objetos 3D com temas da fé. Pedido pelo WhatsApp."><!--/SEO-->')

# ---------- 3. topo: h1 com marca e serviço ----------
sub1('<div><h1>Vista a sua fé.</h1>', '<div><h1><span class="hk">Use Catholic · Camisas católicas e objetos 3D</span><span class="hv">Vista a sua fé.</span></h1>')
sub1("var t=document.querySelector('.hero h1'),x=t.textContent;", "var t=document.querySelector('.hero .hv'),x=t.textContent;")
# CSS: estilos da linha pequena, do título alternativo do topo (.hx) e dos h1 das páginas internas iguais aos h2
css_add = ('.hero h1 .hk{display:block;font-size:13px;line-height:1.4;letter-spacing:.14em;text-transform:uppercase;font-weight:500;opacity:.72;margin:0 0 16px}'
           '.hero h1 .hv{display:block}'
           '.hero .hx{font-family:Poppins,system-ui,sans-serif;margin:0;line-height:1.05;font-size:clamp(42px,6.4vw,84px);letter-spacing:-.03em;font-weight:700;text-wrap:balance}'
           '.hero .hx .hk{display:block;font-size:13px;line-height:1.4;letter-spacing:.14em;text-transform:uppercase;font-weight:500;opacity:.72;margin:0 0 16px}.hero .hx .hv{display:block}.hero .hx .w{display:inline-block;margin-right:.25em}.hero .hx .w:last-child{margin-right:0}'
           'main section h1{letter-spacing:-.02em}.sh h1,.two h1{font-size:clamp(30px,4.2vw,44px)}.faq h1{font-size:clamp(32px,4.5vw,48px)}'
           '.done h1{font-size:clamp(32px,5vw,48px);margin-bottom:12px}.about h1{font-size:clamp(34px,5.5vw,64px);max-width:16ch;margin:0 auto 22px}.pdi h1{font-size:clamp(32px,4.4vw,48px)}'
           '.cookie{position:fixed;left:16px;right:16px;bottom:16px;z-index:90;max-width:560px;margin:0 auto;background:var(--bg,#fff);color:var(--fg,#0a0a0a);border:1px solid rgba(127,127,127,.35);border-radius:14px;padding:16px 18px;box-shadow:0 12px 40px rgba(0,0,0,.18);font-size:14px;line-height:1.45;display:flex;gap:14px;align-items:center;flex-wrap:wrap}'
           '.cookie p{margin:0;flex:1 1 260px}.cookie a{color:inherit}.cookie div{display:flex;gap:8px}.cookie button{font:inherit;font-weight:600;border-radius:999px;padding:9px 16px;cursor:pointer;border:1px solid currentColor;background:transparent;color:inherit}.cookie button.ok{background:#0a0a0a;color:#fff;border-color:#0a0a0a}')
i = s.find('</style>'); s = s[:i] + css_add + s[i:]

# ---------- 4. links do HTML: "#pagina" vira endereço ----------
M = {'inicio': '/', 'camisas': '/camisas', 'lancamentos': '/lancamentos', 'sobre': '/quem-somos', 'faq': '/duvidas', 'privacidade': '/privacidade',
     'sacola': '/sacola', 'finalizar': '/finalizar', 'pedido': '/pedido', 'entrar': '/entrar', 'conta': '/conta', 'redefinir': '/redefinir', 'aprovar': '/aprovar',
     'colecoes': '/#colecoes', 'maisvendidas': '/#maisvendidas', 'lookbook': '/#lookbook'}
for k in ['santos', 'maria', 'porta-tercos', 'sagrada-familia', 'simbolos', 'presentes']: M['obj-' + k] = '/objetos-3d/' + k
def troca_href(m):
    h = m.group(2)
    return m.group(1) + 'href="' + M[h] + '"' if h in M else m.group(0)
s, n = re.subn(r'(<a\b[^>]*?\s)href="#([a-z0-9-]+)"', troca_href, s)
print('links trocados no HTML e nos textos do código:', n)

# ---------- 5. código: links gerados, grades e roteador ----------
sub1("""'<h3><a href="#camisa-'+id+'" data-col="'+col+'">'""", """'<h3><a href="/camisas/'+id+'" data-col="'+col+'">'""")
sub1("""<a class="vd" href="#camisa-'+id+'" data-col="'+col+'">""", """<a class="vd" href="/camisas/'+id+'" data-col="'+col+'">""")
sub1("href='#objeto-'+o.id.slice(2);", "href='/objetos-3d/'+o.sec+'/'+o.id.slice(2);")
sub1("""'<a href="#'+(Q.kind=='obj'?'objeto-'+k.slice(2):'camisa-'+k)+'" data-col=""", """'<a href="'+(Q.kind=='obj'?'/objetos-3d/'+Q.sec+'/'+k.slice(2):'/camisas/'+k)+'" data-col=""")
sub1("bkl.setAttribute('href',OB?'#obj-'+P.sec:'#camisas');", "bkl.setAttribute('href',OB?'/objetos-3d/'+P.sec:'/camisas');")
# nome do produto vira h1
sub1("""'</p><h2>'+esc(P.name)+'</h2><div class="pdpc"><b class="pdpb">'""", """'</p><h1>'+esc(P.name)+'</h1><div class="pdpc"><b class="pdpb">'""")
sub1("""'<p class="pdk">Camisa básica</p><h2>'+esc(P.name)+'</h2>""", """'<p class="pdk">Camisa básica</p><h1>'+esc(P.name)+'</h1>""")
# fotos dos cartões: versão de 400 px, carregando aos poucos, com tamanho reservado
sub1("""v.innerHTML=has?'<img decoding="async" src="'+S[col][side]+'" alt=""", """v.innerHTML=has?'<img decoding="async" loading="lazy" width="720" height="720"'+ucSS(S[col][side])+' src="'+S[col][side]+'" alt=""")
sub1("""function paint(){v.innerHTML='<img loading="lazy" decoding="async" src="'+F[side]+'" alt=""", """function paint(){v.innerHTML='<img loading="lazy" decoding="async" width="600" height="800" src="'+F[side]+'" alt=""")
sub1("function tee(c){", "function ucSS(u){return /^\\/img\\/camisas\\/.+\\.webp$/.test(u)?' srcset=\"'+u.replace(/\\.webp$/,'-400.webp')+' 400w, '+u+' 720w\" sizes=\"(max-width: 700px) 50vw, 340px\"':''}window.ucSS=ucSS;\nfunction tee(c){")
# grades limpas antes de montar (a página já pode vir pré-montada)
sub1("function fill(id,list,nw){var e=document.getElementById(id);list.forEach(", "function fill(id,list,nw){var e=document.getElementById(id);e.innerHTML='';list.forEach(")
sub1("var L=OBJ.filter(function(o){return o.sec==k});L.forEach(function(o){g.appendChild(ocard(o))});", "var L=OBJ.filter(function(o){return o.sec==k});g.innerHTML='';L.forEach(function(o){g.appendChild(ocard(o))});")
sub1("if(location.hash=='#conta')loadOrders();", "if(location.pathname=='/conta'||location.hash=='#conta')loadOrders();")

# roteador por endereço
old_pageof = re.search(r"function pageOf\(h\)\{.*?return\{p:null,el:el\}\}", s, re.S).group(0)
new_pageof = r"""/* UC_ROTAS_V1: endereços reais; links antigos com # continuam funcionando */
var P2={'/':'inicio','/camisas':'camisas','/lancamentos':'lancamentos','/quem-somos':'sobre','/duvidas':'faq','/privacidade':'privacidade','/sacola':'sacola','/finalizar':'finalizar','/pedido':'pedido','/entrar':'entrar','/conta':'conta','/redefinir':'redefinir','/aprovar':'aprovar'},P2R={};for(var k2 in P2)P2R[P2[k2]]=k2;
function R(h){if(!h)return '/';if(h.charAt(0)!='#')return h;var id=h.slice(1);if(P2R[id])return P2R[id];if(id.indexOf('camisa-')==0)return '/camisas/'+id.slice(7);if(id.indexOf('objeto-')==0){var o=CAT['o-'+id.slice(7)];return o?'/objetos-3d/'+o.sec+'/'+id.slice(7):'/'}if(id.indexOf('obj-')==0)return '/objetos-3d/'+id.slice(4);if(id=='colecoes'||id=='maisvendidas'||id=='lookbook')return '/#'+id;return h}
window.ucR=R;window.ucPath=function(p){return P2R[p]||null};
function pageOf(h){h=R(h);var u;try{u=new URL(h,location.href)}catch(e){return{p:null,el:null}}if(u.origin!=location.origin)return{p:null,el:null};
var path=u.pathname.replace(/\/+$/,'')||'/',id='';try{id=decodeURIComponent(u.hash.slice(1))}catch(e){}var el=id?document.getElementById(id):null,m;
if(P2[path])return{p:P2[path],el:el&&el.id!=P2[path]?el:null};
if((m=path.match(/^\/camisas\/([a-z0-9-]+)$/))&&CAT[m[1]]&&CAT[m[1]].kind!='obj')return{p:'produto',el:null,s:m[1],k:'produto:'+m[1]};
if((m=path.match(/^\/objetos-3d\/([a-z0-9-]+)$/))&&OSEC[m[1]])return{p:'obj-'+m[1],el:null};
if((m=path.match(/^\/objetos-3d\/([a-z0-9-]+)\/([a-z0-9-]+)$/))&&CAT['o-'+m[2]]&&CAT['o-'+m[2]].kind=='obj')return{p:'produto',el:null,s:'o-'+m[2],k:'produto:o-'+m[2]};
return{p:null,el:el}}"""
s = s.replace(old_pageof, new_pageof)
sub1("document.querySelectorAll('nav a').forEach(function(a){if(a.getAttribute('href')=='#'+p||(p.indexOf('obj-')==0&&a.getAttribute('href')=='#colecoes')||(p=='produto'&&a.getAttribute('href')==(window.UC_OBJ?'#colecoes':'#camisas')))",
     "document.querySelectorAll('nav a').forEach(function(a){var hp=a.getAttribute('href');if(hp==P2R[p]||(p.indexOf('obj-')==0&&hp=='/#colecoes')||(p=='produto'&&hp==(window.UC_OBJ?'/#colecoes':'/camisas')))")
sub1("""function hfocus(p,quiet){var h=p=='inicio'?main.querySelector('.hero h1'):main.querySelector('section[data-p="'+p+'"] h2');""",
     """function hfocus(p,quiet){var h=p=='inicio'?main.querySelector('.hero h1,.hero .hx'):main.querySelector('section[data-p="'+p+'"] h1,section[data-p="'+p+'"] h2');""")
sub1("function go(h,push){var r=pageOf(h);if(push){try{history.pushState(null,'',h)}catch(e){}}",
     "function go(h,push){h=R(h);var r=pageOf(h);if(push){try{history.pushState(null,'',h)}catch(e){}}if(window.ucTrack)window.ucTrack(h);")
sub1("""document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^="#"]');if(!a)return;e.preventDefault();if(a.classList.contains('skip')){main.focus({preventScroll:true});sc(main,true);return}go(a.getAttribute('href'),true)});""",
     """document.addEventListener('click',function(e){if(e.defaultPrevented||e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;var a=e.target.closest&&e.target.closest('a[href]');if(!a||(a.target&&a.target!='_self')||a.hasAttribute('download'))return;var h=a.getAttribute('href');if(!h||h=='#')return;
if(h.charAt(0)=='#'){e.preventDefault();if(a.classList.contains('skip')){main.focus({preventScroll:true});sc(main,true);return}go(h,true);return}
if(h.charAt(0)=='/'&&h.charAt(1)!='/'){var r=pageOf(h);if(!r.p&&!r.el)return;e.preventDefault();go(h,true)}});""")
sub1("window.addEventListener('popstate',function(){go(location.hash,false)});", "window.addEventListener('popstate',function(){go(location.pathname+location.hash,false)});")
sub1("var r0=pageOf(location.hash);",
     "(function(){var lh=location.hash;if(lh.length>1&&!/access_token=|error_code=|error=|type=/.test(lh)){var np=R(lh);if(np!=lh&&np.charAt(0)=='/'){try{history.replaceState(null,'',np)}catch(e){}}}})();\nvar r0=pageOf(location.pathname+location.hash);")

# títulos: aba = título visível da página
sub1("<div class=\"sh\"><div><h2>Camisas</h2><p>Todas as estampas", "<div class=\"sh\"><div><h2>Camisas católicas</h2><p>Todas as estampas")
sub1("cur=null,BT=document.title,", "cur=null,BT='Use Catholic · Camisas católicas e objetos 3D em Campina Grande-PB',")
sub1("document.title=p=='inicio'?BT:pname(p)+(p.indexOf('obj-')==0?' - Objetos 3D':'')+' | Use Catholic';", "document.title=ucTitle(p);")
m = re.search(r"function pname\(p\)\{[^\n]*?return h\?h\.textContent:''\}", s); assert m
s = s.replace(m.group(0), m.group(0).replace("section[data-p=\"'+p+'\"] h2')", "section[data-p=\"'+p+'\"] h1,section[data-p=\"'+p+'\"] h2')") + """
function ucTitle(p){if(p=='inicio')return BT;var h=main.querySelector('section[data-p="'+p+'"] h1,section[data-p="'+p+'"] h2'),t=((h&&h.textContent.trim())||NM[p]||'').replace(/\\.$/,'');var x=p.indexOf('obj-')==0?' · Objetos 3D':p=='produto'?(window.UC_OBJ?' · Objeto 3D':' · Camisa católica'):p=='sobre'?' · Quem somos':p=='faq'?' · Dúvidas':'';return t+x+' | Use Catholic'}
window.ucTitle=ucTitle;""")

# fotos dos objetos com caminho absoluto (funcionam em /objetos-3d/...)
sub1("o.fotos=o.fotos.filter(function(f){return typeof f=='string'&&/^(data:image\\/|https:\\/\\/|objetos\\/[a-z0-9-]+\\.(jpg|webp)$)/.test(f)});return o})",
     "o.fotos=o.fotos.filter(function(f){return typeof f=='string'&&/^(data:image\\/|https:\\/\\/|\\/?objetos\\/[a-z0-9-]+\\.(jpg|webp)$)/.test(f)}).map(function(f){return f.indexOf('objetos/')==0?'/'+f:f});return o})")
# link antigo com # aberto sem recarregar (popstate) também vira endereço
sub1("window.addEventListener('popstate',function(){go(location.pathname+location.hash,false)});",
     "window.addEventListener('popstate',function(){var lh=location.hash,np=lh.length>1?R(lh):lh;if(np&&np!=lh&&np.charAt(0)=='/'&&np.indexOf('/#')!=0){try{history.replaceState(null,'',np)}catch(e){}go(np,false);return}go(location.pathname+location.hash,false)});")

open(F, 'w', encoding='utf-8').write(s)
print('ok', len(s.encode()) // 1024, 'KB')
