"""Plan seguro del conteo ficticio. Solo --apply autoriza insertar una fila.

No altera configuracion, ventas, auditorias o documentos. No usa modelos.
"""
from pathlib import Path
from uuid import uuid5,NAMESPACE_URL
from datetime import date
import argparse,json,logging,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
FIXTURE=ROOT/'output/pdf/demo_mepia_20261014/resultados_esperados.json'


def prepare(db,apply=False):
    expected=json.loads(FIXTURE.read_text(encoding='utf-8'))
    day=expected['date'];assert date.fromisoformat(day)<=date.today(),'La fecha no puede ser futura'
    businesses=db.table('businesses').select('id,owner_id,business_name').eq('business_name',expected['business_name']).execute().data
    if len(businesses)!=1 or not businesses[0].get('owner_id'):
        raise ValueError('El negocio de demostracion debe ser unico y tener propietario')
    biz=businesses[0];bid=biz['id']
    target={'id':str(uuid5(NAMESPACE_URL,'mepia-video-cash:'+bid+':'+day)),
        'business_id':bid,'date':day,'recorded_by':biz['owner_id'],**expected['cash_count']}
    existing=db.table('cash_counts').select('*').eq('business_id',bid).eq('date',day).execute().data
    if existing:
        if len(existing)!=1 or any(existing[0].get(k)!=v for k,v in target.items()):
            raise ValueError('Ya existe otro conteo en esa fecha; no se modifica')
        return {'date':day,'already_prepared':True,'cash_rows_inserted':0,'model_calls':0}
    # Evita mezclar la preparacion con analisis o ventas anteriores de ese dia.
    for table,column in (('audit_results','date'),('pos_inputs','date'),('transactions','transaction_date')):
        if db.table(table).select('id').eq('business_id',bid).eq(column,day).execute().data:
            raise ValueError('La fecha ya tiene datos; detener y revisar antes de mezclar')
    pending=db.table('documents').select('id').eq('business_id',bid).eq('needs_human_review',True).execute().data
    if pending:raise ValueError('Hay documentos anteriores pendientes de revision; resolver antes del ensayo')
    if apply:db.table('cash_counts').insert(target).execute()
    return {'date':day,'already_prepared':False,'cash_rows_inserted':1 if apply else 0,
            'planned_cash_rows':1,'initial_float':target['initial_float'],
            'actual_counted':target['actual_counted'],'cash_payouts':target['cash_payouts'],
            'apply_requested':apply,'model_calls':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='Insertar un conteo ficticio nuevo; sin sobrescribir datos')
    args=parser.parse_args()
    from dotenv import dotenv_values
    from supabase import create_client
    from urllib.parse import urlparse
    logging.disable(logging.CRITICAL)
    cfg=dotenv_values(ROOT/'api/.env')
    if urlparse(cfg.get('SUPABASE_URL','')).hostname!='iuhadbeahmssruwuawvu.supabase.co':
        raise SystemExit('Destino distinto de MEPIA principal; sin cambios.')
    try:
        db=create_client(cfg['SUPABASE_URL'],cfg['SUPABASE_SERVICE_ROLE_KEY'])
        print(json.dumps(prepare(db,args.apply),ensure_ascii=False))
    except Exception as exc:
        # Nunca imprimir errores del proveedor, credenciales ni identificadores privados.
        if isinstance(exc,ValueError) and str(exc) in {
            'El negocio de demostracion debe ser unico y tener propietario',
            'Ya existe otro conteo en esa fecha; no se modifica',
            'La fecha ya tiene datos; detener y revisar antes de mezclar',
            'Hay documentos anteriores pendientes de revision; resolver antes del ensayo'}:
            print(str(exc))
        else:print('No se pudo preparar el conteo. Error de tipo '+type(exc).__name__+'. Sin reintento automatico.')
        raise SystemExit(1) from None


if __name__=='__main__':main()
