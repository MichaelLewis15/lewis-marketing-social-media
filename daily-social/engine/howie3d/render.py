import sys, json, base64, http.server, threading, functools
from playwright.sync_api import sync_playwright
D='.'
h=functools.partial(http.server.SimpleHTTPRequestHandler,directory=D); h.log_message=lambda *a:None
srv=http.server.ThreadingHTTPServer(('127.0.0.1',8765),h); threading.Thread(target=srv.serve_forever,daemon=True).start()
emblem=open(D+'/emblem.txt').read()
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for j in json.loads(sys.argv[1]):
    out=j.pop('out'); j.setdefault('emblem',emblem)
    pg=b.new_page(viewport={'width':j.get('w',1200),'height':j.get('h',1500)})
    pg.goto('http://127.0.0.1:8765/howie3d.html'); pg.wait_for_function('window.__ready')
    pg.evaluate('P=>window.renderHowie(P)', j)
    url=pg.evaluate("document.getElementById('c').toDataURL('image/png')")
    open(out,'wb').write(base64.b64decode(url.split(',')[1])); pg.close()
  b.close()
srv.shutdown()
