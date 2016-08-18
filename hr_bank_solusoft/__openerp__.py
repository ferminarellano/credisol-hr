# -*- coding: utf-8 -*-
{
    'name': "Planilla Honduras",

    'summary': """
        Instala nuevas caracteristicas que permite llevar una planilla para una empresa de Honduras""",

    'description': """
        Agregar las capacidades de poder aplicar prestamos bancarios a un empleado. Se le puede programar nuevas deducciones al empleados, sea de equipo, adelantos salariales o otros productos que la empresa le brinde al empleado. 
    """,

    'author': "Solusoft",
    'website': "http://www.solusofthn.com",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': ['base', 'hr', 'hr_payroll', 'hr_holidays'],
    'data': ['templates.xml','vistas/impuesto_renta.xml','vistas/impuesto_vecinal.xml','vistas/deducciones.xml','reportes/reporte_planilla.xml', 'reportes/reporte_partida_detallada.xml', 'reportes/reporte_partida_resumida.xml'],
    'demo': ['demo.xml'],
}
