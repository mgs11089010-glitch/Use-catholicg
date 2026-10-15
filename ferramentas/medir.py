#!/usr/bin/env python3
"""Mede como o Lighthouse no celular: 4G lento (562,5 ms, 1,47 Mbps) e CPU 4x mais lenta. Uso: python3 medir.py URL [vezes]"""
import asyncio, sys, json
from playwright.async_api import async_playwright
URL = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 2
JS = """() => new Promise(r => { const o = {}; new PerformanceObserver(l => { for (const e of l.getEntries()) o.lcp = e.startTime; }).observe({type:'largest-contentful-paint', buffered:true});
  const p = performance.getEntriesByName('first-contentful-paint')[0]; o.fcp = p ? p.startTime : null;
  let cls = 0; new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) cls += e.value; }).observe({type:'layout-shift', buffered:true});
  setTimeout(() => { o.cls = cls; const n = performance.getEntriesByType('navigation')[0]; o.load = n.loadEventEnd; o.dcl = n.domContentLoadedEventEnd;
    o.bytes = performance.getEntriesByType('resource').reduce((a, x) => a + (x.transferSize || 0), n.transferSize || 0); o.req = performance.getEntriesByType('resource').length + 1; o.tbt = window.__lt; o.cam = window.__cam; r(o); }, 1500); })"""
async def um(p):
    b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width': 412, 'height': 823}, device_scale_factor=1.75, is_mobile=True, has_touch=True,
        user_agent='Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36')
    await ctx.add_init_script("""window.__lt=0;try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt+=Math.max(0,e.duration-50)}).observe({type:'longtask'})}catch(e){}
      window.__cam=null;(function f(){const i=document.querySelector('#maisvendidas .card img');if(i&&i.complete&&i.naturalWidth&&window.__cam===null)window.__cam=performance.now();if(window.__cam===null)requestAnimationFrame(f)})();""")
    pg = await ctx.new_page(); c = await ctx.new_cdp_session(pg)
    await c.send('Network.enable'); await c.send('Network.setCacheDisabled', {'cacheDisabled': True})
    await c.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 562.5, 'downloadThroughput': 1474.56 * 1024 / 8, 'uploadThroughput': 675 * 1024 / 8})
    await c.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    await pg.route('**/*', lambda r: r.abort() if not r.request.url.startswith('http://127.0.0.1') else r.continue_())
    await pg.goto(URL, wait_until='load', timeout=120000); await pg.wait_for_timeout(2500)
    o = await pg.evaluate(JS); await b.close(); return o
async def main():
    async with async_playwright() as p:
        R = [await um(p) for _ in range(N)]
    k = lambda key: sorted(x[key] or 0 for x in R)[len(R) // 2]
    print(json.dumps({'fcp_s': round(k('fcp') / 1000, 2), 'lcp_s': round(k('lcp') / 1000, 2), 'load_s': round(k('load') / 1000, 2), 'cls': round(k('cls'), 3), 'kb': round(k('bytes') / 1024), 'req': k('req'), 'tbt_ms': round(k('tbt')), 'camisas_s': round(k('cam') / 1000, 2)}))
asyncio.run(main())
