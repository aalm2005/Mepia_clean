const assert=require('node:assert/strict');
const fs=require('node:fs');const ts=require('typescript');
function read(file){const mod={exports:{}};const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;new Function('module','exports','require',code)(mod,mod.exports,require);return mod.exports;}
const {mapCalcResultsToKpis,calcResultsToChartRows}=read('utils/mapCalcResultsToKpis.ts');
const {analysisLabel,metricLabel}=read('utils/analysis-presentation.ts');
const r=(metric,value=0,unit='MXN',status='ok')=>({metric,value,unit,status,context:'Simulado'});
const checks=[];function check(name,fn){fn();checks.push(name);console.log('PASS '+name);}
check('Concentración de ingresos no es ingresos totales',()=>assert.equal(mapCalcResultsToKpis([r('revenue_concentration')])[0].value,'—'));
check('Costo operativo no es margen',()=>assert.equal(mapCalcResultsToKpis([r('operative_cost_margin')])[1].value,'—'));
check('Salud en MXN describe media por producto',()=>assert.equal(metricLabel('health_score'),'Margen medio por producto'));
check('Cero decimal sigue siendo cero',()=>assert.equal(mapCalcResultsToKpis([r('conciliacion_caja','0.00')])[4].value,'0'));
check('No reescala porcentaje',()=>assert.equal(mapCalcResultsToKpis([r('margen_contribucion','0.5','%')])[1].value,'0.5%'));
check('Estados incompletos no grafican',()=>assert.deepEqual(calcResultsToChartRows([r('conciliacion_caja',0,'MXN','incomplete_data')]),[]));
check('Identificación distingue guardado y referencia del mismo día',()=>{const a=analysisLabel({run_id:'aaaaaaaa-0000',date:'2026-10-14',created_at:'2026-10-15T10:00:00Z'});const b=analysisLabel({run_id:'bbbbbbbb-0000',date:'2026-10-14',created_at:'2026-10-15T11:00:00Z'});assert.notEqual(a,b);assert.match(a,/2026-10-14/);assert.match(a,/aaaaaaaa/);});
check('No promete Excel ni arrays al faltar datos',()=>assert(!JSON.stringify(mapCalcResultsToKpis([])).match(/Excel|CSV|arrays|calc_results/)));
check('Los indicadores del ensayo se muestran en español',()=>{
  for (const [metric,expected] of Object.entries({
    waste_cost:'Costo de merma registrada',
    modifier_attach_rate:'Proporción de productos con extras',
    cancellation_rate:'Tasa de cancelaciones',
    reprint_rate:'Tasa de reimpresiones',
    shift_cash_variance:'Diferencia de caja por turno',
    labor_cost_ratio:'Costo laboral sobre ventas',
    sales_per_labor_hour:'Ventas por hora trabajada',
  })) assert.equal(metricLabel(metric),expected);
});
check('Los identificadores históricos conservan el mismo nombre en español',()=>{
  assert.equal(metricLabel('ventas_por_staff'),metricLabel('sales_by_staff'));
  assert.equal(metricLabel('patron_horario_ventas'),metricLabel('hourly_sales_pattern'));
  assert.equal(metricLabel('inventory_variance_merma'),'Merma de inventario');
});
const reportPath=process.argv[2]||'.test_tmp/history_20261019/presentation.json';
fs.mkdirSync(require('node:path').dirname(reportPath),{recursive:true});fs.writeFileSync(reportPath,JSON.stringify({checks,passed:checks.length},null,2));
