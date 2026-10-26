#!/usr/bin/env python3
"""Gera o site estático da Use Catholic a partir de fonte/index.html (o app):
uma página pronta por endereço (início, camisas, cada camisa, cada seção e cada objeto 3D, quem somos, dúvidas...),
cada uma com título igual ao h1, descrição, endereço oficial, prévia para WhatsApp/Instagram, dados para o Google (JSON-LD)
e os produtos já escritos no HTML. Também gera sitemap.xml, robots.txt e 404.html.
Uso: python3 ferramentas/build.py            (na pasta do repositório)"""
import json, os, re, sys, threading, http.server, html, datetime, asyncio, mimetypes
from playwright.async_api import async_playwright
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FONTE = os.path.join(REPO, 'fonte', 'index.html')
CFG = json.load(open(os.path.join(REPO, 'fonte', 'site.json'), encoding='utf-8'))
BASE = CFG['base'].rstrip('/'); HOJE = datetime.date.today().isoformat()
APP = open(FONTE, encoding='utf-8').read()
PORT = 8797

# ---------- servidor local: arquivos do repositório + o app em qualquer endereço ----------
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path.split('?')[0].split('#')[0]; f = os.path.join(REPO, p.lstrip('/'))
        if os.path.splitext(p)[1] and os.path.isfile(f):
            data = open(f, 'rb').read(); ct = mimetypes.guess_type(f)[0] or 'application/octet-stream'
        else:
            data = APP.encode(); ct = 'text/html; charset=utf-8'
        self.send_response(200); self.send_header('Content-Type', ct); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
ORIG = f'http://127.0.0.1:{PORT}'

# ---------- o que o navegador devolve de cada página ----------
COLETA = r"""() => {
 const abs = u => !u ? '' : (u.startsWith('http') ? u : BASEURL + (u.startsWith('/') ? u : '/' + u));
 const limpa = el => { if (!el) return ''; const c = el.cloneNode(true);
   c.querySelectorAll('[style]').forEach(e => { e.style.removeProperty('--d'); e.style.removeProperty('--i'); e.style.removeProperty('opacity'); e.style.removeProperty('transform'); e.style.removeProperty('transition'); if (!e.getAttribute('style').trim()) e.removeAttribute('style') });
   c.querySelectorAll('.rv,.in,.ni').forEach(e => e.classList.remove('rv', 'in', 'ni'));
   c.querySelectorAll('[class=""]').forEach(e => e.removeAttribute('class'));
   return c.innerHTML };
 const vis = [...document.querySelectorAll('main [data-p]')].filter(e => !e.hidden);
 const pag = vis.length ? vis[0].dataset.p : 'inicio';
 const grades = {}; ['c1', 'c2', 'cg', ...Object.keys(OSEC).map(k => 'og-' + k)].forEach(id => { const e = document.getElementById(id); if (e) grades[id] = limpa(e) });
 const out = {pag, titulo: document.title, grades};
 const sec = document.querySelector('main section[data-p="' + pag + '"]');
 const h = pag == 'inicio' ? document.querySelector('.hero h1') : sec && sec.querySelector('h1,h2');
 out.h1 = h ? h.textContent.trim() : '';
 const p1 = sec && sec.querySelector('.sh p, .wrap > p, .wrap p'); out.lead = p1 ? p1.textContent.trim() : '';
 if (pag == 'produto') {
   out.pdg = limpa(document.getElementById('pdg')); out.pdi = limpa(document.getElementById('pdi')); out.pdm = limpa(document.getElementById('pdm'));
   const bk = document.querySelector('#produto .back'); out.back = [bk.getAttribute('href'), bk.lastChild.textContent];
   const slug = location.pathname.split('/').pop(); const id = location.pathname.startsWith('/camisas/') ? slug : 'o-' + slug; const P = CAT[id];
   const fotos = []; Object.keys(P.S || {}).forEach(k => (P.S[k] || []).forEach(u => { if (u && !u.startsWith('data:')) fotos.push(abs(u)) }));
   const desc = (document.querySelector('#pdi .pdl') || {}).textContent || P.desc || '';
   out.prod = {id, nome: P.name, obj: P.kind == 'obj', sec: P.sec || '', secNome: P.sec ? OSEC[P.sec] : '', fotos, desc: desc.trim(), cores: (P.cols || []).filter(c => c).map(c => CN[c]),
     ofertas: P.kind == 'obj' ? oks(P).map(z => ({nome: OSZ[z].n, alt: ohh(P, z), preco: opr2(P, z)})) : [{nome: 'Camisa', preco: P.price}],
     alt: P.kind == 'obj' ? oalt(P) : 'Tamanhos P, M, G e GG'};
 }
 if (pag.startsWith('obj-')) { const k = pag.slice(4); out.lista = OBJ.filter(o => o.sec == k).map(o => ({nome: o.nome, url: '/objetos-3d/' + k + '/' + o.id.slice(2), preco: opr2(o, oks(o)[0]), foto: abs(o.fotos[0])})); out.secNome = OSEC[k] }
 if (pag == 'camisas' || pag == 'inicio') out.camisas = Object.keys(CAT).filter(k => CAT[k].kind != 'obj').map(k => ({nome: CAT[k].name, url: '/camisas/' + k, preco: CAT[k].price, foto: abs(((CAT[k].S || {})[CAT[k].cols[0]] || [])[0] || '')}));
 if (pag == 'faq') out.faq = [...document.querySelectorAll('#faq details')].map(d => ({q: (d.querySelector('summary') || {}).textContent || '', a: ((d.textContent || '').replace((d.querySelector('summary') || {}).textContent || '', '')).trim()})).filter(x => x.q && x.a);
 out.nObj = OBJ.length; out.nCam = Object.keys(CAT).filter(k => CAT[k].kind != 'obj').length;
 out.minObj = Math.min(...OBJ.map(o => opr2(o, oks(o)[0])));
 return out }"""

