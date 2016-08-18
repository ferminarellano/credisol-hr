# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta, date
from dateutil import relativedelta
import calendar, time

class deduccion_partida_contable(models.Model):
	_name = 'deduccion.partida'
	_rec_name = 'descripcion'
	
	def _set_is_active(self):
                return True
	
	name = fields.Char(string='Cuenta Contable', required=True)
	descripcion = fields.Char(string='Descripcion', required=True) 
	
	def name_get(self, cr, uid, ids, context={}):

		if not len(ids):
				return []

		res=[]

		for cta in self.browse(cr, uid, ids, context=context):
				res.append((cta.id, cta.descripcion + ' - ' + cta.name))

		return res


class deduccion_tipo(models.Model):
	_name = 'deduccion.tipo'

	def _set_is_active(self):
		return True

	name = fields.Char(string='Nombre', required=True)
	input_code = fields.Char(string='Código', help='Ingrese el codigo a utilizar en las entradas en el calculo de planilla en las reglas salariales')
	partida_contable = fields.Many2one(string="Partida Contable", comodel_name="deduccion.partida", required=True)
	is_active = fields.Boolean(string='Activo', default=_set_is_active)

	_sql_constraints = [
		('deduccion_tipo_unique', 'UNIQUE(input_code)','Ya existe una deduccion con este codigo'),
	]

class empleado_deduccion(models.Model):
	_name = 'empleado.deduccion'
	
	name = fields.Char(compute='_get_name', readonly=True)
	empleado_id = fields.Many2one(comodel_name="hr.employee", string="Empleado", required=True)
	control_saldo = fields.Boolean(string="Control de Saldo", help="Seleccione esta opción si la deducción lleva un saldo a favor de la empresa")
	cuota_auto = fields.Boolean(string="Cuotas autogeneradas", help="Seleccione esta opción si desea que el sistema le genere un plan de pago")
	deduccion_id = fields.Many2one(comodel_name="deduccion.tipo", string="Deduccion", required=True)
	referencia = fields.Char(string="Referencia")
	monto_inicial = fields.Float(string="Monto Inicial")
	cuota_qty = fields.Integer(string="Cuotas", help="Ingrese la cantidad de cuotas quincenales en las que se realizara el pago")
	cuota_monto = fields.Float(string="Monto", help="Ingrese el monto que se deducira en cada cuota")
	fecha_inicio = fields.Date(string="Fecha Inicio", help="Ingrese la fecha a partir de la que se empezará a realizar la deducción")
	saldo = fields.Float(compute='_calcular_saldo', readonly=True)
	monto_cancelado = fields.Float(compute='_calcular_saldo', string="Monto Cancelado", readonly=True)
	deduccion_cuotas_ids = fields.One2many(comodel_name="empleado.deduccion.cuota", inverse_name="empleado_deduccion_id", string="Cuotas")
	pagado = fields.Boolean(string="Pagado")

	@api.model
	def create(self, vals):
		deduccion = super(empleado_deduccion, self).create(vals)

		if deduccion.cuota_auto:
			self._crear_cuotas(deduccion.id, deduccion.fecha_inicio, deduccion.cuota_qty, deduccion.cuota_monto)
			deduccion.cuota_auto = False
			deduccion.fecha_inicio = None
			deduccion.cuota_qty = None
			deduccion.cuota_monto = None

		return deduccion
	
	def _crear_cuotas(self, id, fecha_inicio, cuota_cantidad, cuota_monto):
		fecha_pago = fecha_inicio
		for x in range(0, cuota_cantidad):
			fecha_pago = self._get_fecha_pago(fecha_pago)
			self.env['empleado.deduccion.cuota'].create({
				'empleado_deduccion_id':id,
				'cuota_monto':cuota_monto,
				'cuota_estado':False,
				'fecha_pago':fecha_pago,
				'monto_cancelado':0,
				'estado':'pendiente'
			})	

	def _get_fecha_pago(self, fecha):
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

	@api.depends('empleado_id', 'deduccion_id')
	def _get_name(self):
		for record in self:
			nombre = u'%s' % record.deduccion_id.name
			if record.referencia:
				nombre +=  " #" + str(record.referencia)
			empleado_nombre = u'%s' % record.empleado_id.name
			nombre +=  " - " + empleado_nombre
			record.name = nombre
	
	@api.depends('monto_inicial','deduccion_cuotas_ids')
	def _calcular_saldo(self):
		for record in self:
			cuotas_canceladas = self.env['empleado.deduccion.cuota'].search([('cuota_estado','=',1), ('empleado_deduccion_id','=',record.id)])
			total_canceladas = 0.0

			for cuota in cuotas_canceladas:
				total_canceladas += cuota.cuota_monto

			record.saldo = record.monto_inicial - total_canceladas
			record.monto_cancelado = total_canceladas

	@api.onchange('control_saldo')
	def limpiar_saldos(self):
		self.monto_inicial = None
		self.saldo = None
		self.monto_cancelado = None

