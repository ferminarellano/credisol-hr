#-*- coding:utf-8 -*-

from openerp.osv import osv
from openerp.report import report_sxw

class reporte_partida_detallada(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(reporte_partida_detallada, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'get_available_salary_rules': self.get_available_salary_rules,
			'get_salary_rule_total': self.get_salary_rule_total,
			'get_account_description': self.get_account_description,
			'get_account_number': self.get_account_number,
			'get_salary_rule_name': self.get_salary_rule_name,
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
	
	def get_account_description(self, salary_rule_id):
		salary_rule = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, salary_rule_id)
		salary_rule_code = salary_rule[0].code
		
		deducciones = self.pool.get('deduccion.tipo').search(self.cr, self.uid, [('input_code','=', salary_rule_code)])
		if len(deducciones) > 0:
			return self.pool.get('deduccion.tipo').browse(self.cr, self.uid, deducciones[0])[0].partida_contable.descripcion
		else:
			return '---'
	
	def get_account_number(self, salary_rule_id):
		salary_rule = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, salary_rule_id)
		salary_rule_code = salary_rule[0].code
		
		deducciones = self.pool.get('deduccion.tipo').search(self.cr, self.uid, [('input_code','=', salary_rule_code)])
		if len(deducciones) > 0:
			return self.pool.get('deduccion.tipo').browse(self.cr, self.uid,deducciones[0])[0].partida_contable.name
		else:	
			return '---'
		
	def get_salary_rule_name(self, salary_rule_id):
		salary_rule = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, salary_rule_id)
		salary_rule_name = salary_rule[0].name
		
		return salary_rule_name
		
	def get_salary_rule_total(self, payslips, salary_rule_id, tipo):
		salary_rule = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, salary_rule_id)
		
		if (tipo == 'haber' and salary_rule[0].category_id.code == 'NET') or (tipo == 'haber' and salary_rule[0].category_id.code == 'DED') or (tipo == 'debe' and salary_rule.category_id.code != 'DED' and salary_rule.category_id.code != 'NET'):
			salary_rule_total = 0
		
			for payslip in payslips:
				for line in payslip.line_ids:
					if line.salary_rule_id.id == salary_rule_id:
						salary_rule_total += line.amount
			return salary_rule_total
		else:
			return '-'

	def get_available_salary_rules(self, payslips):
		salary_rule_ids = []
		salary_rule_ids_sorted = []

                for payslip in payslips:
                        for line in payslip.line_ids:
                                if not line.salary_rule_id.id in salary_rule_ids:
                                        salary_rule_ids.append(line.salary_rule_id.id)
		
		salary_rules = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, salary_rule_ids)
		sorted_salary_rules = salary_rules.sorted(key=lambda r: r.sequence)

		for salary_rule in sorted_salary_rules:
			salary_rule_ids_sorted.append(salary_rule.id) 

                return salary_rule_ids_sorted

			
class wrapped_reporte_partida_detallada(osv.AbstractModel):
	_name = 'report.hr_bank_solusoft.report_reporte_partida_detallada_template'
	_inherit = 'report.abstract_report'
	_template = 'hr_bank_solusoft.report_reporte_partida_detallada_template'
	_wrapped_report_class = reporte_partida_detallada