async def coletar(rotas):
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        await pg.route('**/*', lambda r: r.abort() if not r.request.url.startswith(ORIG) else r.continue_())
        await pg.goto(ORIG + '/'); await pg.wait_for_timeout(800)
        if rotas is None:
            rotas = await pg.evaluate("""() => { const r = ['/', '/camisas', '/lancamentos', '/quem-somos', '/duvidas', '/privacidade'];
              Object.keys(CAT).filter(k => CAT[k].kind != 'obj').forEach(k => r.push('/camisas/' + k));
              Object.keys(OSEC).forEach(k => r.push('/objetos-3d/' + k));
              OBJ.forEach(o => r.push('/objetos-3d/' + o.sec + '/' + o.id.slice(2)));
              return r }""")
        for r in rotas:
            await pg.goto(ORIG + r); await pg.wait_for_timeout(350)
            res[r] = await pg.evaluate(COLETA.replace('BASEURL', json.dumps(BASE)))
            assert res[r]['titulo'], r
        await b.close()
    return res

# ---------- montagem de cada página ----------
def esc(t): return html.escape(t or '', quote=True)
def corta(t, n=158):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return t if len(t) <= n else t[:n - 1].rsplit(' ', 1)[0].rstrip(',;:') + '…'
def br(v): return ('%.2f' % v).replace('.', ',')
LOJA_ID = BASE + '/#loja'
def loja():
    return {'@type': 'OnlineStore', '@id': LOJA_ID, 'name': 'Use Catholic', 'url': BASE + '/', 'logo': BASE + '/icone-512.png', 'image': BASE + '/img/og.jpg',
            'description': 'Camisas básicas católicas com estampas de santos e da Eucaristia, e objetos 3D de santos, Nossa Senhora, porta-terços e presépios.',
            'telephone': CFG['telefone'], 'email': CFG.get('email') or None, 'sameAs': [CFG['instagram']],
            'address': {'@type': 'PostalAddress', 'addressLocality': CFG['cidade'], 'addressRegion': CFG['uf'], 'addressCountry': 'BR'},
            'areaServed': {'@type': 'Country', 'name': 'Brasil'}, 'currenciesAccepted': 'BRL', 'paymentAccepted': 'Pix, cartão de crédito',
            'contactPoint': {'@type': 'ContactPoint', 'telephone': CFG['telefone'], 'contactType': 'customer service', 'availableLanguage': 'Portuguese'}}
def troca():
    return {'@type': 'MerchantReturnPolicy', 'applicableCountry': 'BR', 'returnPolicyCategory': 'https://schema.org/MerchantReturnFiniteReturnWindow', 'merchantReturnDays': 7}
