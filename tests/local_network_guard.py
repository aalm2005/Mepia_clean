"""Bloqueo de red y configuración privada, exclusivamente para pruebas locales."""
import ipaddress
import json
import os
from pathlib import Path
import socket

_installed = False


def local(host):
    if host in (None, '', 'localhost'):
        return True
    if isinstance(host, bytes):
        host = host.decode('ascii', errors='replace')
    try:
        return ipaddress.ip_address(str(host).split('%')[0]).is_loopback
    except ValueError:
        return False


def record(event):
    directory = os.environ.get('MEPIA_NETWORK_AUDIT_DIR')
    if directory:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        with (path / f'python-{os.getpid()}.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'event': event, 'pid': os.getpid()}) + '\n')


def install():
    global _installed
    if _installed:
        return
    _installed = True
    original, original_ex, resolve = socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo

    def check(address):
        # Socketpair/IPC is local; inet connections require an explicit loopback.
        if isinstance(address, tuple) and not local(address[0]):
            record('external_connect_blocked')
            raise RuntimeError('MEPIA: conexión externa bloqueada en pruebas locales')

    def connect(sock, address):
        check(address)
        return original(sock, address)

    def connect_ex(sock, address):
        check(address)
        return original_ex(sock, address)

    def getaddrinfo(host, *args, **kwargs):
        if not local(host):
            record('external_dns_blocked')
            raise RuntimeError('MEPIA: resolución externa bloqueada en pruebas locales')
        return resolve(host, *args, **kwargs)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.getaddrinfo = getaddrinfo
    # Tests inject explicit configuration; never read the user's .env files.
    import dotenv
    dotenv.load_dotenv = lambda *args, **kwargs: False
    dotenv.dotenv_values = lambda *args, **kwargs: {}
    record('guard_installed')
