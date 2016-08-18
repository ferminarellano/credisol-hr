#-*- coding:utf-8 -*-

from openerp.osv import osv
from openerp.report import report_sxw

class reporte_partida_resumida(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(reporte_partida_resumida, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'get_available_accounts_ids': self.get_available_accounts_ids,
			'get_account_total': self.get_account_total,
			'get_account_description': self.get_account_description,
			'get_account_number': self.get_account_number,
			'get_totales':self.get_totales
		})
	
	def get_totales(self, payslips, tipo):
		debe_total = 0
		haber_total = 0

		for payslip in payslips:
			for line in payslip.line_ids:
				salary_code = line.salary_rule_id.category_id.code
				
				if (tipo == 'haber' and salary_code == 'NET') or (tipo == 'haber' and salary_code == 'DED'):
					haber_total += line.amount
				elif tipo == 'debe' and salary_code != 'DED' and salary_code != 'NET':
					debe_total += line.amount
		
		if tipo == 'debe':
			return debe_total
		elif tipo == 'haber':
			return haber_total
		
	def get_available_accounts_ids(self, payslips):
		salary_rule_ids = []
		salary_rule_ids_sorted = []
		accounts_ids = []

                for payslip in payslips:
                        for line in payslip.line_ids:
                                if not line.salary_rule_id.id in salary_rule_ids:
                                        salary_rule_ids.append(line.salary_rule_id.id)
		
		salary_rules = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, salary_rule_ids)
		sorted_salary_rules = salary_rules.sorted(key=lambda r: r.sequence)

		for salary_rule in sorted_salary_rules:
			deduccion_ids = self.pool.get('deduccion.tipo').search(self.cr, self.uid, [('input_code','=', salary_rule.code)], limit=1)
			deduccion_obj = self.pool.get('deduccion.tipo').browse(self.cr, self.uid, deduccion_ids)
			
			if deduccion_obj and deduccion_obj[0].partida_contable:
				if deduccion_obj[0].partida_contable.id not in accounts_ids:
					accounts_ids.append(deduccion_obj[0].partida_contable.id)
		
		return accounts_ids
		
	def get_account_description(self, account_id):
		account_ids = self.pool.get('deduccion.partida').search(self.cr, self.uid, [('id','=', account_id)], limit=1)
		account_obj = self.pool.get('deduccion.partida').browse(self.cr, self.uid, account_ids)
		
		if account_obj and account_obj[0].descripcion:
			return account_obj[0].descripcion
		else:
			'---'
	
	def get_account_number(self, account_id):
		account_ids = self.pool.get('deduccion.partida').search(self.cr, self.uid, [('id','=', account_id)], limit=1)
		account_obj = self.pool.get('deduccion.partida').browse(self.cr, self.uid, account_ids)
		
		if account_obj and account_obj[0].name:
			return account_obj[0].name
		else:
			'---'
			
	def get_account_total(self, payslips, account_id, tipo):
		deducciones_codes = []
		account_total = 0
		
		deduccion_ids = self.pool.get('deduccion.tipo').search(self.cr, self.uid, [('partida_contable','=', account_id)])
		deduccion_objs = self.pool.get('deduccion.tipo').browse(self.cr, self.uid, deduccion_ids)
		
		for deduccion in deduccion_objs:
			deducciones_codes.append(deduccion.input_code)
		
		for codigo in deducciones_codes:
			reglas_salariales_ids = self.pool.get('hr.salary.rule').search(self.cr, self.uid, [('code','=', codigo)])
			reglas_salariales_objs = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, reglas_salariales_ids)
			
			for regla_salarial in reglas_salariales_objs:

				if(tipo == 'haber' and regla_salarial.category_id.code == 'NET') or (tipo == 'haber' and regla_salarial.category_id.code == 'DED') or (tipo == 'debe' and regla_salarial.category_id.code != 'DED' and regla_salarial.category_id.code != 'NET'):
				
					for payslip in payslips:
						for line in payslip.line_ids:
							if line.salary_rule_id.id == regla_salarial.id:
								account_total += line.amount
		return account_total

class wrapped_reporte_partida_detallada(osv.AbstractModel):
	_name = 'report.hr_bank_solusoft.report_reporte_partida_resumida_template'
	_inherit = 'report.abstract_report'
	_template = 'hr_bank_solusoft.report_reporte_partida_resumida_template'
	_wrapped_report_class = reporte_partida_resumida
