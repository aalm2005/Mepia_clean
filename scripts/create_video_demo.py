"""Genera documentos ficticios, sin conectarse a servicios ni cargar .env."""
from pathlib import Path
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/demo_mepia_20261014'
DATE='2026-10-14'


def pdf(name,title,subtitle,blocks):
    styles=getSampleStyleSheet()
    styles['Title'].textColor=colors.HexColor('#143f68')
    styles['Title'].fontSize=21;styles['Title'].leading=25
    doc=SimpleDocTemplate(str(OUT/name),pagesize=A4,rightMargin=45,leftMargin=45,
        topMargin=45,bottomMargin=45,title=title,author='MEPIA - demostracion',invariant=1)
    story=[Paragraph('MEPIA | DEMOSTRACION',styles['Heading2']),
        Paragraph(title,styles['Title']),Paragraph(subtitle,styles['Normal']),Spacer(1,17)]
    for block in blocks:
        if isinstance(block,list):
            table=Table(block,colWidths=[280,95,130] if len(block[0])==3 else [330,175],hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f1fa')),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),
                ('FONTSIZE',(0,0),(-1,-1),10),('LEADING',(0,0),(-1,-1),14),
                ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#c5d3e3')),
                ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
                ('ALIGN',(1,0),(-1,-1),'RIGHT')]))
            story.extend([table,Spacer(1,15)])
        else:story.extend([Paragraph(block,styles['Normal']),Spacer(1,12)])
    story.extend([Spacer(1,12),Paragraph('DATOS FICTICIOS. Documento de demostracion sin validez fiscal.',styles['Normal'])])
    doc.build(story)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pdf('01_ventas_demo_2026-10-14.pdf','REPORTE DIARIO DE VENTAS POS',
        'Negocio: MEPIA Dev | Fecha: 14/10/2026 | Moneda: MXN',[
        '<b>Venta Total: $2,900.00 MXN</b>',
        '<b>Efectivo: $1,450.00 MXN</b><br/><b>Tarjeta: $1,450.00 MXN</b>',
        [['Producto','Cantidad','Precio unitario'],['Paquete A (IVA incluido)','10','$116.00'],
         ['Paquete B (IVA incluido)','10','$174.00']],
        'Precios unitarios con IVA incluido. Los productos suman $2,900.00.',
        '<b>Conteo fisico de caja del mismo dia</b>',
        [['Concepto','Importe'],['Fondo inicial','$200.00'],['Dinero contado al cerrar','$1,650.00'],
         ['Salidas de efectivo','$0.00'],['Devoluciones','$0.00']],
        'El conteo de caja se prepara por separado antes del ensayo; el lector POS extrae ventas y formas de pago.'])
    pdf('03_compra_demo_REFERENCIA_NO_SUBIR.pdf','COMPROBANTE DE COMPRA',
        'MEPIA Dev | Fecha: 14/10/2026 | Solo referencia visual del XML',[
        '<b>Proveedor:</b> Proveedor Ficticio MEPIA<br/><b>Folio:</b> DEMO-COMPRA-20261014',
        'Concepto: Compra de insumos para demostracion.',
        [['Concepto','Importe'],['Subtotal','$800.00'],['IVA','$128.00'],['Total','$928.00']],
        'Cargar solo el archivo 02_compra_demo_2026-10-14.xml. Este PDF muestra la misma compra; cargar ambos registraria dos documentos distintos.'])
    xml='''<?xml version="1.0" encoding="UTF-8"?>
<!-- DATOS FICTICIOS PARA MEPIA. Sin timbre ni validez fiscal. -->
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" Version="4.0"
 Fecha="2026-10-14T12:00:00" Folio="DEMO-COMPRA-20261014"
 SubTotal="800.00" Total="928.00" Moneda="MXN" TipoDeComprobante="I">
 <cfdi:Emisor Nombre="Proveedor Ficticio MEPIA" Rfc="XAXX010101000" RegimenFiscal="601"/>
 <cfdi:Receptor Nombre="MEPIA Dev - demostracion" Rfc="XAXX010101000" UsoCFDI="G03"/>
 <cfdi:Conceptos><cfdi:Concepto Descripcion="Compra de insumos para demostracion"
 Cantidad="1" ValorUnitario="800.00" Importe="800.00"/></cfdi:Conceptos>
 <cfdi:Impuestos TotalImpuestosTrasladados="128.00"><cfdi:Traslados>
 <cfdi:Traslado Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="128.00"/>
 </cfdi:Traslados></cfdi:Impuestos>
</cfdi:Comprobante>
'''
    (OUT/'02_compra_demo_2026-10-14.xml').write_text(xml,encoding='utf-8',newline='\n')
    expected={'synthetic':True,'date':DATE,'business_name':'MEPIA Dev',
        'pos':{'total':'2900.00','cash':'1450.00','card':'1450.00'},
        'invoice':{'amount':'928.00','tax_amount':'128.00','reference':'DEMO-COMPRA-20261014'},
        'cash_count':{'initial_float':200.0,'actual_counted':1650.0,'cash_payouts':0.0},
        'cash_reconciliation':{'value':'0.00','unit':'MXN','status':'ok'},
        'not_proven':['ticket promedio: no hay tickets individuales','utilidad: faltan costos confirmados',
                      'otras metricas: requieren datos adicionales']}
    (OUT/'resultados_esperados.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Preparados: dos PDF, un XML ficticio y resultados esperados. Sin red ni base de datos.')


if __name__=='__main__':main()
