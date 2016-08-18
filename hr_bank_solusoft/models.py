# -*- coding: utf-8 -*-

import time
from math import floor
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp.tools.translate import _
from openerp import models, fields, api
from datetime import datetime, timedelta
from openerp.osv import osv
import calendar
import logging

class hr_holidays(models.Model): 
	_name = 'hr.holidays'
	_inherit = 'hr.holidays'

	def write(self, cr, uid, ids, vals, context=None):
		return osv.osv.write(self, cr, uid, ids, vals, context=context)
			
	def create(self, cr, uid, vals, context=None):
		return osv.osv.create(self, cr, uid, vals, context=context)

class hr_contract(models.Model):
	_name = 'hr.contract'
	_inherit = 'hr.contract'
	
	def get_total_salaries(self, cr, uid, employee_id, date_from, date_to, context=None):
		total_salarios = 0
		payslip_obj = self.pool.get('hr.payslip')
		payslip_ids = payslip_obj.search(cr, uid, [('employee_id','=',employee_id),('state','=','done'),('date_from','>',date_from),('date_to','<=',date_to),('credit_note','=',False)])
		
		payslip_line_obj = self.pool.get('hr.payslip.line')
		
		for payslip_id in payslip_ids:
			payslip_line_ids = payslip_line_obj.search(cr, uid, [('slip_id','=',payslip_id), ('code','=','BASIC')])
			payslip_lines = payslip_line_obj.browse(cr, uid, payslip_line_ids, context=context)
			
			for payslip_line in payslip_lines:
				total_salarios = total_salarios + payslip_line.total
			
		return total_salarios
	
	def update_legal_leaves(self, cr, uid, hr_officer_id, context=None):
		contracts_obj = self.pool.get('hr.contract')
		today = datetime.now().strftime('%Y-%m-%d')

		contracts_ids = contracts_obj.search(cr, uid, [('x_holiday','=',True)])
		contracts = contracts_obj.browse(cr, uid, contracts_ids, context=context)
		
		for contract in contracts:
		
			if contract.type_id.name == 'Empleado Permanente':
				start_date = contract.date_start
				start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
				
				contract_day = start_date_dt.day
				contract_month = start_date_dt.month
				
				today_date_dt = datetime.strptime(today, '%Y-%m-%d')
				
				today_day = today_date_dt.day
				today_month = today_date_dt.month
				
				if contract_day==today_day and contract_month==today_month:
					difference_in_years = relativedelta.relativedelta(today_date_dt, start_date_dt).years
					holidays_obj = self.pool.get('hr.holidays')
					legal_leave_id = 0
					
					legal_leave = {
						'create_date': datetime.now(),
						'write_uid': 1,
						'holiday_status_id': 1,
						'create_uid': 1,
						'employee_id': contract.employee_id.id,
						'manager_id': hr_officer_id,
						'manager_id2':contract.employee_id.parent_id.id,
						'user_id': contract.employee_id.user_id.id,
						'message_last_post': datetime.now(),
						'holiday_type': 'employee',
						'state': 'validate',
						'type': 'add',
						'department_id': contract.employee_id.department_id.id,
						'write_date': datetime.now(),
						'name': 'Vacaciones '+str(today_date_dt.year),
					}
									
					if difference_in_years == 1:
						legal_leave['number_of_days_temp'] = 10
						legal_leave['number_of_days'] = 10
					elif difference_in_years == 2:
						legal_leave['number_of_days_temp'] = 12
						legal_leave['number_of_days'] = 12
					elif difference_in_years == 3:
						legal_leave['number_of_days_temp'] = 15
						legal_leave['number_of_days'] = 15
					elif difference_in_years >= 4:
						legal_leave['number_of_days_temp'] = 20
						legal_leave['number_of_days'] = 20
						
					if difference_in_years > 0:
						legal_leave_id = holidays_obj.create(cr, uid, legal_leave, context=context)
						
					if legal_leave_id > 0:
						vacaciones = holidays_obj.browse(cr, uid, legal_leave_id, context=context)
						vacaciones.write({'state':'validate'})
	
	def get_hundredth(self, monto):
		return floor(monto * 100) / 100.0
		
	def calcular_isr(self, monto):
		total_gravable = monto
	
		resultado = 0

		if total_gravable > 116402:
			primera_escala = total_gravable - 116402
			
			if primera_escala>83598:
				segunda_escala = primera_escala - 83598
				resultado = 83598 * 0.15

				if segunda_escala > 300000:
					tercera_escala = segunda_escala - 300000
					resultado = resultado + 300000*0.2 + tercera_escala*0.25
				else:
					resultado = resultado + segunda_escala*0.2
			else:
				resultado = primera_escala*0.15
		return self.get_hundredth(resultado)
	
	def get_salario_mensual(self, mes, periodo):
		for record in self:
		
			fecha_inicial_contrato = record.date_start
			fecha_final_contrato = record.date_end or periodo+'-12-31'
			
			last_day = calendar.monthrange(int(periodo),int(mes))[1] #31
			trim_left=False
			trim_right=False
			
			if not fecha_inicial_contrato < periodo+'-'+mes+'-'+'01':
				dt = datetime.strptime(fecha_inicial_contrato, '%Y-%m-%d')
				inicio_mes = dt.month
				if inicio_mes == int(mes):
					trim_left=True
				else:
					return 0
				
			if not fecha_final_contrato >= periodo+'-'+mes+'-'+str(last_day):
				dt = datetime.strptime(fecha_final_contrato, '%Y-%m-%d')
				final_mes = dt.month
				if final_mes == int(mes):
					trim_right=True
				else:
					return 0
				
			return record.get_proportional_salary2(trim_left, trim_right)
	
	def get_proportional_salary2(self, trim_left, trim_right):
		for record in self:
		
			dia_inicial = trim_left and datetime.strptime(record.date_start, '%Y-%m-%d').day or 1
			dia_final = trim_right and datetime.strptime(record.date_end or "", '%Y-%m-%d').day or 30
			
			dias_trabajados = (dia_final - dia_inicial) + 1
			salario_diario = record.wage/30
			
			if dias_trabajados == 30:
				return record.wage
			return self.get_hundredth(salario_diario*dias_trabajados)
				
	def get_proportional_salary(self):
		salario_proporcional = 0
		for record in self:
			fecha_inicio = record.date_start
			dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
			dia = dt.day
			dias_trabajados = (30 - dia) + 1

			salario_diario = record.wage/30
			salario_proporcional = salario_diario*dias_trabajados
		return salario_proporcional
	
	def get_isr_saldo_pendiente(self, empleado, payslip):
		for record in self:
			fecha_inicio = payslip.date_from
			dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
			periodo = dt.year
			isr = self.env['impuesto.sobre.renta'].search([('empleado_id','=',empleado.id),('periodo','=',periodo)])
			return isr.saldo_pendiente
			
	def get_isr_ingresos_gravables(self, empleado, payslip):
		for record in self:
			fecha_inicio = payslip.date_from
			dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
			periodo = dt.year
			isr = self.env['impuesto.sobre.renta'].search([('empleado_id','=',empleado.id),('periodo','=',periodo)])
			return isr.ingresos_gravables
			
	def get_isr_total_deducido(self, empleado, payslip):
		for record in self:
			fecha_inicio = payslip.date_from
			dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
			periodo = dt.year
			isr = self.env['impuesto.sobre.renta'].search([('empleado_id','=',empleado.id),('periodo','=',periodo)])
			return isr.total_deducido
	
	def get_cantidad_pagos(self, payslip):
		for record in self:
			fecha_inicio = payslip.date_from
			fecha_final_contrato = ''
			
			if record.date_end:
				#contratos = self.search([('employee_id','=',record.employee_id)])
				fecha_final_contrato = record.date_end
			else:
				dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
				periodo = dt.year
				fecha_final_contrato = str(periodo)+'-12-31'
			
			fecha_pago = fecha_inicio
			pagos = 0
			
			while fecha_pago <= fecha_final_contrato:
				pagos = pagos + 1
				fecha_pago = self._get_next_payday(fecha_pago)
			
			return pagos-1
	
	def _get_next_payday(self, fecha):
		dt = datetime.strptime(fecha, '%Y-%m-%d')
		dia = dt.day
		anio_final = dt.year
		
		if dia<14:
			if dt.isoweekday() == 6 and dia == 13:
				dia_final = calendar.monthrange(dt.year,dt.month)[1] - 1
				mes_final = dt.month
			else:
				dia_final = 14
				mes_final = dt.month
		elif dia == 14:
			dia_final = calendar.monthrange(dt.year,dt.month)[1] - 1 
			mes_final = dt.month
		else:
			if 15 <= dia <=  26:
				dia_final = calendar.monthrange(dt.year,dt.month)[1] - 1
				mes_final = dt.month
			else:
				dia_final = 14
				mes_final = dt.month + 1
			
				if dt.month == 12:
					anio_final = dt.year + 1
					mes_final = 1

		fecha_final =  str(anio_final)+'-'+str(mes_final)+'-'+str(dia_final)
		fecha_dt = datetime.strptime(fecha_final,'%Y-%m-%d')
		dia_int = fecha_dt.isoweekday()

		if dia_int == 7:
			fecha_dt = fecha_dt - timedelta(days=1)
		
		return fecha_dt.strftime('%Y-%m-%d')
		
