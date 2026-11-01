"""Offline static review. Findings are evidence, not a zero-egress proof."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'/'vendor'))
from quick_validate import validate_skill
TEXT_SUFFIXES={'.md','.py','.sh','.ps1','.js','.mjs','.cjs','.html','.css','.svg','.yaml','.yml','.json','.toml'}
URL=re.compile(r'(?:https?|wss?|ftp)://[^\s<>"\x27`)\\]+')
NETWORK_CALL=re.compile(r'\b(?:requests\.(?:get|post|request)|urllib\.request\.urlopen|httpx\.(?:get|post|request)|socket\.(?:create_connection|getaddrinfo)|(?:session|client)\.(?:get|post)|(?:page|context)\.(?:goto|route|route_web_socket)|WebSocket|EventSource)\s*\(|(?<![.\w])fetch\s*\(')
REMOTE_GIT=re.compile(r'\b(?:git\s+(?:pull|push|fetch|clone|ls-remote)|gh\s+(?:pr|api|issue|run))\b')
BOOTSTRAP=re.compile(r'\b(?:npx\s+|npm\s+(?:install|ci)\b|pnpm\s+(?:install|add)\b|yarn\s+add\b|(?:curl|wget)\s+|(?:python\S*\s+-m\s+)?pip\s+install\b|uv\s+(?:add|sync|run)\b|poetry\s+install\b|playwright\s+install\b)')

def external_url(value):
    import ipaddress
    host=urlsplit(value).hostname
    if not host or host=='localhost':return False
    try:return not ipaddress.ip_address(host).is_loopback
    except ValueError:return True

def scan_text(relative,text):
    findings=[];fenced=False;markdown=Path(relative).suffix=='.md'
    def add(number,category,line):findings.append({'file':relative,'line':number,'category':category,'text':line.strip()[:350]})
    for number,line in enumerate(text.splitlines(),1):
        if markdown and re.match(r'^\s*(```|~~~)',line):fenced=not fenced;continue
        code=not markdown or fenced
        comment=line.lstrip().startswith(('#','//','<!--'))
        public=[m.group() for m in URL.finditer(line) if external_url(m.group())]
        if Path(relative).suffix=='.svg' and 'xmlns=' in line:
            public=[u for u in public if u!='http://www.w3.org/2000/svg']
        if public:
            category='public-url-in-code' if code and not comment else 'inert-source-link'
            if re.search(r'(?:src|href)\s*=|@import|url\s*\(|!\[',line):category='external-page-resource'
            if re.search(r'`[^`]*\b(?:open|goto|tab-new|navigate|fetch|download)\s+https?://',line,re.I) and not comment:category='public-url-in-code'
            if re.match(r'^\s*(?:\[\^[^]]+\]:|\[[^]]+\]\(https?://)',line):category='inert-source-link'
            add(number,category,line)
        if code and not comment:
            if REMOTE_GIT.search(line):add(number,'remote-git-or-forge',line)
            if BOOTSTRAP.search(line) and '--no-index' not in line and '--offline' not in line:add(number,'online-bootstrap',line)
            if NETWORK_CALL.search(line):add(number,'network-api-review',line)
        if markdown and re.search(r'^\| (?:Fetch a URL|Search the web).*\b(?:web_fetch|web_extract|web_search|google_web_search)\b',line):add(number,'online-tool-mapping',line)
        if markdown and re.search(r'^\s*(?:\d+\.\s*)?(?:Fetch (?:fresh|the latest|guidelines)|Use WebFetch to retrieve)',line,re.I):add(number,'online-rule-fetch',line)
    return findings

def inventory(path):
    findings=[]
    for file in sorted(path.rglob('*')):
        if not file.is_file() or file.suffix not in TEXT_SUFFIXES:continue
        try:content=file.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:continue
        findings+=scan_text(file.relative_to(path).as_posix(),content)
    return findings

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    records=json.loads((ROOT/'skills.lock.json').read_text(encoding='utf-8'))
    review_file=ROOT/'audit'/'reviewed-network-surfaces.json'
    reviewed=json.loads(review_file.read_text(encoding='utf-8')) if review_file.is_file() else {}
    result={'scope':f'{len(records)} selected skill trees and first-party runtime Python adapters; raw sources, binaries and vendored dependencies are not certified network-free','scanner_revision':2,'skills':[],'runtime':[],'errors':[],
            'limits':['Static patterns do not prove absence of dynamically constructed requests.','Native OpenSpec and vendored Python/Node libraries retain network-capable code.','Only documented launch paths are approved; this is not an OS firewall.']}
    files=[]
    def classify(findings,base):
        for finding in findings:
            path=base/finding['file'];key=path.relative_to(ROOT).as_posix()
            if finding['category']=='inert-source-link':finding['disposition']='source-only; do not fetch'
            elif finding['category']=='network-api-review':
                entry=reviewed.get(key,{})
                if entry.get('sha256')==digest(path):finding['disposition']='reviewed: '+entry['reason']
                else:result['errors'].append({**finding,'file':key,'error':'Network API requires content-pinned manual review'})
            else:result['errors'].append({**finding,'file':key,'error':'Unresolved network directive/resource'})
    for record in records:
        folder=ROOT/record['profile']/record['name']
        valid,message=validate_skill(folder)
        if not valid:result['errors'].append({'skill':record['name'],'error':message})
        for py in folder.rglob('*.py'):
            try:ast.parse(py.read_text(encoding='utf-8-sig'),filename=str(py))
            except SyntaxError as error:result['errors'].append({'file':str(py.relative_to(ROOT)),'error':str(error)})
        original=ROOT/'upstream'/record['repo'].replace('/','--')/record['source_path']
        after=inventory(folder);classify(after,folder)
        result['skills'].append({**record,'format_valid':valid,'before_findings':inventory(original) if original.is_dir() else [],'after_findings':after})
        files += [{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)} for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    for path in sorted((ROOT/'runtime').glob('*.py'))+sorted((ROOT/'runtime'/'guard').glob('*.py'))+[ROOT/'tools'/'local_with_server.py']:
        ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
        findings=scan_text(path.relative_to(ROOT).as_posix(),path.read_text(encoding='utf-8-sig'))
        classify(findings,ROOT);result['runtime']+=findings
        files.append({'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path)})
    output=ROOT/'audit';output.mkdir(exist_ok=True)
    (output/'network-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'skill-files.sha256.json').write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')
    print(f"Skills: {len(records)}; files hashed (skills and adapters): {len(files)}; unresolved findings/errors: {len(result['errors'])}")
    if result['errors']:print(json.dumps(result['errors'],ensure_ascii=False,indent=2));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
