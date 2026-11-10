"""Consultas de análisis guardados: sesión/propietario antes de cualquier evidencia.

No importa motores ni proveedores. Una corrida por día, nunca suma indicadores.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.audit_results import restore_result

FINISHED = {'completed', 'partial', 'escalated'}
STATUSES = FINISHED | {'failed', 'running'}
# Solo escalares del negocio y día. No mezclar productos/ingredientes/canales
# cuyo identificador no está conservado en CalcResult, ni medias de recetas.
DAILY_METRICS = {
    ('conciliacion_caja', 'MXN'): 'Diferencia de caja',
    ('punto_equilibrio_diario', 'unidades/día'): 'Punto de equilibrio diario',
    ('ticket_promedio', 'MXN'): 'Ticket promedio',
    ('volumen_tickets', 'tickets'): 'Cantidad de tickets',
    ('tasa_descuento', '%'): 'Tasa de descuento',
}
TREND_LIMIT = 300

def pipeline_status(row):
    node = row.get('node_status')
    raw = row.get('result_data') or {}
    if node in ('failed', 'error', 'timeout'): return 'failed'
    status = raw.get('pipeline_status') if isinstance(raw, dict) else None
    if status in STATUSES: return status
    return 'completed' if node in ('success', 'completed') else 'unknown'

def usable(row):
    return pipeline_status(row) in FINISHED and row.get('node_status') in (None, 'success', 'completed')

def summary(row):
    return {'run_id': row['id'], 'date': row['date'], 'created_at': row.get('created_at'),
            'status': pipeline_status(row)}

def numeric(value):
    if isinstance(value, bool) or value is None: return None
    if not isinstance(value, (str, int, float, Decimal)): return None
    try:
        number = Decimal(str(value))
        # También limita la representación que puede mostrar el navegador.
        return str(number) if number.is_finite() and abs(number) <= Decimal('1e100') else None
    except (InvalidOperation, ValueError): return None

def trends_for(rows, selected, db, limited=False):
    representatives = {}
    for row in sorted(rows, key=lambda r: (r['date'], r.get('created_at') or '', r['id']), reverse=True):
        if usable(row): representatives.setdefault(row['date'], row)
    # La fecha seleccionada debe coincidir con tarjetas e informe, aun siendo anterior.
    if usable(selected): representatives[selected['date']] = selected
    days = sorted(representatives)[-90:]
    values = {}
    ignored = 0
    for day in days:
        restored = restore_result(representatives[day], db)
        results = restored['sequential_results']['calc_results']
        day_values = {}
        for result in results:
            if not isinstance(result, dict): continue
            key = (result.get('metric'), result.get('unit'))
            if key not in DAILY_METRICS:
                ignored += 1
                continue
            # Una clave repetida es ambigua: tampoco sumar ni elegir arbitrariamente.
            day_values.setdefault(key, []).append(result)
        for key, items in day_values.items():
            item = items[0]
            value = numeric(item.get('value')) if len(items) == 1 and item.get('status') in ('ok','warning','critical') else None
            values.setdefault(key, {})[day] = value
    series = []
    for key, by_day in sorted(values.items()):
        # Espacios entre fechas son explícitos: jamás se convierten en cero ni se conectan.
        points = []
        previous = None
        for day in days:
            if previous and date.fromisoformat(day) > date.fromisoformat(previous) + timedelta(days=1):
                points.append({'date': (date.fromisoformat(previous)+timedelta(days=1)).isoformat(), 'value': None, 'run_id': None})
            points.append({'date': day, 'value': by_day.get(day), 'run_id': representatives[day]['id']})
            previous = day
        count = sum(p['value'] is not None for p in points)
        series.append({'metric': key[0], 'unit': key[1], 'label': DAILY_METRICS[key],
                       'points': points, 'valid_periods': count,
                       'missing_periods': sum(p['value'] is None for p in points)})
    return {'business_id': selected['business_id'], 'run_id': selected['id'], 'series': series,
            'periods': len(days), 'limited': limited or len(representatives)>90,
            'ignored_results': ignored,
            'policy': 'Una corrida por fecha; la seleccionada en su fecha y la última terminada en las demás. No se suman resultados.'}

@dataclass
class Access:
    business_id: str
    db: object

def create_analysis_router(*, auth, db_factory):
    router = APIRouter(prefix='/business/{business_id}/analyses', tags=['Análisis guardados'])
    bearer = HTTPBearer(auto_error=False)
    def current_user(credentials: HTTPAuthorizationCredentials | None = Security(bearer)):
        if credentials is None or credentials.scheme.lower() != 'bearer':
            raise HTTPException(401, 'Inicia sesión', headers={'WWW-Authenticate':'Bearer'})
        return auth.user_id(credentials.credentials)
    def access(business_id: UUID, response: Response, user: str = Depends(current_user)):
        response.headers['Cache-Control'] = 'private, no-store'
        try: db = db_factory()
        except Exception: raise HTTPException(503, 'Análisis no disponibles. Intenta de nuevo.') from None
        bid = str(business_id)
        auth.verify_business_access(db, user, bid)
        return Access(bid, db)
    def query(scope):
        return scope.db.table('audit_results').select('*').eq('business_id',scope.business_id).eq('node_id','N05')
    def read(operation):
        try: return operation()
        except HTTPException: raise
        except Exception: raise HTTPException(503, 'No fue posible recuperar los análisis guardados. Intenta de nuevo.') from None
    def owned_run(scope, run_id):
        rows = read(lambda: query(scope).eq('id',str(run_id)).limit(1).execute().data)
        if not rows: raise HTTPException(404, 'Este análisis no existe o no corresponde al negocio seleccionado.')
        row = rows[0]
        if row.get('business_id') != scope.business_id or row.get('id') != str(run_id):
            raise HTTPException(404, 'Este análisis no existe o no corresponde al negocio seleccionado.')
        return row
    @router.get('')
    def history(page: int = Query(0,ge=0,le=100000), scope: Access = Depends(access)):
        rows = read(lambda: query(scope).order('created_at',desc=True).order('id',desc=True)
                    .range(page*25,page*25+25).execute().data)
        return {'business_id':scope.business_id, 'items':[summary(row) for row in rows[:25]],
                'next_page':page+1 if len(rows)>25 else None}
    @router.get('/latest')
    def latest(scope: Access = Depends(access)):
        # Filtrar en servidor los estados terminales fallidos; paginar sin asumir
        # que los primeros 25 sean utilizables ni truncar el historial al límite Data API.
        for page in range(100):
            rows = read(lambda: query(scope).or_('node_status.is.null,node_status.in.(success,completed)')
                        .order('created_at',desc=True).order('id',desc=True).range(page*100,page*100+99).execute().data)
            for row in rows:
                if usable(row): return {'business_id':scope.business_id, 'analysis':summary(row), 'limited':False}
            if len(rows)<100: return {'business_id':scope.business_id, 'analysis':None, 'limited':False}
        return {'business_id':scope.business_id, 'analysis':None, 'limited':True}
    @router.get('/{run_id}')
    def result(run_id: UUID, scope: Access = Depends(access)):
        row = owned_run(scope, run_id)
        result = read(lambda: restore_result(row,scope.db))
        # No cambiar el contrato del motor ni fabricar el estado de un N05 histórico.
        result['pipeline_status'] = pipeline_status(row)
        if not usable(row): result['forensic_status_available'] = False
        return result
    @router.get('/{run_id}/trends')
    def trends(run_id: UUID, scope: Access = Depends(access)):
        selected = owned_run(scope,run_id)
        rows = read(lambda: query(scope).lte('date',selected['date']).order('date',desc=True)
                    .order('created_at',desc=True).order('id',desc=True).limit(TREND_LIMIT+1).execute().data)
        return read(lambda: trends_for(rows[:TREND_LIMIT],selected,scope.db,len(rows)>TREND_LIMIT))
    @router.get('/{run_id}/layer3')
    def layer3(run_id: UUID, scope: Access = Depends(access)):
        row = owned_run(scope,run_id)
        parent = ((row.get('result_data') or {}).get('escalation') or {}).get('layer2_run_id')
        if not parent: raise HTTPException(404,'Este análisis no tiene informe avanzado.')
        from agents.layer3_execution import get_layer3_failure_by_parent, get_layer3_failure
        failure = get_layer3_failure_by_parent(parent)
        if failure: return failure
        def nodes(node):
            return (scope.db.table('audit_results').select('*').eq('business_id',scope.business_id)
                    .eq('node_id',node))
        starts = read(lambda: nodes('N10').eq('result_data->>layer2_run_id',parent)
                      .order('created_at',desc=True).limit(1).execute().data)
        if not starts: raise HTTPException(404,'El informe avanzado aún no ha iniciado.')
        lid = (starts[0].get('result_data') or {}).get('layer3_run_id')
        if not lid: raise HTTPException(404,'El informe avanzado aún no ha iniciado.')
        failure = get_layer3_failure(lid)
        if failure: return failure
        finals = read(lambda: nodes('N14').eq('result_data->>layer3_run_id',lid)
                      .order('created_at',desc=True).limit(1).execute().data)
        if finals:
            final=finals[0]
            return {'layer3_run_id':lid,'status':'completed' if final.get('node_status') in ('success','completed') else 'failed',
                    'draft_status':(final.get('result_data') or {}).get('draft_status')}
        return {'layer3_run_id':lid,'status':'running'}
    return router
