"""Run with Python to reopen the local, freely rotatable scene."""
from pathlib import Path
import http.server,sys,subprocess,time,urllib.request,webbrowser
ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:8931/viewer/'
if '--serve' in sys.argv:
 handler=lambda *a,**kw:http.server.SimpleHTTPRequestHandler(*a,directory=str(ROOT),**kw)
 http.server.ThreadingHTTPServer(('127.0.0.1',8931),handler).serve_forever()
else:
 def ready():
  try:
   with urllib.request.urlopen(URL,timeout=1) as response:return '门的两侧' in response.read().decode('utf-8')
  except OSError:return False
 if not ready():
  with (ROOT/'viewer-server.log').open('ab') as log:
   subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--serve'],cwd=ROOT,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  for _ in range(30):
   if ready():break
   time.sleep(.2)
 if ready():webbrowser.open(URL)
 else:raise RuntimeError('Could not start the local viewer on port 8931.')