def migalhas(itens):
    return {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': BASE + u} for i, (n, u) in enumerate(itens)]}
def descricao(r, d):
    pag = d['pag']
    if r == '/': return f"Camisas católicas com estampas de santos e da Eucaristia por R$ 75 e {d['nObj']} objetos 3D de santos, Nossa Senhora e presépios a partir de R$ {br(d['minObj'])}. Use Catholic, {CFG['cidade']}-{CFG['uf']}. Pedido pelo WhatsApp."
    if pag == 'camisas': return 'Camisas básicas católicas: ' + ', '.join(c['nome'] for c in d['camisas']) + '. R$ 75, 2 por R$ 140 ou 3 por R$ 200. Frete grátis acima de R$ 250.'
    if pag == 'produto':
        P = d['prod']
        if P['obj']:
            mn = min(o['preco'] for o in P['ofertas'])
            return corta(f"{P['nome']} em objeto 3D ({P['alt'][0].lower() + P['alt'][1:]}). {'A partir de ' if len(P['ofertas']) > 1 else ''}R$ {br(mn)}. {P['desc']}")
        return corta(f"Camisa básica católica {P['nome']}, nas cores {', '.join(P['cores'])}, tamanhos P a GG. R$ 75, ou 3 por R$ 200. {P['desc']}")
    if pag.startswith('obj-'):
        L = d['lista']; mn = min(x['preco'] for x in L)
        return corta(f"{d['secNome']} em objeto 3D: " + ', '.join(x['nome'] for x in L) + f". A partir de R$ {br(mn)}. Use Catholic.")
    return corta(d['lead'] or d['h1'])
def cabeca(r, d, noindex=False):
    url = BASE + ('/' if r == '/' else r); pag = d['pag']; titulo = d['titulo']; desc = descricao(r, d)
    img, iw, ih, tipo = BASE + '/img/og.jpg', 1200, 630, 'website'
    grafo = [loja(), {'@type': 'WebSite', '@id': BASE + '/#site', 'url': BASE + '/', 'name': 'Use Catholic', 'inLanguage': 'pt-BR', 'publisher': {'@id': LOJA_ID}}]
    pagina = {'@type': 'WebPage', '@id': url + '#pagina', 'url': url, 'name': titulo, 'description': desc, 'isPartOf': {'@id': BASE + '/#site'}, 'inLanguage': 'pt-BR'}
    if pag == 'produto':
        P = d['prod']; tipo = 'product'
        if P['fotos']: img = P['fotos'][0]; iw = ih = None
        if img.endswith('.webp'):   # WhatsApp mostra melhor jpg na prévia do link
            nome = 'img/og/' + P['id'] + '.jpg'; os.makedirs(os.path.join(REPO, 'img/og'), exist_ok=True)
            from PIL import Image
            Image.open(os.path.join(REPO, img.replace(BASE + '/', ''))).convert('RGB').save(os.path.join(REPO, nome), quality=85, optimize=True, progressive=True)
            img = BASE + '/' + nome; iw = ih = 720
        if P['obj']:
            ofertas = [{'@type': 'Offer', 'name': (o['nome'] + (f", {o['alt']} cm" if o['alt'] else '')), 'price': '%.2f' % o['preco'], 'priceCurrency': 'BRL',
                        'availability': 'https://schema.org/InStock', 'itemCondition': 'https://schema.org/NewCondition', 'url': url, 'seller': {'@id': LOJA_ID}, 'hasMerchantReturnPolicy': troca()} for o in P['ofertas']]
            cat = 'Objetos 3D católicos > ' + P['secNome']; mig = [('Início', '/'), (P['secNome'], '/objetos-3d/' + P['sec']), (P['nome'], r)]
        else:
            ofertas = [{'@type': 'Offer', 'price': '75.00', 'priceCurrency': 'BRL', 'availability': 'https://schema.org/InStock', 'itemCondition': 'https://schema.org/NewCondition',
                        'url': url, 'seller': {'@id': LOJA_ID}, 'hasMerchantReturnPolicy': troca()}]
            cat = 'Camisas católicas'; mig = [('Início', '/'), ('Camisas', '/camisas'), (P['nome'], r)]
        grafo.append({'@type': 'Product', '@id': url + '#produto', 'name': P['nome'], 'description': desc, 'image': P['fotos'][:6] or [BASE + '/img/og.jpg'], 'sku': P['id'],
                      'brand': {'@type': 'Brand', 'name': 'Use Catholic'}, 'category': cat, 'url': url, 'offers': ofertas if len(ofertas) > 1 else ofertas[0]})
        grafo.append(migalhas(mig)); pagina['@type'] = 'ItemPage'
    elif pag.startswith('obj-') or pag == 'camisas':
        L = d['lista'] if pag.startswith('obj-') else d['camisas']
        grafo.append({'@type': 'ItemList', 'name': d['h1'], 'numberOfItems': len(L), 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': BASE + x['url'], 'name': x['nome']} for i, x in enumerate(L)]})
        grafo.append(migalhas([('Início', '/'), (d['h1'], r)])); pagina['@type'] = 'CollectionPage'
        if pag.startswith('obj-') and L and L[0].get('foto'): img = L[0]['foto']; iw = ih = None
    elif pag == 'faq' and d.get('faq'):
        grafo.append({'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q['q'].strip(), 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'\s+', ' ', q['a'])}} for q in d['faq']]})
    if pag not in ('produto',): grafo.append(pagina)
    ld = json.dumps({'@context': 'https://schema.org', '@graph': grafo}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    h = [f'<title>{esc(titulo)}</title>', f'<meta name="description" content="{esc(desc)}">', f'<link rel="canonical" href="{url}">']
    if noindex: h.append('<meta name="robots" content="noindex, follow">')
    else: h.append('<meta name="robots" content="index, follow, max-image-preview:large">')
    h += ['<meta property="og:site_name" content="Use Catholic">', '<meta property="og:locale" content="pt_BR">', f'<meta property="og:type" content="{tipo}">',
          f'<meta property="og:title" content="{esc(titulo)}">', f'<meta property="og:description" content="{esc(desc)}">', f'<meta property="og:url" content="{url}">',
          f'<meta property="og:image" content="{esc(img)}">', f'<meta property="og:image:alt" content="{esc(d["h1"] or "Use Catholic")}">']
    if iw: h += [f'<meta property="og:image:width" content="{iw}">', f'<meta property="og:image:height" content="{ih}">']
    h += ['<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{esc(titulo)}">', f'<meta name="twitter:description" content="{esc(desc)}">', f'<meta name="twitter:image" content="{esc(img)}">']
    if CFG.get('gsc'): h.append(f'<meta name="google-site-verification" content="{esc(CFG["gsc"])}">')
    if CFG.get('ga_id'):
        g = esc(CFG['ga_id'])
        h.append(f"<script>window.UC_GA='{g}';window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('consent','default',{{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',wait_for_update:500}});gtag('js',new Date());gtag('config','{g}');</script>"
                 f'<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>')
    h.append(f'<script type="application/ld+json">{ld}</script>')
    return '\n'.join(h), desc

def montar(r, d, grades, noindex=False):
    s = APP; pag = d['pag']
    head, desc = cabeca(r, d, noindex)
    s = re.sub(r'<!--SEO-->.*?<!--/SEO-->', lambda m: head, s, count=1, flags=re.S)
    # produtos já escritos no HTML (o app redesenha por cima quando carrega)
    for gid, inner in grades.items():
        s, n = re.subn(r'(<div\b[^>]*\bid="' + gid + r'"[^>]*>)(</div>)', lambda m: m.group(1) + inner + m.group(2), s, count=1); assert n == 1, gid
    for k in [x[3:] for x in grades if x.startswith('og-')]:
        if grades['og-' + k]:
            i = s.index('id="obj-' + k + '"'); j = s.index('</section>', i); seg = s[i:j]
            seg = re.sub(r'<div class="empty3"[^>]*>.*?</div></div>', '', seg, count=1, flags=re.S)
            seg = re.sub(r'(class="omore")\s*hidden', r'\1', seg, count=1); s = s[:i] + seg + s[j:]
    if pag == 'produto':
        for gid in ('pdg', 'pdi', 'pdm'):
            s, n = re.subn(r'(<div\b[^>]*\bid="' + gid + r'"[^>]*>)(</div>)', lambda m: m.group(1) + d[gid] + m.group(2), s, count=1); assert n == 1, gid
        s = s.replace('<a class="back" href="/camisas"><svg class="i il" aria-hidden="true"><use href="#i-ar"/></svg>Camisas</a>',
                      f'<a class="back" href="{d["back"][0]}"><svg class="i il" aria-hidden="true"><use href="#i-ar"/></svg>{esc(d["back"][1])}</a>', 1)
    # só a página certa aparece
    def vis(m):
        tag = m.group(0); p = re.search(r'data-p="([^"]+)"', tag).group(1)
        tag = re.sub(r'\s+hidden(?=[\s>])', '', tag)
        return tag if p == pag else tag[:-1] + ' hidden>'
    s = re.sub(r'<(?:section|div)\b[^>]*\bdata-p="[^"]+"[^>]*>', vis, s)
    if pag != 'inicio':
        # um h1 só: o título da página; o do topo vira um título equivalente sem ser h1
        s = re.sub(r'<h1>(<span class="hk">.*?</span><span class="hv">.*?</span>)</h1>', r'<div class="hx">\1</div>', s, count=1, flags=re.S)
        if pag != 'produto':
            i = s.index(f'data-p="{pag}"'); j = s.index('<h2', i); k = s.index('</h2>', j)
            s = s[:j] + '<h1' + s[j + 3:k] + '</h1>' + s[k + 5:]
    # política de privacidade conforme a medição
    if CFG.get('ga_id'):
        s = s.replace('<span data-ga-off>', '<span data-ga-off hidden>').replace('<span data-ga-on hidden>', '<span data-ga-on>')
    return s, desc

def salvar(r, s):
    f = os.path.join(REPO, 'index.html' if r == '/' else r.strip('/') + '.html')
    os.makedirs(os.path.dirname(f), exist_ok=True); open(f, 'w', encoding='utf-8').write(s)

APPS = ['/sacola', '/finalizar', '/pedido', '/entrar', '/conta', '/redefinir', '/aprovar', '/agenda']
def main():
    dados = asyncio.run(coletar(None)); grades = dados['/']['grades']
    feitos = []
    for r, d in dados.items():
        s, desc = montar(r, d, grades); salvar(r, s); feitos.append((r, d['titulo'], d['h1'], desc))
    apps = asyncio.run(coletar(APPS))
    for r, d in apps.items():
        s, _ = montar(r, d, grades, noindex=True); salvar(r, s)
    # mapa do site e robots
    pri = lambda r: '1.0' if r == '/' else '0.9' if r.count('/') == 1 else '0.8' if r.count('/') == 2 else '0.7'
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for r, d in dados.items():
        u = BASE + ('/' if r == '/' else r); xml.append(f'  <url><loc>{u}</loc><lastmod>{HOJE}</lastmod><priority>{pri(r)}</priority>')
        if d['pag'] == 'produto':
            for f in d['prod']['fotos'][:4]: xml.append(f'    <image:image><image:loc>{esc(f)}</image:loc></image:image>')
        xml.append('  </url>')
    xml.append('</urlset>'); open(os.path.join(REPO, 'sitemap.xml'), 'w').write('\n'.join(xml) + '\n')
    open(os.path.join(REPO, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\n' + ''.join(f'Disallow: {a}\n' for a in APPS) + f'\nSitemap: {BASE}/sitemap.xml\n')
    # resumo para assistentes de IA (llms.txt)
    L = ['# Use Catholic', '', f"> Loja online de camisas básicas católicas e objetos 3D com temas da fé, de {CFG['cidade']}-{CFG['uf']}. Pedido pelo site ou pelo WhatsApp {CFG['telefone']}.", '',
         '## Condições', '- Camisas: 1 por R$ 75, 2 por R$ 140, 3 por R$ 200 (pode misturar estampas e cores). Tamanhos P, M, G e GG.',
         f"- Objetos 3D: {dados['/']['nObj']} peças, a partir de R$ {br(dados['/']['minObj'])}. Santos e Nossa Senhora em 7, 10 e 15 cm.",
         '- Pagamento: Pix ou cartão de crédito em até 3x, com juros no cartão (taxa da maquininha: 3,15% à vista, 5,39% em 2x, 6,12% em 3x).', '- Frete grátis acima de R$ 250. O prazo depende da região e aparece antes de finalizar.',
         '- Troca em até 7 dias depois de receber, com a peça sem uso.', '- Encomendas: objetos 3D que não estão no site podem ser pedidos pelo WhatsApp.', '',
         '## Camisas']
    for c in dados['/camisas']['camisas']: L.append(f"- [{c['nome']}]({BASE}{c['url']}): camisa básica católica, R$ {br(c['preco'])}")
    for r, d in dados.items():
        if d['pag'].startswith('obj-'):
            L += ['', f"## Objetos 3D: {d['secNome']}"] + [f"- [{x['nome']}]({BASE}{x['url']}): a partir de R$ {br(x['preco'])}" for x in d['lista']]
    L += ['', '## Páginas', f'- [Quem somos]({BASE}/quem-somos)', f'- [Dúvidas frequentes]({BASE}/duvidas)', f'- [Política de privacidade]({BASE}/privacidade)', f"- [Instagram]({CFG['instagram']})", '']
    open(os.path.join(REPO, 'llms.txt'), 'w', encoding='utf-8').write('\n'.join(L))
    srv.shutdown()
    print(f'{len(feitos)} páginas para o Google + {len(apps)} páginas da loja (sem indexar)')
    for r, t, h, desc in feitos: print(f'  {r:55s} | {t}')
if __name__ == '__main__': main()
