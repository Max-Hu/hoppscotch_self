"""Launch local Python tools with supplied dependencies and a network guard."""
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def validate_python_arguments(arguments):
    """Check interpreter options before the script/module, including combined flags."""
    if not arguments:raise ValueError('Supply a local script/module')
    index=0
    while index<len(arguments):
        arg=arguments[index]
        if arg in ('-c','-m'):
            if index+1>=len(arguments):raise ValueError('Missing code/module')
            return
        if not arg.startswith('-') or arg=='--':return
        if arg in ('-X','-W'):
            if index+1>=len(arguments):raise ValueError('Missing interpreter option value')
            if arg=='-X' and arguments[index+1]!='utf8':raise ValueError('Only -X utf8 is approved')
            index+=2;continue
        if arg not in ('-u','-B','-b','-bb','-q','-s','-v','-vv','-h','--help','-V','--version'):
            raise ValueError('Unapproved interpreter flag; startup-guard bypass is disabled')
        index+=1

def environment():
    env=os.environ.copy()
    dependencies=ROOT/'runtime'/('python-windows' if os.name=='nt' else 'python-linux')
    paths=[ROOT/'runtime'/'guard',ROOT/'runtime',ROOT/'tools'/'vendor',dependencies]
    env['PYTHONPATH']=os.pathsep.join(str(p) for p in paths)
    env.update(PIP_NO_INDEX='1',UV_OFFLINE='1',PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',DO_NOT_TRACK='1',OPENSPEC_TELEMETRY='0',OPENSPEC_NO_UPDATE_CHECK='1')
    return env

def main():
    try:validate_python_arguments(sys.argv[1:])
    except ValueError as error:print(error,file=sys.stderr);return 2
    return subprocess.call([sys.executable,*sys.argv[1:]],env=environment())

if __name__=='__main__':raise SystemExit(main())
