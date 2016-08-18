# -*- coding: utf-8 -*-
from openerp import http

# class /opt/odoo80/addons/hrBankSolusoft/(http.Controller):
#     @http.route('//opt/odoo80/addons/hr_bank_solusoft///opt/odoo80/addons/hr_bank_solusoft//', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//opt/odoo80/addons/hr_bank_solusoft///opt/odoo80/addons/hr_bank_solusoft//objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('/opt/odoo80/addons/hr_bank_solusoft/.listing', {
#             'root': '//opt/odoo80/addons/hr_bank_solusoft///opt/odoo80/addons/hr_bank_solusoft/',
#             'objects': http.request.env['/opt/odoo80/addons/hr_bank_solusoft/./opt/odoo80/addons/hr_bank_solusoft/'].search([]),
#         })

#     @http.route('//opt/odoo80/addons/hr_bank_solusoft///opt/odoo80/addons/hr_bank_solusoft//objects/<model("/opt/odoo80/addons/hr_bank_solusoft/./opt/odoo80/addons/hr_bank_solusoft/"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/opt/odoo80/addons/hr_bank_solusoft/.object', {
#             'object': obj
#         })