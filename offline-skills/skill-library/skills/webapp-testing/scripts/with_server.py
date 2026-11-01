"""Offline replacement for webapp-testing's shell-based server helper."""
import argparse
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import tempfile
import time

def python_command(text):
    parts=shlex.split(text,posix=True)
    if not parts or Path(parts[0]).name.lower() not in ('python','python3','python.exe','python3.exe'):
        raise ValueError('Only local Python server commands are supported by this offline helper')
    if any(p in ('&&',';','|') for p in parts):raise ValueError('Shell operators are disabled')
    root=Path(__file__).resolve()
    library=next((p for p in root.parents if (p/'runtime'/'offline_python.py').is_file()),None)
    if library is None:raise RuntimeError('Keep helper inside the portable skill-library directory')
    sys.path.insert(0,str(library/'runtime'))
    from offline_python import validate_python_arguments
    validate_python_arguments(parts[1:])
    return [sys.executable,*parts[1:]]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server',action='append',required=True)
    parser.add_argument('--port',action='append',required=True,type=int)
    parser.add_argument('--timeout',type=float,default=30)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    if len(args.server)!=len(args.port) or not command:parser.error('Match servers/ports and supply a local Python test command')
    servers=[python_command(s) for s in args.server]
    command=python_command(shlex.join(command))
    # Resolve the runtime beside the installed skill library, not through the network.
    root=Path(__file__).resolve()
    library=next((p for p in root.parents if (p/'runtime'/'offline_python.py').is_file()),None)
    if library is None:raise RuntimeError('Keep helper inside the portable skill-library directory')
    sys.path.insert(0,str(library/'runtime'))
    from offline_python import environment
    processes=[]
    with tempfile.TemporaryFile() as log:
        try:
            for cmd,port in zip(servers,args.port):
                with socket.socket() as probe:
                    if probe.connect_ex(('127.0.0.1',port))==0:raise RuntimeError(f'Port {port} already in use')
                process=subprocess.Popen(cmd,env=environment(),stdout=log,stderr=log)
                processes.append(process);deadline=time.monotonic()+args.timeout
                while time.monotonic()<deadline:
                    if process.poll() is not None:raise RuntimeError('Local server exited before readiness')
                    try:
                        with socket.create_connection(('127.0.0.1',port),timeout=.2):break
                    except OSError:time.sleep(.1)
                else:raise TimeoutError('Local server readiness timed out')
            return subprocess.call(command,env=environment())
        finally:
            for process in reversed(processes):
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait()

if __name__=='__main__':raise SystemExit(main())
