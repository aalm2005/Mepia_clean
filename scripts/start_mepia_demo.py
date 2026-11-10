"""Arranca MEPIA con datos ficticios en memoria; Ctrl+C detiene la demo.

El gateway simula escrituras de análisis, sin alterar los proxies del producto.
La UI/lecturas/chat/ajustes son reales con Auth/DB/proveedores de prueba.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.test_mepia_local import environment


def available(port):
    with socket.socket() as probe:probe.bind(('127.0.0.1',port))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',default=shutil.which('node'))
    parser.add_argument('--build-dir',type=Path,help='Build aislado ya validado con Supabase local 8025')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    out=(args.output or ROOT/'.test_tmp'/('demo_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'))).resolve()
    if not out.is_relative_to((ROOT/'.test_tmp').resolve()):parser.error('Salida debe estar en .test_tmp')
    for port in (8025,3036,3037):available(port)
    out.mkdir(parents=True,exist_ok=False)
    env=environment(out)
    build=args.build_dir.resolve() if args.build_dir else out/'build'/'next'
    if not build.is_relative_to((ROOT/'.test_tmp').resolve()):parser.error('Build debe estar en .test_tmp')
    if not (build/'BUILD_ID').exists():
        print('Preparando la interfaz de demostración...',flush=True)
        subprocess.run([args.node,'tests/local_build.cjs',str(build.parent)],cwd=ROOT,env=env,check=True)
    proof=build.parent/'report.json'
    if not proof.exists() or json.loads(proof.read_text(encoding='utf-8')).get('public_backend_origin')!='http://127.0.0.1:8025':
        parser.error('No reutilizar un build sin constancia de Supabase sintético local en 8025')
    env['MEPIA_NEXT_DIST_DIR']=str(build.relative_to(ROOT))
    children=[];logs=[]
    commands=[('api',[sys.executable,'-B','-m','uvicorn','tests.mepia_demo_server:app','--host','127.0.0.1','--port','8025','--no-access-log']),
              ('ui',[args.node,'node_modules/next/dist/bin/next','start','--hostname','127.0.0.1','--port','3036']),
              ('gateway',[sys.executable,'-B','-m','uvicorn','tests.mepia_demo_gateway:app','--host','127.0.0.1','--port','3037','--no-access-log'])]
    try:
        for name,command in commands:
            log=(out/(name+'.log')).open('w',encoding='utf-8');logs.append(log)
            children.append(subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
        for attempt in range(90):
            if any(child.poll() is not None for child in children):raise RuntimeError('Un proceso de demostración terminó; revisa los registros locales')
            try:
                with urlopen('http://127.0.0.1:3037/login',timeout=2) as response:
                    if response.status==200:break
            except OSError:time.sleep(1)
        else:raise RuntimeError('La demostración no estuvo disponible a tiempo')
        (out/'session.json').write_text(json.dumps({'demo':True,'url':'http://127.0.0.1:3037/__demo__','pids':[c.pid for c in children],'real_provider_calls':0}),encoding='utf-8')
        print('DEMOSTRACIÓN lista: http://127.0.0.1:3037/__demo__\nDatos ficticios y temporales; cero API reales. Ctrl+C para detener.',flush=True)
        while all(child.poll() is None for child in children):time.sleep(1)
    except KeyboardInterrupt:print('Deteniendo la demostración...',flush=True)
    finally:
        for child in children:
            if child.poll() is None:
                if os.name=='nt':subprocess.run(['taskkill.exe','/pid',str(child.pid),'/t','/f'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                else:child.terminate()
        for log in logs:log.close()


if __name__=='__main__':main()