class hr_agencias(models.Model):
	_name = 'hr.agencias'

	def _set_is_active(self):
		return True

	name = fields.Char(string='Nombre', required=True)
	is_active = fields.Boolean(string='Activo', default=_set_is_active)

class banks(models.Model):
	_name = 'hr.banks'

	def _set_is_active(self):
		return True

	name = fields.Char(string='Nombre', required=True)
	phone = fields.Char(string='Teléfono')
	email = fields.Char(string='Email')
	input_code = fields.Char(string='Código', help='Ingrese el codigo a utilizar en las entradas en calculo de planilla, estas mismas se pueden utilizar en el calculo de las reglas salariales.')
	is_active = fields.Boolean(string='Activo', default=_set_is_active)

class bank_loan(models.Model):
	_name = 'bank.loan'

	empleado_id = fields.Many2one(comodel_name="hr.employee", string="Empleado", required=True)
	banco_id = fields.Many2one(comodel_name="hr.banks", string="Banco", required=True)
	referencia = fields.Char(string="Referencia", help="En este campo se puede ingresar cualquier identificador como ser el Numero de Prestamo", required=True)
	monto_total = fields.Float(string="Valor del Prestamo", required=True)
	cuota_monto = fields.Float(string="Valor de Cuota", required=True)
	cuota_qty = fields.Integer(string="Cantidad de Cuotas Quincenales", required=True)
	start_date = fields.Date(string="Fecha de Inicio", required=True)
	name = fields.Char(compute='_get_name', readonly=True)
	cuotas_ids = fields.One2many(comodel_name="bank.loan.quote", inverse_name="prestamo_id", string="Cuotas")
	saldo = fields.Float(compute='_calcular_saldo', readonly=True)
	monto_cancelado = fields.Float(compute='_calcular_saldo', readonly=True)

	@api.model
	def create(self, vals):
		new_record = super(bank_loan, self).create(vals)
		self._create_bank_quotes(new_record.id,new_record.start_date,new_record.cuota_qty,new_record.cuota_monto)
		return new_record

	@api.depends('empleado_id', 'banco_id')
	def _get_name(self):
		for record in self:
			nombre = record.banco_id.name.encode('utf-8')
			if record.referencia:
				nombre +=  " #" + str(record.referencia)  
			nombre +=  " - " + str(record.empleado_id.name)
			record.name = nombre
	
	@api.depends('monto_total','cuotas_ids')
	def _calcular_saldo(self):
		for record in self:
			cuotas_canceladas = self.env['bank.loan.quote'].search([('estado','!=','pendiente'), ('prestamo_id','=',record.id)])
			total_canceladas = 0.0

			for cuota in cuotas_canceladas:
				total_canceladas += cuota.monto_cancelado

			record.saldo = record.monto_total - total_canceladas
			record.monto_cancelado = total_canceladas			 
	
	def _get_bank_loan_id(self):
		for record in self:
			return record.id
	
	def _create_bank_quotes(self, prestamo_id, fecha_inicio, cuotas_qty, cuota_monto):
		next_payday = fecha_inicio
		for x in range(0, cuotas_qty):
			next_payday = self._get_next_payday(next_payday)
			self.env['bank.loan.quote'].create({
				'prestamo_id':prestamo_id,
				'fecha_pago':next_payday,
				'cuota_monto':cuota_monto,
				'cuota_estado':0
			})

	def _get_next_payday(self, fecha):
		dt = datetime.strptime(fecha, '%Y-%m-%d')
		dia = dt.day
		anio_final = dt.year
		
		if dia<14:
			if dt.isoweekday() == 6 and dia == 13:
				dia_final = calendar.monthrange(dt.year,dt.month)[1] - 1
				mes_final = dt.month
			else:
				dia_final = 14
				mes_final = dt.month
		elif dia == 14:
			dia_final = calendar.monthrange(dt.year,dt.month)[1] - 1 
			mes_final = dt.month
		else:
			if 15 <= dia <=  26:
				dia_final = calendar.monthrange(dt.year,dt.month)[1] - 1
				mes_final = dt.month
			else:
				dia_final = 14
				mes_final = dt.month + 1
			
				if dt.month == 12:
					anio_final = dt.year + 1
					mes_final = 1

		fecha_final =  str(anio_final)+'-'+str(mes_final)+'-'+str(dia_final)
		fecha_dt = datetime.strptime(fecha_final,'%Y-%m-%d')
		dia_int = fecha_dt.isoweekday()

		if dia_int == 7:
			fecha_dt = fecha_dt - timedelta(days=1)
		
		return fecha_dt.strftime('%Y-%m-%d')
							
