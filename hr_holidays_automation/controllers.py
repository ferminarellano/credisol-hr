# -*- coding: utf-8 -*-
from openerp import http

# class HrHolidaysAutomation(http.Controller):
#     @http.route('/hr_holidays_automation/hr_holidays_automation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_holidays_automation/hr_holidays_automation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_holidays_automation.listing', {
#             'root': '/hr_holidays_automation/hr_holidays_automation',
#             'objects': http.request.env['hr_holidays_automation.hr_holidays_automation'].search([]),
#         })

#     @http.route('/hr_holidays_automation/hr_holidays_automation/objects/<model("hr_holidays_automation.hr_holidays_automation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_holidays_automation.object', {
#             'object': obj
#         })