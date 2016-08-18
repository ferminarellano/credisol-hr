# -*- coding: utf-8 -*-
from openerp import http

# class Addons/hrContractSolusoft/(http.Controller):
#     @http.route('/addons/hr_contract_solusoft//addons/hr_contract_solusoft//', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/addons/hr_contract_solusoft//addons/hr_contract_solusoft//objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('addons/hr_contract_solusoft/.listing', {
#             'root': '/addons/hr_contract_solusoft//addons/hr_contract_solusoft/',
#             'objects': http.request.env['addons/hr_contract_solusoft/.addons/hr_contract_solusoft/'].search([]),
#         })

#     @http.route('/addons/hr_contract_solusoft//addons/hr_contract_solusoft//objects/<model("addons/hr_contract_solusoft/.addons/hr_contract_solusoft/"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('addons/hr_contract_solusoft/.object', {
#             'object': obj
#         })