"""Local-only OpenSpec launcher. Online maintenance commands are unavailable."""
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'--help','-h','--version','-V','list','show','status','instructions','new','archive','validate','schemas','templates','context','doctor','view','init'}

def validate(arguments):
    if not arguments or arguments[0] not in ALLOWED:
        raise ValueError('Offline launcher: command is not approved; no install/update/feedback/store/registry commands.')
    if any('://' in a or a=='--store' or a.startswith('--store=') for a in arguments):
        raise ValueError('Offline launcher: URLs and registered/remote stores are disabled.')
    if arguments[0]=='new' and (len(arguments)<2 or arguments[1]!='change'):
        raise ValueError('Offline launcher permits only new change, not schema acquisition.')
    if arguments[0]=='init' and '--help' not in arguments and '-h' not in arguments and '--tools' not in arguments and not any(a.startswith('--tools=') for a in arguments):
        raise ValueError('Specify local init explicitly, e.g. init --tools none; no interactive tool installation.')
    if arguments[0]=='init' and '--help' not in arguments and '-h' not in arguments:
        values=[]
        for index,arg in enumerate(arguments):
            if arg.startswith('--tools='):values.append(arg.split('=',1)[1])
            elif arg=='--tools':values.append(arguments[index+1] if index+1<len(arguments) else None)
        if values!=['none'] or any(a.startswith('--copilot-cloud') for a in arguments):
            raise ValueError('Offline init permits --tools none only; reviewed skills are supplied separately.')

def main():
    arguments=sys.argv[1:]
    try:validate(arguments)
    except ValueError as error:print(error,file=sys.stderr);return 2
    if platform.machine().lower() not in ('amd64','x86_64'):
        print('Only Windows/Linux x64 executables are bundled; no download fallback.',file=sys.stderr);return 2
    family='windows-x64' if os.name=='nt' else 'linux-x64'
    executable=ROOT/'runtime'/'openspec'/family/('openspec.exe' if os.name=='nt' else 'openspec')
    if not executable.is_file():print('Missing local OpenSpec executable; no download fallback.',file=sys.stderr);return 2
    env=os.environ.copy()
    env.update(OPENSPEC_TELEMETRY='0',DO_NOT_TRACK='1',OPENSPEC_NO_UPDATE_CHECK='1',OPENSPEC_NO_COMPLETIONS='1',CI='true',NO_COLOR='1',XDG_CONFIG_HOME=str(ROOT/'state'/'config'),XDG_DATA_HOME=str(ROOT/'state'/'data'))
    if os.name!='nt':executable.chmod(executable.stat().st_mode | 0o111)
    return subprocess.call([str(executable),*arguments],env=env)

if __name__=='__main__':raise SystemExit(main())
