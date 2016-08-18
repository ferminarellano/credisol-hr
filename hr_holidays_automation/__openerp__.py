# -*- coding: utf-8 -*-
{
    'name': "Holidays Automation",
    'summary': """Automatically allocates yearly employees´ legal leaves""",
    'description': """
        This module creates a cron job that checks daily all of the employees contract, 
		depending on the total years the employee has worked for the company it allocates 
		holidays to that employee. It also discounts automatically any advanced legal leaves the employee asked for. 
    """,
    'author': "Fermin Arellano",
    'website': "http://www.codesalpha.com",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': ['base','hr','hr_holidays', 'hr_contract', 'hr_bank_solusoft'],
    'data': ['templates.xml','data/scheduler.xml'],
    'demo': ['demo.xml',],
}