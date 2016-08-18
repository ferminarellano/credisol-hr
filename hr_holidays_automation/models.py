# -*- coding: utf-8 -*-

from openerp import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from openerp.osv import osv
from openerp.exceptions import ValidationError

class hr_contract(models.Model):
	_name = 'hr.contract'
	_inherit = 'hr.contract'
	
	# If autocompute = True, the contract will be used in compute_legal_leaves ...
	autocompute = fields.Boolean(string="Cálculo Vacaciones", default=False)
	
	@api.model
	def create(self, vals):
		if vals.get('employee_id') and vals.get('autocompute') and vals['autocompute'] == True:
			contracts_count = self.search_count([('autocompute','=',True), ('employee_id','=',vals['employee_id'])])
			if contracts_count > 0:
				raise ValidationError('La opción de "Cálculo de Vacaciones" solo puede estar habilitada en uno de los contratos del empleado.')
		return super(hr_contract, self).create(vals)
	
	@api.multi
	def write(self, vals):
		if vals.get('autocompute') and vals['autocompute'] == True:
			contract_obj = self.env['hr.contract']
			contracts_count = contract_obj.search_count([('autocompute','=',True), ('employee_id','=',self.employee_id.id)])
			if contracts_count > 0:
				raise ValidationError('La opción de "Cálculo de Vacaciones" solo puede estar habilitada en uno de los contratos del empleado.')
		return super(hr_contract, self).write(vals)
	
