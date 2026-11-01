"""Playwright context guard. Install before opening a page."""
import ipaddress
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

def local_url(url):
    parsed=urlsplit(url)
    if parsed.scheme in ('data','about','blob'):return True
    if parsed.scheme=='file':return parsed.hostname in (None,'','localhost')
    if parsed.scheme not in ('http','https','ws','wss'):return False
    if parsed.hostname=='localhost':return True
    try:return ipaddress.ip_address(parsed.hostname or '').is_loopback
    except ValueError:return False

def protect_context(context,blocked):
    # Launch contexts with service_workers='block' so worker fetches cannot bypass routing.
    def handle(route):
        if local_url(route.request.url):route.continue_()
        else:blocked.append(route.request.url);route.abort('blockedbyclient')
    context.route('**/*',handle)
    def websocket(route):
        if local_url(route.url):route.connect_to_server()
        else:
            # A routed socket is local/mock until connect_to_server is called.
            # Do not forward it. Synchronous close inside this callback can stall
            # Chromium/Playwright while the constructor is still being evaluated.
            blocked.append(route.url)
    context.route_web_socket('**/*',websocket)

def launch_local_browser(playwright,**kwargs):
    """Use an existing executable only; Playwright's download cache is not consulted."""
    configured=os.environ.get('OFFLINE_BROWSER_EXECUTABLE')
    candidates=[configured] if configured else []
    if not configured:
        candidates += [r'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',r'C:/Program Files/Google/Chrome/Application/chrome.exe']
        candidates += [shutil.which(name) for name in ('chromium','chromium-browser','google-chrome','microsoft-edge')]
    executable=next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()),None)
    if executable is None:raise RuntimeError('No local browser. Pre-provision one and set OFFLINE_BROWSER_EXECUTABLE; no download fallback.')
    arguments=kwargs.pop('args',[])+['--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run']
    return playwright.chromium.launch(executable_path=executable,headless=True,args=arguments,**kwargs)
