#!/usr/bin/env python3
"""Servidor local parecido com a Vercel: gzip, cleanUrls (/x -> x.html ou x/index.html), 404.html com status 404."""
import http.server, gzip, os, sys, mimetypes
ROOT = os.path.abspath(sys.argv[1]); PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8790; SPA = len(sys.argv) > 3 and sys.argv[3] == 'spa'
TXT = ('text/', 'application/javascript', 'application/json', 'image/svg+xml', 'application/xml')
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def resolve(self, p):
        p = p.split('?')[0].split('#')[0]
        from urllib.parse import unquote; p = unquote(p)
        cand = [p] if p.endswith('/') is False else []
        f = os.path.join(ROOT, p.lstrip('/'))
        for c in ([f] if os.path.isfile(f) else []) + [f.rstrip('/') + '.html', os.path.join(f, 'index.html')]:
            if os.path.isfile(c): return c, 200
        if SPA: return os.path.join(ROOT, 'index.html'), 200
        return os.path.join(ROOT, '404.html'), 404
    def do_GET(self):
        f, code = self.resolve(self.path)
        if not os.path.isfile(f): self.send_response(404); self.end_headers(); return
        data = open(f, 'rb').read(); ct = mimetypes.guess_type(f)[0] or 'application/octet-stream'
        if f.endswith('.webmanifest'): ct = 'application/manifest+json'
        self.send_response(code); self.send_header('Content-Type', ct + ('; charset=utf-8' if ct.startswith('text/') or 'javascript' in ct else ''))
        if ct.startswith(TXT) and 'gzip' in self.headers.get('Accept-Encoding', ''):
            data = gzip.compress(data, 6); self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(data))); self.send_header('Cache-Control', 'no-cache'); self.end_headers(); self.wfile.write(data)
http.server.ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
