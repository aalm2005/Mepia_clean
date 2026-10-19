"""Documentos reales de demo, motor y grounding; DB/modelos simulados."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import json,sys

import pytest
from agents.pos_parser import extract_pos_data
from agents.factura_parser import extract_factura_xml
from agents.gatekeeper import GatekeeperAgent
from agents.calc_engine import run_calc_engine
from agents.chat_grounding import ChatGroundingService
from scripts.prepare_video_demo import prepare, FIXTURE

OUT=FIXTURE.parent


class Query:
    def __init__(self,db,table):
        self.db,self.table=db,table;self.filters=[];self.rows=None;self.one=False;self.sorts=[];self.n=None;self.invert=False
    def select(self,*a,**kw):return self
    def eq(self,k,v):self.filters.append(lambda r:r.get(k)==v);return self
    def gte(self,k,v):self.filters.append(lambda r:str(r.get(k,''))>=str(v));return self
    def lte(self,k,v):self.filters.append(lambda r:str(r.get(k,''))<=str(v));return self
    @property
    def not_(self):self.invert=True;return self
    def is_(self,k,v):
        inverse=self.invert;self.invert=False
        self.filters.append(lambda r:(r.get(k) is None)!=inverse);return self
    def single(self):self.one=True;return self
    def order(self,k,desc=False):self.sorts.append((k,desc));return self
    def limit(self,n):self.n=n;return self
    def or_(self,value):
        assert value=='node_status.is.null,node_status.in.(success,completed)'
        self.filters.append(lambda r:r.get('node_status') in (None,'success','completed'));return self
    def insert(self,row):self.rows=row if isinstance(row,list) else [row];return self
    def upsert(self,row,**kw):return self.insert(row)
    def execute(self):
        if self.rows is not None:
            self.db.writes.append(self.table);self.db.store.setdefault(self.table,[]).extend(deepcopy(self.rows))
            return SimpleNamespace(data=deepcopy(self.rows))
        rows=[r for r in self.db.store.get(self.table,[]) if all(f(r) for f in self.filters)]
        for key,desc in reversed(self.sorts):rows=sorted(rows,key=lambda r:r.get(key,''),reverse=desc)
        if self.n is not None:rows=rows[:self.n]
        if self.one:
            assert len(rows)<=1
            return SimpleNamespace(data=deepcopy(rows[0]) if rows else None)
        return SimpleNamespace(data=deepcopy(rows))


class DB:
    def __init__(self):
        self.bid=str(uuid4());self.owner=str(uuid4());self.writes=[]
        self.store={'businesses':[{'id':self.bid,'owner_id':self.owner,'business_name':'MEPIA Dev'}]}
    def table(self,name):return Query(self,name)


def test_actual_pdf_and_xml_are_readable_and_consistent():
    pos=extract_pos_data((OUT/'01_ventas_demo_2026-10-14.pdf').read_bytes())
    assert len(pos)==1 and pos[0].date.isoformat()=='2026-10-14' and not pos[0].needs_human_review
    assert pos[0].totals.total==Decimal('2900')
    assert pos[0].totals.cash==pos[0].totals.card==Decimal('1450')
    assert sum(item.quantity*item.unit_price for item in pos[0].line_items)==Decimal('2900')
    invoice=extract_factura_xml((OUT/'02_compra_demo_2026-10-14.xml').read_bytes())
    assert not invoice.needs_human_review and invoice.extracted_fields.transaction_date==pos[0].date
    assert invoice.extracted_fields.amount==Decimal('928') and invoice.extracted_fields.tax_amount==Decimal('128')


def test_plan_is_read_only_and_apply_is_idempotent():
    db=DB();assert prepare(db)['cash_rows_inserted']==0 and db.writes==[]
    assert prepare(db,True)['cash_rows_inserted']==1 and db.writes==['cash_counts']
    assert prepare(db,True)['already_prepared'] and db.writes==['cash_counts']


@pytest.mark.parametrize('collision',['cash_counts','pos_inputs','transactions','audit_results','documents','owner'])
def test_preparation_refuses_to_replace_or_mix_existing_data(collision):
    db=DB()
    if collision=='owner':db.store['businesses'][0]['owner_id']=None
    else:db.store[collision]=[{'id':str(uuid4()),'business_id':db.bid,'date':'2026-10-14',
        'transaction_date':'2026-10-14','needs_human_review':True}]
    before=deepcopy(db.store)
    with pytest.raises(ValueError):prepare(db,True)
    assert db.store==before and db.writes==[]


def test_cash_count_completes_document_pipeline_and_grounding_without_models():
    db=DB();day='2026-10-14'
    # Falta conteo -> los dos documentos, por si solos, no activan conciliacion.
    pos=extract_pos_data((OUT/'01_ventas_demo_2026-10-14.pdf').read_bytes())[0]
    invoice=extract_factura_xml((OUT/'02_compra_demo_2026-10-14.xml').read_bytes()).extracted_fields
    original=deepcopy(db.store)
    prepare(db,True)
    db.store['pos_inputs']=[{'id':str(uuid4()),'business_id':db.bid,'date':day,
        'cash_sales':str(pos.totals.cash),'card_sales':str(pos.totals.card),
        'total_sales':str(pos.totals.total),'refunds':0}]
    db.store['transactions']=[{'id':str(uuid4()),'business_id':db.bid,'transaction_date':day,
        'type':'egreso','category':'proveedor','amount':str(invoice.amount),'expense_behavior':None}]
    cash=db.store.pop('cash_counts')
    no_count=GatekeeperAgent(db).evaluate(db.bid,day)
    assert no_count.active_metrics==[]
    db.store['cash_counts']=cash
    gate=GatekeeperAgent(db).evaluate(db.bid,day)
    assert gate.active_metrics==['cash_reconciliation']
    calculated=run_calc_engine(gate,db,day,db.bid)
    row=next(r for r in calculated.results if r.metric=='conciliacion_caja')
    assert row.value==Decimal('0.00') and row.status=='ok' and row.unit=='MXN'
    packet=ChatGroundingService(db).build_packet(db.bid,day)
    assert packet.source_s3_result_id==calculated.run_id
    assert any(m['metric']=='conciliacion_caja' and Decimal(str(m['value']))==0 for m in packet.metrics)
    assert packet.final_report is None


def test_missing_claude_uses_openai_with_simulated_response(monkeypatch):
    from agents.core_auditor import _call_llm_with_fallback
    calls=[]
    def unavailable(**kw):raise ValueError('synthetic missing Claude key')
    def create(**kw):
        calls.append(kw)
        content=json.dumps({'executive_summary':'Sintético','operational_narrative':'Sintética','pragmatic_actions':[]})
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    monkeypatch.setenv('ANTHROPIC_API_KEY','');monkeypatch.setenv('OPENAI_API_KEY','synthetic-openai-key')
    monkeypatch.setitem(sys.modules,'langchain_anthropic',SimpleNamespace(ChatAnthropic=unavailable))
    monkeypatch.setitem(sys.modules,'openai',SimpleNamespace(OpenAI=lambda **kw:SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)))))
    report,model=_call_llm_with_fallback('Datos de prueba',0.1)
    assert report['executive_summary']=='Sintético' and 'fallback' in model and len(calls)==1
    assert calls[0]['model']=='gpt-4o'