class empleado_deduccion_cuota(models.Model):
	_name = 'empleado.deduccion.cuota'

	empleado_deduccion_id = fields.Many2one(comodel_name="empleado.deduccion", ondelete="cascade", string="Deducción Empleado")
	fecha_pago = fields.Date(string="Fecha de Pago", required=True)
	cuota_monto = fields.Float(string="Monto", required=True)
	monto_cancelado = fields.Float(string="Monto Cancelado", readonly=True)
	estado = fields.Selection(selection=[
		('pendiente','Pendiente'),
		('parcial','Abono Parcial'),
		('pagado','Pagado'),	
	], string="Estado", select=True, readonly=True, copy=False, default="pendiente")
	cuota_estado = fields.Boolean(string="Estado")

	@api.multi
	def unlink(self):
		for cuota in self:
			if cuota.estado not in ('pendiente'):
				raise ValidationError("No puede borrar cuotas que ya han sido canceladas parcial o completamente.")
		return models.Model.unlink(self)

class isr_deduccion(models.Model):
	_name = 'isr.deduccion'

	def _set_is_active(self):
		return True

	name = fields.Char(string='Nombre', required=True)
	is_active = fields.Boolean(string='Activo', default=_set_is_active)        

class isr_deduccion_empleado(models.Model):
	_name = 'isr.deduccion.empleado'

	name = fields.Char(compute='_get_name', readonly=True)
	tipo = fields.Selection([('single', 'Empleado'),('general','General')], string="Tipo de deduccion", required=True, help="Seleccione 'Empleado' para asignar la deduccion a un solo empleado, y General para todos los empleados")
	empleado_id = fields.Many2one(comodel_name="hr.employee", string="Empleado")
	isr_deduccion_id = fields.Many2one(comodel_name="isr.deduccion", string="Deduccion ISR", required=True)
	monto = fields.Float(string="Valor de la deduccion", required=True, help="Ingrese el monto total anual a deducir del ISR")

	@api.depends('empleado_id', 'isr_deduccion_id')
	def _get_name(self):
		for record in self:
			nombre = str(record.isr_deduccion_id.name)+" - "
			if record.tipo == 'single':
				nombre += str(record.empleado_id.name_related)
			else:
				nombre += "Empleados en General"
			record.name = nombre

	@api.onchange('tipo')
	def set_empleado(self):
		if self.tipo == 'general':
			self.empleado_id = None
	
	@api.one
	@api.constrains('tipo','empleado_id')
	def _check_employee_contract_type(self):
		if self.tipo == 'single':
			contratos = self.env['hr.contract'].search([('employee_id','=',self.empleado_id.id)])
			
			empleado_permanente = False

			for contrato in contratos:
				if contrato.type_id.name == 'Empleado Permanente':
					empleado_permanente = True

			if not empleado_permanente:
				raise ValidationError("El empleado debe tener un contrato de Empleado Permanente")					

class impuesto_vecinal_config(models.Model):
	_name = 'impuesto.vecinal.config'

	#Como llevo el control de si un empleado pago su IV o si todavia le queda saldo? 

	name = fields.Char(compute='_get_name', readonly=True)
	agencia = fields.Many2one(string='Agencia',comodel_name='hr.agencias')
	periodo = fields.Char(string="Año Fiscal", size=4, required=True)
	cuotas = fields.Integer(string="Cuotas Quincenales", help="Especifique la cantidad de cuotas en las que se cancelará el monto total.", required=True)
	fecha_inicio = fields.Date(string="Fecha de inicio", help="Seleccione a partir de que fecha se empezará a aplicar el cobro.", required=True)
	cuotas_ids = fields.One2many(comodel_name="impuesto.vecinal.cuotas", inverse_name="id_impuesto_vecinal_config", string="Cuotas", required=True)

	_sql_constraints = [
                ('impuesto_vecinal_unique', 'UNIQUE(agencia,periodo)', 'Ya existe una configuración de Impuesto Vecinal para esta agencia en el año fiscal'),
        ]	

	@api.model
	def create(self, vals):
		new_record = super(impuesto_vecinal_config, self).create(vals)
		self._create_iv_quotes(new_record.id,new_record.fecha_inicio,new_record.cuotas)
		return new_record

	@api.depends('agencia', 'periodo')
	def _get_name(self):
		for record in self:
			agencia = record.agencia
			nombre = agencia.name
			nombre +=  "/" + str(record.periodo)
			record.name = nombre

	def _create_iv_quotes(self, prestamo_id, fecha_inicio, cuotas_qty):
		next_payday = fecha_inicio
		for x in range(0, cuotas_qty):
			next_payday = self._get_next_payday(next_payday)
			self.env['impuesto.vecinal.cuotas'].create({
				'id_impuesto_vecinal_config':prestamo_id,
				'name':"Cuota "+str(x+1)+"/"+str(cuotas_qty),
				'fecha_pago':next_payday
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
			if 15 <= dia <= 26:
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

class impuesto_vecinal_cuotas(models.Model):
	_name = 'impuesto.vecinal.cuotas'

	id_impuesto_vecinal_config = fields.Many2one(comodel_name="impuesto.vecinal.config", string="Configuración", ondelete='cascade')
	name = fields.Char()
	fecha_pago = fields.Date(string="Fecha de Pago")
