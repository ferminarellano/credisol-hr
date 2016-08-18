# -*- coding: utf-8 -*-
{
    'name': "Contrato de Empleados Permanentes",
    'summary': """
        Genera un contrato en formato PDF a empleados permanentes""",

    'description': """
        Genera un contrato en formato PDF a empleados permanentes de la empresa.
    """,

    'author': "Solusoft",
    'website': "http://www.solusofthn.com",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': ['base','hr','hr_contract'],
    'data': ['templates.xml','contrato_permanente.xml'],
    'demo': ['demo.xml']
}
