"""Behavioral smoke tests for local skill resources and their offline adapters."""
from __future__ import annotations
import http.server
import importlib.util
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime'))
from offline_python import environment
from browser_guard import local_url

class LocalHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/status':payload=b'<span id="status">completed</span>'
        else:
            payload=b'''<!doctype html><html><body><label for="task">Task</label><input id="task"><button id="start">Start</button><div id="result"></div><script>document.querySelector('#start').onclick=async()=>{document.querySelector('#result').innerHTML=await (await fetch('/status')).text()};</script></body></html>'''
        self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(payload)
    def log_message(self,*args):pass

class OfflineLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),LocalHandler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)

    def python(self,code,timeout=30):
        try:
            return subprocess.run([sys.executable,'-u','-X','utf8','-c',code],env=environment(),capture_output=True,text=True,timeout=timeout)
        except subprocess.TimeoutExpired as error:
            print('Last subprocess output:',error.stdout,error.stderr,flush=True)
            raise

    def test_python_guard_blocks_external_dns_and_tcp(self):
        code='''import socket
blocked=0
for operation in (lambda:socket.getaddrinfo("example.invalid",443),lambda:socket.create_connection(("203.0.113.1",443),timeout=.1)):
 try:operation()
 except PermissionError:blocked+=1
assert blocked==2,blocked
print("two external operations blocked before connection")'''
        result=self.python(code);self.assertEqual(result.returncode,0,result.stderr)

    def test_guard_allows_loopback_http(self):
        result=self.python(f'import urllib.request; assert b"completed" in urllib.request.urlopen({self.base+"/status"!r}).read()')
        self.assertEqual(result.returncode,0,result.stderr)

    def test_browser_url_classifier(self):
        for url in ('http://127.0.0.1:8000','http://localhost:8000','http://[::1]:8000','file:///tmp/local.html'):
            self.assertTrue(local_url(url),url)
        for url in ('https://example.invalid','http://127.0.0.1.evil.invalid','http://localhost@evil.invalid','ws://example.invalid','file://remote-share/path'):
            self.assertFalse(local_url(url),url)

    def test_browser_form_local_update_and_external_routes(self):
        code=f'''from playwright.sync_api import sync_playwright,expect
from browser_guard import protect_context,launch_local_browser
with sync_playwright() as p:
 browser=launch_local_browser(p)
 context=browser.new_context(service_workers="block")
 blocked=[];protect_context(context,blocked)
 page=context.new_page();page.set_default_timeout(10000);page.goto({self.base!r},wait_until="domcontentloaded")
 print('browser reached local page',flush=True)
 page.get_by_label("Task").fill("offline-audit")
 page.get_by_role("button",name="Start").click()
 expect(page.locator("#status")).to_have_text("completed")
 print('local form and update complete',flush=True)
 page.evaluate("fetch('https://example.invalid/test').catch(()=>null)")
 print('external HTTP was intercepted',flush=True)
 page.evaluate("() => {{ new WebSocket('wss://example.invalid/ws'); return true; }}")
 page.wait_for_timeout(300)
 assert any(x.startswith('https://example.invalid') for x in blocked),blocked
 assert any(x.startswith('wss://example.invalid') for x in blocked),blocked
 page.screenshot(path={str(ROOT/'tests'/'browser-smoke.png')!r})
 context.close();browser.close()
print('local form and update passed; external HTTP/WebSocket blocked')'''
        result=self.python(code,timeout=60);self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_property_testing_dependency_is_local(self):
        result=self.python('from hypothesis import find,settings,strategies as st; x=find(st.lists(st.integers(0,3),min_size=2),lambda xs:len(set(xs))<len(xs),settings=settings(database=None,max_examples=100)); assert len(set(x))<len(x)')
        self.assertEqual(result.returncode,0,result.stderr)

    def test_server_helper_local_start_and_cleanup(self):
        with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        helper=ROOT/'skills'/'webapp-testing'/'scripts'/'with_server.py'
        result=subprocess.run([sys.executable,str(helper),'--server',f'python -m http.server {port} --bind 127.0.0.1','--port',str(port),'--',sys.executable,'-c',f'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:{port}").status==200'],env=environment(),capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        with socket.socket() as probe:self.assertNotEqual(probe.connect_ex(('127.0.0.1',port)),0)

    def test_server_helper_rejects_download_commands(self):
        helper=ROOT/'skills'/'webapp-testing'/'scripts'/'with_server.py'
        result=subprocess.run([sys.executable,str(helper),'--server','npx some-package','--port','12345','--','python','-c','pass'],env=environment(),capture_output=True,text=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Only local Python server commands',result.stderr)

    def test_openspec_rejects_network_commands(self):
        runner=ROOT/'runtime'/'openspec_offline.py'
        for args in (['install'],['update'],['store','list'],['status','--store','remote'],['new','change','https://example.invalid'],['init','--tools','all'],['init','--tools','none','--tools=all'],['init','--tools=none','--tools','all'],['init','--tools','none','--copilot-cloud=true']):
            result=subprocess.run([sys.executable,str(runner),*args],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2,(args,result.stdout,result.stderr))

    def test_python_launcher_rejects_combined_guard_bypass_flags(self):
        runner=ROOT/'runtime'/'offline_python.py'
        for flag in ('-I','-E','-S','-IS','-Es','-uS','-Xpresite=some_module'):
            result=subprocess.run([sys.executable,str(runner),flag,'-c','print("unexpected")'],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2,(flag,result.stdout,result.stderr))
            self.assertNotIn('unexpected',result.stdout)
        allowed=subprocess.run([sys.executable,str(runner),'-X','utf8','-c','import sys; assert sys.argv[1]=="-S"','-S'],capture_output=True,text=True,timeout=10)
        self.assertEqual(allowed.returncode,0,allowed.stderr)

    def test_server_helper_rejects_combined_guard_bypass(self):
        helper=ROOT/'skills'/'webapp-testing'/'scripts'/'with_server.py'
        result=subprocess.run([sys.executable,str(helper),'--server','python -IS -m http.server','--port','12345','--','python','-c','pass'],env=environment(),capture_output=True,text=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('startup-guard bypass is disabled',result.stderr)

    def test_scanner_detects_previous_blind_spots(self):
        spec=importlib.util.spec_from_file_location('audit_library',ROOT/'tools'/'audit_library.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        cases=[('server.cjs',"const logo = 'https://example.invalid/logo.png';",'public-url-in-code'),
               ('guide.md','```bash\npwcli open https://example.invalid\n```','public-url-in-code'),
               ('theme.css','@import "https://example.invalid/font.css";','external-page-resource'),
               ('guide.md','```sh\n  git push origin main\n```','remote-git-or-forge'),
               ('guide.md','| Search the web | `web_search` |','online-tool-mapping'),
               ('script.py','requests.get(target)','network-api-review')]
        for name,text,category in cases:
            self.assertIn(category,[f['category'] for f in module.scan_text(name,text)],(name,text))
        self.assertEqual([f['category'] for f in module.scan_text('source.md','[Source](https://example.invalid)')],['inert-source-link'])

    def test_copied_browser_examples_all_install_context_guard(self):
        import ast
        for file in (ROOT/'skills'/'webapp-testing'/'examples').glob('*.py'):
            tree=ast.parse(file.read_text(encoding='utf-8'))
            calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call)]
            self.assertFalse(any(isinstance(c.func,ast.Attribute) and isinstance(c.func.value,ast.Name) and c.func.value.id=='browser' and c.func.attr=='new_page' for c in calls),file)
            self.assertTrue(any(isinstance(c.func,ast.Name) and c.func.id=='protect_context' for c in calls),file)

    def test_visual_companion_has_local_branding_and_resource_policy(self):
        node=os.environ.get('OFFLINE_NODE_EXECUTABLE') or shutil.which('node')
        if not node:self.skipTest('Preinstalled Node required for optional visual companion check')
        server=ROOT/'skills'/'brainstorming'/'scripts'/'server.cjs'
        with tempfile.TemporaryDirectory(prefix='skill-companion-') as folder:
            env=os.environ.copy();env.update(BRAINSTORM_DIR=folder,BRAINSTORM_HOST='127.0.0.1',BRAINSTORM_URL_HOST='127.0.0.1',BRAINSTORM_TOKEN='a'*64)
            with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
            env['BRAINSTORM_PORT']=str(port)
            process=subprocess.Popen([node,str(server)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            try:
                state=Path(folder)/'state'/'server-info';deadline=time.monotonic()+10
                while not state.exists() and time.monotonic()<deadline:
                    if process.poll() is not None:self.fail(process.stderr.read().decode())
                    time.sleep(.1)
                self.assertTrue(state.exists())
                request=urllib.request.Request(f'http://127.0.0.1:{port}/',headers={'Cookie':f'brainstorm-key-{port}='+('a'*64)})
                with urllib.request.urlopen(request,timeout=5) as response:
                    html=response.read().decode();policy=response.headers['Content-Security-Policy']
                self.assertIn('Superpowers v',html)
                self.assertNotIn('primeradiant.com',html)
                self.assertNotIn('<img',html)
                self.assertIn("default-src 'self'",policy)
                self.assertIn("connect-src 'self'",policy)
            finally:
                process.terminate();process.wait(timeout=5);process.stderr.close()
            env['BRAINSTORM_HOST']='0.0.0.0'
            refused=subprocess.run([node,str(server)],env=env,capture_output=True,text=True,timeout=5)
            self.assertNotEqual(refused.returncode,0)
            self.assertIn('loopback binding',refused.stderr)

    def test_openspec_local_lifecycle(self):
        runner=ROOT/'runtime'/'openspec_offline.py'
        workspace=ROOT/'tests'/'workspaces';workspace.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='skill-openspec-',dir=workspace) as folder:
            def cli(*args):
                result=subprocess.run([sys.executable,str(runner),*args],cwd=folder,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,(args,result.stdout,result.stderr));return result.stdout
            cli('init','--tools','none','--profile','core','--no-animation')
            cli('new','change','offline-smoke')
            self.assertIn('offline-smoke',cli('status','--change','offline-smoke','--json'))
            self.assertIn('template',cli('instructions','proposal','--change','offline-smoke','--json'))
            change=Path(folder)/'openspec'/'changes'/'offline-smoke'
            (change/'proposal.md').write_text('## Why\nVerify local documentation workflow.\n\n## What Changes\n- Add a local guide.\n\n## Capabilities\n### New Capabilities\nNone.\n### Modified Capabilities\nNone.\n\n## Impact\nDocumentation only.\n')
            (change/'tasks.md').write_text('## 1. Verify\n- [x] 1.1 Local check complete\n')
            cli('archive','offline-smoke','--skip-specs','--yes')
            self.assertFalse(change.exists())
            self.assertTrue(list((Path(folder)/'openspec'/'changes'/'archive').glob('*offline-smoke')))

if __name__=='__main__':
    if len(sys.argv)>1:unittest.main(verbosity=2)
    else:
        started=time.monotonic()
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OfflineLibraryTests))
        report={'tests_run':result.testsRun,'successful':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'elapsed_seconds':round(time.monotonic()-started,3),'python':sys.version.split()[0],'platform':sys.platform,'scope':'Windows local smoke checks; no Linux execution, OS packet capture, or full agent-behavior proof'}
        (ROOT/'tests'/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        raise SystemExit(0 if result.wasSuccessful() else 1)