class bank_loan_quote(models.Model):
	_name = 'bank.loan.quote'

	prestamo_id = fields.Many2one(comodel_name="bank.loan", string="Prestamo", ondelete='cascade')
	fecha_pago = fields.Date(string="Fecha de Pago")
	cuota_monto = fields.Float(string="Valor de Cuota")
	monto_cancelado = fields.Float(string="Monto Cancelado", readonly=True)
	estado = fields.Selection(selection=[
		('pendiente','Pendiente'),
		('parcial','Abono Parcial'),
		('pagado','Pagado'),	
	], string="Estado", select=True, readonly=True, copy=False, default="pendiente")
	cuota_estado = fields.Boolean(string="Pagada")

class hr_payslip_run(models.Model):
	_name = 'hr.payslip.run'
	_inherit = 'hr.payslip.run'

	agencia = fields.Many2one(string='Agencia',comodel_name='hr.agencias')
		
class hr_payslip(models.Model):
	_name = 'hr.payslip'
	_inherit = 'hr.payslip'

	def set_datefrom():
		today = int(time.strftime('%d'))

		if today < 15:
                        return lambda *a: time.strftime('%Y-%m-01')
                else:
                        return lambda *a: time.strftime('%Y-%m-16')

	def set_dateto():
		today = int(time.strftime('%d'))

		if today < 15:
			return lambda *a: time.strftime('%Y-%m-15')
		else:
			return lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10]

	_defaults = {
		'date_from': set_datefrom(),
		'date_to': set_dateto(),
		'state': 'draft',
		'credit_note': False,
		'company_id': lambda self, cr, uid, context: \
				self.pool.get('res.users').browse(cr, uid, uid,
				context=context).company_id.id,
	}

	def process_sheet(self, cr, uid, ids, context=None):
		payslip = self.browse(cr, uid, ids, context=context)
		employee_id = payslip[0].employee_id.id	
		date_to = payslip[0].date_to
		
		#necesitamos guardar en una lista los input_code de todos los prestamos que apliquen a un empleado.
		bank_loan_obj = self.pool.get('bank.loan')
		bank_loan_ids = bank_loan_obj.search(cr, uid, [('empleado_id','=',employee_id)])
		
		bank_loan_input_codes = []
		for bank_loan in bank_loan_obj.browse(cr, uid, bank_loan_ids, context=context):
			bank_loan_input_codes.append(str(bank_loan.banco_id.input_code))

		#necesitamos guardar en una lista los input_code de todas las deducciones que apliquen a un empleado.
		deducciones_obj = self.pool.get('empleado.deduccion')
		deducciones_ids = deducciones_obj.search(cr, uid, [('empleado_id','=',employee_id)])

		deducciones_input_codes = []
		
		for deduccion in deducciones_obj.browse(cr, uid, deducciones_ids, context=context):
			deducciones_input_codes.append(deduccion.deduccion_id.input_code)
	
		#en la tabla hr_payslip_input buscar por payslip_id todos los inputs
		hr_payslip_input_obj = self.pool.get('hr.payslip.input')
		hr_payslip_input_ids = hr_payslip_input_obj.search(cr, uid, [('payslip_id','=',ids[0])])
		
		hr_payslip_input_codes = []
		
		for payslip_input in hr_payslip_input_obj.browse(cr, uid, hr_payslip_input_ids, context=context):
			hr_payslip_input_codes.append({'code':str(payslip_input.code), 'amount':payslip_input.amount})
				
		#buscar los inputs en las listas de de input_code. Si se encuentra buscar cuotas por fecha del payslip. Y aplicar pagos.
		for payslip_input_code in hr_payslip_input_codes:
			code = payslip_input_code['code']

			if code in bank_loan_input_codes:
				#get bank loans where employee id and bank code is input code.
				employee_bank_loans_ids = bank_loan_obj.search(cr, uid, [('empleado_id','=',employee_id),('banco_id.input_code','=',code)])
                
				for loan in bank_loan_obj.browse(cr, uid, employee_bank_loans_ids, context=context):
					#get bank quotes.
					bank_loan_quotes_obj = self.pool.get('bank.loan.quote')
					bank_loan_quotes_ids = bank_loan_quotes_obj.search(cr, uid, [('prestamo_id','=',loan.id),('estado','!=','pagado')])
                
					for bank_loan_quote in bank_loan_quotes_obj.browse(cr, uid, bank_loan_quotes_ids, context=context):
						#is bank loan quote before payslip.date_to
						if bank_loan_quote.fecha_pago <= date_to:
							#pagar_cuota con el amount del input de payslip.
							if bank_loan_quote.cuota_monto <= payslip_input_code['amount']:
								bank_loan_quote.write({'estado':'pagado', 'monto_cancelado':bank_loan_quote.cuota_monto, 'cuota_estado':True})
								payslip_input_code['amount'] = payslip_input_code['amount']-bank_loan_quote.cuota_monto
							else:
								bank_loan_quote.write({'estado':'parcial', 'monto_cancelado':payslip_input_code['amount'], 'cuota_estado':False})
								payslip_input_code['amount'] = 0
			
			if code in deducciones_input_codes:
				#conseguir las deducciones del empleado.
				deducciones_empleado_ids = deducciones_obj.search(cr, uid, [('empleado_id','=',employee_id),('pagado','=',False)])

				for deduction in deducciones_obj.browse(cr, uid, deducciones_empleado_ids, context=context):
					if deduction.deduccion_id.input_code == code:
						#get deduccion cuotas
						deduccion_cuotas_obj = self.pool.get('empleado.deduccion.cuota')
						deduccion_cuotas_ids = deduccion_cuotas_obj.search(cr, uid, [('empleado_deduccion_id','=',deduction.id),('estado','!=','pagado')])

						for deduccion_cuota in deduccion_cuotas_obj.browse(cr, uid, deduccion_cuotas_ids, context=context):
							if deduccion_cuota.fecha_pago <= date_to:
								if deduccion_cuota.cuota_monto <= payslip_input_code['amount']:
									deduccion_cuota.write({'estado':'pagado', 'monto_cancelado':deduccion_cuota.cuota_monto, 'cuota_estado':True})
									payslip_input_code['amount'] = payslip_input_code['amount']-deduccion_cuota.cuota_monto
								else:
									deduccion_cuota.write({'estad':'parcial', 'monto_cancelado':payslip_input_code['amount'], 'cuota_estado':False})
									payslip_input_code['amount'] = 0	

		return self.write(cr, uid, ids, {'paid':True, 'state':'done'}, context=context)
	
	def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
		res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id, contract_id, context)
		
		employee_obj = self.pool.get('hr.employee')
		contract_obj = self.pool.get('hr.contract')		

		if context is None:
            		context = {}
		
		if not employee_id:
			return res
		
		employee_id = employee_obj.browse(cr, uid, employee_id, context=context)		

		if not context.get('contract', False):
            		contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
        	else:
            		if contract_id:
                		contract_ids = [contract_id]
           		else:
                		contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)

        	if not contract_ids:
            		return res
        
		contract_record = contract_obj.browse(cr, uid, contract_ids[0], context=context)
        	res['value'].update({
                	'contract_id': contract_record and contract_record.id or False
        	})

        	struct_record = contract_record and contract_record.struct_id or False
        	if not struct_record:
            		return res
        	res['value'].update({
                    'struct_id': struct_record.id,
        	})

		input_line_ids = self.get_inputs(cr, uid, contract_ids, date_from, date_to, context=context, employee_id=employee_id)

		res['value'].update({
			'input_line_ids':input_line_ids,
		})
		
		return res
		
	def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
		def _sum_salary_rule_category(localdict, category, amount):
			if category.parent_id:
				localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
			localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
			return localdict

		class BrowsableObject(object):
			def __init__(self, pool, cr, uid, employee_id, dict):
				self.pool = pool
				self.cr = cr
				self.uid = uid
				self.employee_id = employee_id
				self.dict = dict

			def __getattr__(self, attr):
				return attr in self.dict and self.dict.__getitem__(attr) or 0.0

		class InputLine(BrowsableObject):
			"""a class that will be used into the python code, mainly for usability purposes"""
			def sum(self, code, from_date, to_date=None):
				if to_date is None:
					to_date = datetime.now().strftime('%Y-%m-%d')
				result = 0.0
				self.cr.execute("SELECT sum(amount) as sum\
							FROM hr_payslip as hp, hr_payslip_input as pi \
							WHERE hp.employee_id = %s AND hp.state = 'done' \
							AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
							(self.employee_id, from_date, to_date, code))
				res = self.cr.fetchone()[0]
				return res or 0.0

		class WorkedDays(BrowsableObject):
			"""a class that will be used into the python code, mainly for usability purposes"""
			def _sum(self, code, from_date, to_date=None):
				if to_date is None:
					to_date = datetime.now().strftime('%Y-%m-%d')
				result = 0.0
				self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
							FROM hr_payslip as hp, hr_payslip_worked_days as pi \
							WHERE hp.employee_id = %s AND hp.state = 'done'\
							AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
							(self.employee_id, from_date, to_date, code))
				return self.cr.fetchone()

			def sum(self, code, from_date, to_date=None):
				res = self._sum(code, from_date, to_date)
				return res and res[0] or 0.0

			def sum_hours(self, code, from_date, to_date=None):
				res = self._sum(code, from_date, to_date)
				return res and res[1] or 0.0

		class Payslips(BrowsableObject):
			"""a class that will be used into the python code, mainly for usability purposes"""

			def sum(self, code, from_date, to_date=None):
				if to_date is None:
					to_date = datetime.now().strftime('%Y-%m-%d')
				self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
							FROM hr_payslip as hp, hr_payslip_line as pl \
							WHERE hp.employee_id = %s AND hp.state = 'done' \
							AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
							(self.employee_id, from_date, to_date, code))
				res = self.cr.fetchone()
				return res and res[0] or 0.0

		#we keep a dict with the result because a value can be overwritten by another rule with the same code
		result_dict = {}
		rules = {}
		categories_dict = {}
		blacklist = []
		payslip_obj = self.pool.get('hr.payslip')
		inputs_obj = self.pool.get('hr.payslip.worked_days')
		obj_rule = self.pool.get('hr.salary.rule')
		payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
		worked_days = {}
		for worked_days_line in payslip.worked_days_line_ids:
			worked_days[worked_days_line.code] = worked_days_line
		inputs = {}
		for input_line in payslip.input_line_ids:
			inputs[input_line.code] = input_line

		categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
		input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
		worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
		payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
		rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)

		baselocaldict = {'categories': categories_obj, 'rules': rules_obj, 'payslip': payslip_obj, 'worked_days': worked_days_obj, 'inputs': input_obj}
		#get the ids of the structures on the contracts and their parent id as well
		structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
		#get the rules of the structure and thier children
		rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
		#run the rules by sequence
		sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

		for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
			employee = contract.employee_id
			localdict = dict(baselocaldict, employee=employee, contract=contract)
			for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
				key = rule.code + '-' + str(contract.id)
				localdict['result'] = None
				localdict['result_qty'] = 1.0
				localdict['result_rate'] = 100
				#check if the rule can be applied
				if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
					#compute the amount of the rule
					amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
					#check if there is already a rule computed with that code
					previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
					#set/overwrite the amount computed for this rule in the localdict
					tot_rule = amount * qty * rate / 100.0
					localdict[rule.code] = tot_rule
					rules[rule.code] = rule
					#sum the amount for its salary category
					localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
					#create/overwrite the rule in the temporary results
					result_dict[key] = {
						'salary_rule_id': rule.id,
						'contract_id': contract.id,
						'name': rule.name,
						'code': rule.code,
						'category_id': rule.category_id.id,
						'sequence': rule.sequence,
						'appears_on_payslip': rule.appears_on_payslip,
						'condition_select': rule.condition_select,
						'condition_python': rule.condition_python,
						'condition_range': rule.condition_range,
						'condition_range_min': rule.condition_range_min,
						'condition_range_max': rule.condition_range_max,
						'amount_select': rule.amount_select,
						'amount_fix': rule.amount_fix,
						'amount_python_compute': rule.amount_python_compute,
						'amount_percentage': rule.amount_percentage,
						'amount_percentage_base': rule.amount_percentage_base,
						'register_id': rule.register_id.id,
						'amount': amount,
						'employee_id': contract.employee_id.id,
						'quantity': qty,
						'rate': rate,
					}
				else:
					#blacklist this rule and its children
					blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

		result = [value for code, value in result_dict.items()]
		return result

	def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
		"""
		@param contract_ids: list of contract id
		@return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
		"""
		def was_on_leave(employee_id, datetime_day, context=None):
			res = False
			day = datetime_day.strftime("%Y-%m-%d")
			holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',day),('date_to','>=',day)])
			if holiday_ids:
				res = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].holiday_status_id.name
			return res

		res = []
		for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
			if not contract.working_hours:
				#fill only if the contract as a working schedule linked
				continue
			attendances = {
				 'name': _("Normal Working Days paid at 100%"),
				 'sequence': 1,
				 'code': 'WORK100',
				 'number_of_days': 0.0,
				 'number_of_hours': 0.0,
				 'contract_id': contract.id,
			}
			leaves = {}
			day_from = datetime.strptime(date_from,"%Y-%m-%d")
			day_to = datetime.strptime(date_to,"%Y-%m-%d")
			nb_of_days = (day_to - day_from).days + 1
			for day in range(0, nb_of_days):
				working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
				if working_hours_on_day:
					#the employee had to work
					leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day), context=context)
					if leave_type:
						#if he was on leave, fill the leaves dict
						if leave_type in leaves:
							leaves[leave_type]['number_of_days'] += 1.0
							leaves[leave_type]['number_of_hours'] += working_hours_on_day
						else:
							leaves[leave_type] = {
								'name': leave_type,
								'sequence': 5,
								'code': leave_type,
								'number_of_days': 1.0,
								'number_of_hours': working_hours_on_day,
								'contract_id': contract.id,
							}
					else:
						#add the input vals to tmp (increment if existing)
						attendances['number_of_days'] += 1.0
						attendances['number_of_hours'] += working_hours_on_day
			leaves = [value for key,value in leaves.items()]
			res += [attendances] + leaves
			
			#si el contrato es para empleado por hora, hacer el calculo.
			if contract.type_id.name == 'Empleado por Hora':
				asistencia_obj = self.pool.get('hr.attendance')
				asistencia_ids = asistencia_obj.search(cr, uid, [('employee_id','=',contract.employee_id.id),('action','=','sign_out'),('action_desc.name','!=','Salida almuerzo')])
				
				asistencia = {
					 'name': "Total de Horas Trabajadas segun Reloj Marcador",
					 'sequence': 1,
					 'code': 'RELOJ',
					 'number_of_days': 0.0,
					 'number_of_hours': 0.0,
					 'contract_id': contract.id,
				}
				
				for asistencia_db in asistencia_obj.browse(cr, uid, asistencia_ids, context=context):
					if day_from.strftime("%Y-%m-%d") + ' 00:00:00' <= asistencia_db.name <= day_to.strftime("%Y-%m-%d") + ' 23:59:59':
						asistencia['number_of_hours'] += asistencia_db.worked_hours

				asistencia['number_of_days'] = round(asistencia.get('number_of_hours','0')/8)
				
				res += [asistencia]
				
		return res
		
	def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None, employee_id=False):
		res = super(hr_payslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
		
		if not employee_id:
			return res
		
		contract_obj = self.pool.get('hr.contract')

		#Se cargan los prestamos y cuotas de prestamo y se devuelven a cargar en Inputs.

		bank_loan_obj = self.pool.get('bank.loan')
		bank_loan_quote_obj = self.pool.get('bank.loan.quote')

		bank_loan_ids = bank_loan_obj.search(cr, uid, [('empleado_id','=',employee_id.id)])	
		
		for contract in contract_obj.browse(cr, uid, contract_ids, context=context):

			prestamos = {}
			id_contrato = 0

			for bank_loan in bank_loan_obj.browse(cr, uid, bank_loan_ids, context=context):
				bank_loan_quotes_ids = bank_loan_quote_obj.search(cr, uid, [('prestamo_id','=',bank_loan.id), ('estado','!=','pagado')])
			
				for bank_loan_quote in bank_loan_quote_obj.browse(cr, uid, bank_loan_quotes_ids, context=context):
					if bank_loan_quote.fecha_pago <= date_to:	
						
						if not prestamos.get(bank_loan.banco_id.input_code):
							prestamos[bank_loan.banco_id.input_code] = {'name':"Prestamo - "+bank_loan.banco_id.name, 'amount':bank_loan_quote.cuota_monto-bank_loan_quote.monto_cancelado} 
						else:
							prestamos[bank_loan.banco_id.input_code] = {'name':"Prestamo - "+bank_loan.banco_id.name, 'amount':prestamos.get(bank_loan.banco_id.input_code, 0)['amount']+bank_loan_quote.cuota_monto-bank_loan_quote.monto_cancelado} 
						
						id_contrato = contract.id		
									
			for llave, valor in prestamos.iteritems():
				
				prestamos_total = {
					'name':valor['name'],
					'code':llave,
					'amount':valor['amount'],
					'contract_id':id_contrato
				}
				
				res += [prestamos_total]

		#Se cargan las deducciones al ISR que aplican a cada empleado.
		
		isr_deducible_obj = self.pool.get('isr.deduccion.empleado')
		isr_deducible_ids = isr_deducible_obj.search(cr, uid, [('empleado_id','=',employee_id.id)])
		isr_deducible_gral_ids = isr_deducible_obj.search(cr, uid, [('tipo','=','general')])

		for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
			deducible_total = 0.0		

			for deducible in isr_deducible_obj.browse(cr, uid, isr_deducible_ids, context=context):
				deducible_total += deducible.monto

			for deducible_gral in isr_deducible_obj.browse(cr, uid, isr_deducible_gral_ids, context=context):
				deducible_total += deducible_gral.monto

			if deducible_total > 0:
				if contract.type_id.name == 'Empleado Permanente':
					deducibles = {
						'name':'Deducibles del ISR',
						'code':'ISRDED',
						'amount':deducible_total,
						'contract_id':contract.id
					}

					res += [deducibles]

		#Se cargan las cuotas del Impuesto Vecinal y se agregan a los inputs de aplicar. 

		impuesto_vecinal_obj = self.pool.get('impuesto.vecinal.config')
		impuesto_vecinal_cuotas_obj = self.pool.get('impuesto.vecinal.cuotas')

		dt = datetime.strptime(date_from, '%Y-%m-%d')
		anio = dt.year			
	
		impuesto_vecinal_config_ids = impuesto_vecinal_obj.search(cr, uid, [('agencia','=',employee_id.agencias.id),('periodo','=',anio)])

		for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
			
			for impuesto_vecinal in impuesto_vecinal_obj.browse(cr, uid, impuesto_vecinal_config_ids, context=context):		
				impuesto_vecinal_cuotas_ids = impuesto_vecinal_cuotas_obj.search(cr, uid, [('id_impuesto_vecinal_config','=',impuesto_vecinal.id)])
				
				for impuesto_vecinal_cuota in impuesto_vecinal_cuotas_obj.browse(cr, uid, impuesto_vecinal_cuotas_ids, context=context):
					if date_from <= impuesto_vecinal_cuota.fecha_pago <= date_to:
						impto_vecinal = {
							'name':impuesto_vecinal_cuota.name,
							'code':'IMPVEC',
							'amount':impuesto_vecinal.cuotas,
							'contract_id':contract.id
						}

						res += [impto_vecinal]
						
		#Se cargan las cuotas de las deducciones del empleado.	
		empleado_deduccion_obj = self.pool.get('empleado.deduccion')
		empleado_deduccion_cuotas_obj = self.pool.get('empleado.deduccion.cuota')
		
		empleado_deduccion_ids = empleado_deduccion_obj.search(cr, uid, [('empleado_id','=',employee_id.id)])
		
		for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
		
			deducciones = {}
			id_contrato = 0

			for deduccion in empleado_deduccion_obj.browse(cr, uid, empleado_deduccion_ids, context=context):
				empleado_deduccion_cuotas_ids = empleado_deduccion_cuotas_obj.search(cr, uid, [('empleado_deduccion_id','=',deduccion.id),('estado','!=','pagado')])
				
				for empleado_deduccion_cuota in empleado_deduccion_cuotas_obj.browse(cr, uid, empleado_deduccion_cuotas_ids, context=context):
					if empleado_deduccion_cuota.fecha_pago <= date_to:
						
						codigo_deduccion = deduccion.deduccion_id.input_code
						
						if not deducciones.get(codigo_deduccion):
							deducciones[codigo_deduccion] = {
								'name':deduccion.deduccion_id.name, 
								'amount':empleado_deduccion_cuota.cuota_monto - empleado_deduccion_cuota.monto_cancelado
							}
						else:
							deducciones[codigo_deduccion] = {
								'name':deduccion.deduccion_id.name,
								'amount':deducciones.get(codigo_deduccion, 0)['amount'] + empleado_deduccion_cuota.cuota_monto - empleado_deduccion_cuota.monto_cancelado
							}

						id_contrato = contract.id

			for key, value in deducciones.iteritems():
				deducciones_total = {
					'name':value['name'],
					'code':key,
					'amount':value['amount'],
					'contract_id':id_contrato
				}
				
				res += [deducciones_total]
				
		return res
