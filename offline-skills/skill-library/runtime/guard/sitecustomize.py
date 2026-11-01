"""Python test-process guard: block external DNS, TCP and UDP. Not an OS firewall."""
import ipaddress
import os
import socket

def allowed(host):
    if isinstance(host,bytes):host=host.decode('ascii','replace')
    if host in ('localhost',None,''):return True
    try:return ipaddress.ip_address(str(host).split('%')[0]).is_loopback
    except ValueError:return False

def reject(host):
    log=os.environ.get('OFFLINE_NETWORK_LOG')
    if log:
        with open(log,'a',encoding='utf-8') as stream:stream.write('BLOCKED '+str(host)+'\n')
    raise PermissionError('Offline skill test process blocked a non-loopback network target')

_getaddrinfo=socket.getaddrinfo
def getaddrinfo(host,*args,**kwargs):
    if not allowed(host):reject(host)
    return _getaddrinfo(host,*args,**kwargs)
socket.getaddrinfo=getaddrinfo
_gethostbyname=socket.gethostbyname
def gethostbyname(host):
    if not allowed(host):reject(host)
    return _gethostbyname(host)
socket.gethostbyname=gethostbyname
_gethostbyname_ex=socket.gethostbyname_ex
def gethostbyname_ex(host):
    if not allowed(host):reject(host)
    return _gethostbyname_ex(host)
socket.gethostbyname_ex=gethostbyname_ex
_connect=socket.socket.connect
def connect(self,address):
    if isinstance(address,tuple) and not allowed(address[0]):reject(address[0])
    return _connect(self,address)
socket.socket.connect=connect
_connect_ex=socket.socket.connect_ex
def connect_ex(self,address):
    if isinstance(address,tuple) and not allowed(address[0]):reject(address[0])
    return _connect_ex(self,address)
socket.socket.connect_ex=connect_ex
_sendto=socket.socket.sendto
def sendto(self,*args):
    address=args[-1]
    if isinstance(address,tuple) and not allowed(address[0]):reject(address[0])
    return _sendto(self,*args)
socket.socket.sendto=sendto
