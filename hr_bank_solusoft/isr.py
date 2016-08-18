# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from dateutil import relativedelta
from openerp.tools.translate import _
from openerp import models, fields, api
from openerp.osv import osv
from math import floor
import logging

class impuesto_sobre_renta(models.Model):
	_name = 'impuesto.sobre.renta'
	_logger = logging.getLogger(__name__)

	empleado_id = fields.Many2one(comodel_name="hr.employee", string="Empleado", required=True)
	periodo = fields.Char(string="Año Fiscal", size=4, required=True)
	total_isr = fields.Float(compute='_calcular_isr', string='Total ISR', readonly=True)
	total_deducido = fields.Float(compute='_calcular_total_deducido', string='Deducido a la fecha', readonly=True)
	saldo_pendiente = fields.Float(compute='_calcular_saldo_pendiente', string='Saldo pendiente', readonly=True) 
	total_salarios = fields.Float(compute='_calcular_total_salarios', string='Total salarios', readonly=True) 
	total_incentivos = fields.Float(compute='_calcular_total_incentivos', string='Total incentivos', readonly=True) 
	total_ingresos = fields.Float(compute='_calcular_total_ingresos', string='Total ingresos', readonly=True) 
	total_deducibles = fields.Float(compute='_calcular_total_deducibles', string='Total deducibles', readonly=True) 
	ingresos_gravables = fields.Float(compute='_calcular_ingresos_gravables', string='Ingresos gravables', readonly=True) 
	salarios_mensuales_ids = fields.One2many(comodel_name="isr.salarios", inverse_name="impuesto_sobre_renta_id", string="Salarios")
	
	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		res = []
		for cta in self.browse(cr, uid, ids, context=context):
			res.append((cta.id, cta.empleado_id.name +' - ISR/' + cta.periodo))
		return res
	
	@api.model
	def create(self, vals):
		impuesto = super(impuesto_sobre_renta, self).create(vals)
		self._calcular_salarios(impuesto.id, impuesto.empleado_id.id, impuesto.periodo)
		return impuesto
	
	def _calcular_salarios(self, impuesto_id, empleado_id, periodo):
		contratos = self.env['hr.contract'].search([('employee_id','=',empleado_id)])
		meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
		cursor = 0
		
		for contrato in contratos:
			cursor = 0
			salario = contrato.wage
			
			for mes in meses:
				cursor = cursor+1
				salario_calculado = contrato.get_salario_mensual(str(cursor).zfill(2), periodo)
				
				if salario_calculado > 0:
					self.env['isr.salarios'].create({
						'impuesto_sobre_renta_id':impuesto_id,
						'contrato_id':contrato.id,
						'mes': mes,
						'salario': salario_calculado
					})	
	
	@api.one
	@api.depends('ingresos_gravables')
	def _calcular_isr(self):
		for record in self:
			total_gravable = record.ingresos_gravables
		
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
		
			record.total_isr = self.get_hundredth(resultado)
			
	def get_hundredth(self, monto):
		return floor(monto * 100) / 100.0
	
	@api.one
	@api.depends('empleado_id', 'periodo')
	def _calcular_total_deducido(self):
		for record in self:
			contratos = self.env['hr.contract'].search([('employee_id','=',record.empleado_id.id)])
			total = 0
			
			for contrato in contratos:
				if record.periodo:
					payslips = self.env['hr.payslip'].search([('employee_id','=',record.empleado_id.id), ('state','=','done'), ('paid','=','t'), ('contract_id','=',contrato.id), ('date_from','>=',record.periodo+'-01-01'), ('date_to','<=',record.periodo+'-12-31')])
					#falta la validacion del periodo
					for payslip in payslips:
						for line in payslip.line_ids:
							if line.code == 'ISR':
								total = total + line.total
		
			record.total_deducido = total
	
	@api.one
	@api.depends('total_isr', 'total_deducido')
	def _calcular_saldo_pendiente(self):
		for record in self:
			record.saldo_pendiente = record.total_isr - record.total_deducido
		
	@api.depends('salarios_mensuales_ids')
	def _calcular_total_salarios(self):
		total = 0
		for record in self:
			salarios = self.env['isr.salarios'].search([('impuesto_sobre_renta_id','=',record.id)])
			
			for salario in salarios:
				total = total+salario.salario
		
		record.total_salarios = total
	
	@api.depends('empleado_id')
	def _calcular_total_incentivos(self):
		for record in self:
			contratos = self.env['hr.contract'].search([('employee_id','=',record.empleado_id.id)])
			total = 0
			
			for contrato in contratos:
				if record.periodo:
					payslips = self.env['hr.payslip'].search([('employee_id','=',record.empleado_id.id), ('state','=','done'), ('paid','=','t'), ('contract_id','=',contrato.id), ('date_from','>=',record.periodo+'-01-01'), ('date_to','<=',record.periodo+'-12-31')])
						#falta la validacion del periodo
					for payslip in payslips:
						for line in payslip.line_ids:
							if line.code == 'BONMEN':
								total = total + line.total
		
			record.total_incentivos = total
	
	@api.depends('total_salarios','total_incentivos')
	def _calcular_total_ingresos(self):
		for record in self:
			record.total_ingresos = record.total_salarios + record.total_incentivos
	
	@api.depends('empleado_id')
	def _calcular_total_deducibles(self):
		for record in self:
			deducibles = self.env['isr.deduccion.empleado'].search(['|', ('empleado_id','=',record.empleado_id.id), ('tipo','=','general')])
			deducible_total = 0.0		

			for deducible in deducibles:
				deducible_total += deducible.monto
				
			record.total_deducibles = deducible_total

	@api.depends('empleado_id','total_ingresos', 'total_deducibles')
	def _calcular_ingresos_gravables(self):
		for record in self:
			record.ingresos_gravables = record.total_ingresos - record.total_deducibles
			
	@api.onchange('salarios_mensuales_ids')
	def recalcular(self):
		salarios = self.salarios_mensuales_ids
		total = 0
		for salario in salarios:
			total = total + salario.salario
		self.total_salarios = total
	
	@api.model
	def recalcular_todo(self):
		total = 0
		
		for record in self:
			contratos = self.env['hr.contract'].search([('employee_id','=',record.empleado_id.id)])
			
			for contrato in contratos:
				payslips = self.env['hr.payslip'].search([('employee_id','=',record.empleado_id.id), ('state','=','done'), ('paid','=','t'), ('contract_id','=',contrato.id), ('date_from','>=',record.periodo+'-01-01'), ('date_to','<=',record.periodo+'-12-31')])
					#falta la validacion del periodo
				for payslip in payslips:
					for line in payslip.line_ids:
						if line.code == 'BONMEN':
							total = total + line.total
		
			record.write({'total_incentivos': total})
		
		
class isr_salarios(models.Model):
	_name = 'isr.salarios'

	impuesto_sobre_renta_id = fields.Many2one(comodel_name="impuesto.sobre.renta", ondelete="cascade", string="ISR")
	contrato_id = fields.Many2one(comodel_name="hr.contract", string="Contrato", readonly=True)
	mes = fields.Selection(selection=[
		('enero','Enero'),
		('febrero','Febrero'),
		('marzo','Marzo'),
		('abril','Abril'),
		('mayo','Mayo'),
		('junio','Junio'),
		('julio','Julio'),
		('agosto','Agosto'),
		('septiembre','Septiembre'),
		('octubre','Octubre'),
		('noviembre','Noviembre'),
		('diciembre','Diciembre'),
	], string="Mes", select=True, readonly=True, copy=False, default="enero")
	salario = fields.Float(string="Salario Mensual")
	
	@api.multi
	def unlink(self):
		raise ValidationError("No pueden eliminarse los periodos mensuales.")
		return models.Model.unlink(self)