class hr_holidays(models.Model):
	_name = 'hr.holidays'
	_inherit = 'hr.holidays'
	
	advance = fields.Boolean(string="Adelanto Vacaciones", default=False)
	advance_settled = fields.Boolean(string="Adelanto saldado", default=False)
	autocompute = fields.Boolean(string="Auto calculado", default=False)
	autocompute_date = fields.Date(required=False)
	
	def create(self, cr, uid, vals, context=None):
		if vals.get('employee_id') and vals.get('number_of_days_temp') and vals.get('type') and vals['type'] == 'add' and vals.get('advance') and vals['advance'] == True:
			allowed_advanced_days = self._allowed_advanced_days(cr, uid, vals['employee_id'])
			if vals['number_of_days_temp'] > allowed_advanced_days:
				raise ValidationError('La cantidad de días excede el limite del empleado. Puede solicitar unicamente: %s' % allowed_advanced_days)
		return osv.osv.create(self, cr, uid, vals, context=context)
			
	def write(self, cr, uid, ids, vals, context=None):
		if vals.get('employee_id') and vals.get('number_of_days_temp') and vals.get('type') and vals['type'] == 'add' and vals.get('advance') and vals['advance'] == True:
			allowed_advanced_days = self._allowed_advanced_days(cr, uid, vals['employee_id'])
			if vals['number_of_days_temp'] > allowed_advanced_days:
				raise ValidationError('La cantidad de días excede el limite del empleado. Puede solicitar unicamente: %s' % allowed_advanced_days)
		return osv.osv.write(self, cr, uid, ids, vals, context=context)
	
	def compute_legal_leaves(self, cr, uid, context=None):
		today_dt = date.today()
		first_dt = date(today_dt.year, 1, 1)
		first = first_dt.strftime('%Y-%m-%d')
		
		contracts_obj = self.pool.get('hr.contract')
		contracts_ids = contracts_obj.search(cr, uid, [('autocompute','=',True), ('date_start','<',first)])
		contracts = contracts_obj.browse(cr, uid, contracts_ids, context=context)
		
		for contract in contracts:
			start_date = contract.date_start
			start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
				
			if contract.type_id.name == 'Empleado Permanente' and contract.employee_id.active and self._validate_date(start_date_dt, today_dt) and self._validate_holidays(cr, uid, contract.employee_id, first_dt):
			
				difference_in_years = relativedelta(today_dt, start_date_dt).years
				holidays_obj = self.pool.get('hr.holidays')
				legal_leave_id = 0
				
				legal_leave = {
					'create_date': datetime.now(),
					'write_uid': 1,
					'holiday_status_id': 1,
					'create_uid': 1,
					'employee_id': contract.employee_id.id,
					'manager_id': 157,
					'manager_id2':contract.employee_id.parent_id.id,
					'user_id': contract.employee_id.user_id.id,
					'message_last_post': datetime.now(),
					'holiday_type': 'employee',
					'state': 'validate',
					'type': 'add',
					'department_id': contract.employee_id.department_id.id,
					'write_date': datetime.now(),
					'name': 'Vacaciones '+str(today_dt.year),
					'autocompute': True,
					'autocompute_date': today_dt,
				}
				
				total_advanced_days = self._advanced_days(cr, uid, contract.employee_id)
								
				if difference_in_years == 1:
					legal_leave['number_of_days_temp'] = 10 - total_advanced_days
					legal_leave['number_of_days'] = 10 - total_advanced_days
				elif difference_in_years == 2:
					legal_leave['number_of_days_temp'] = 12 - total_advanced_days
					legal_leave['number_of_days'] = 12 - total_advanced_days
				elif difference_in_years == 3:
					legal_leave['number_of_days_temp'] = 15 - total_advanced_days
					legal_leave['number_of_days'] = 15 - total_advanced_days
				elif difference_in_years >= 4:
					legal_leave['number_of_days_temp'] = 20 - total_advanced_days
					legal_leave['number_of_days'] = 20 - total_advanced_days
					
				if difference_in_years > 0:
					legal_leave_id = holidays_obj.create(cr, uid, legal_leave, context=context)
					
				if legal_leave_id > 0:
					vacaciones = holidays_obj.browse(cr, uid, legal_leave_id, context=context)
					vacaciones.write({'state':'validate'})
					self._settle_advances(cr, uid, contract.employee_id)
					
	def holidays_first_validate(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		manager = ids2 and ids2[0] or False
		holiday_obj = self.browse(cr, uid, ids[0], context=context)
  
		if self and holiday_obj.employee_id.id is not manager:
			self.holidays_first_validate_notificate(cr, uid, ids, context=context)
			return self.write(cr, uid, ids, {'state':'validate1', 'manager_id': manager})
		raise ValidationError('Usted NO puede hacer la primera aprobacion')
		return False
  
	def _validate_date(self, start_date_dt, today_date):
		virtual_date = date(today_date.year, start_date_dt.month, start_date_dt.day)
		return True if virtual_date <= today_date else False
		
	def _validate_holidays(self, cr, uid, employee, first):
		holidays_obj = self.pool.get('hr.holidays')
		holidays_count = holidays_obj.search_count(cr, uid, [('employee_id','=',employee.id),('autocompute','=',True),('autocompute_date','>=',first)])
		return False if holidays_count > 0 else True
	
	def _advanced_days(self, cr, uid, employee, context=None):
		holidays_obj = self.pool.get('hr.holidays')
		holidays_ids = holidays_obj.search(cr, uid, [('employee_id','=',employee.id),('type','=','add'),('advance','=',True),('advance_settled','=',False)])
		advanced_holidays = holidays_obj.browse(cr, uid, holidays_ids, context=context)
		total = 0.0
		
		for advance in advanced_holidays:
			total += advance.number_of_days
		
		return total
		
	def _settle_advances(self, cr, uid, employee, context=None):
		holidays_obj = self.pool.get('hr.holidays')
		holidays_ids = holidays_obj.search(cr, uid, [('employee_id','=',employee.id),('type','=','add'),('advance','=',True),('advance_settled','=',False)])
		advanced_holidays = holidays_obj.browse(cr, uid, holidays_ids, context=context)

		for advance in advanced_holidays:
			advance.write({'advance_settled':True})
		
	def _allowed_advanced_days(self, cr, uid, employee, context=None):
		contracts_obj = self.pool.get('hr.contract')
		contracts_ids = contracts_obj.search(cr, uid, [('autocompute','=',True), ('employee_id','=',employee)])
		contracts = contracts_obj.browse(cr, uid, contracts_ids, context=context)
		today_dt = date.today()
		difference_in_years = 0
		
		if len(contracts) == 0:
			raise ValidationError('Necesita activar la opción de "Cálculo de Vacaciones" en el contrato del empleado.')
		else:
			for contract in contracts:
				start_date = contract.date_start
				start_date_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
				virtual_date = date(today_dt.year, start_date_dt.month, start_date_dt.day)
				
				if today_dt > virtual_date:
					difference_in_years = relativedelta(date(today_dt.year+1, start_date_dt.month, start_date_dt.day), start_date_dt).years
				else:
					difference_in_years = relativedelta(virtual_date, start_date_dt).years
				
				total_advanced_days = self._advanced_days(cr, uid, contract.employee_id)
				
				if difference_in_years == 1:
					return (10 - total_advanced_days)
				elif difference_in_years == 2:
					return (12 - total_advanced_days)
				elif difference_in_years == 3:
					return (15 - total_advanced_days)
				elif difference_in_years >= 4:
					return (20 - total_advanced_days)
		return 0

					

					
					
					
					
					
	
	
		