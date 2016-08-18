#-*- coding:utf-8 -*-

from openerp.osv import osv
from openerp.report import report_sxw

class reporte_planilla(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(reporte_planilla, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'get_payroll_headers': self.get_payroll_headers,
			'get_available_salary_rules': self.get_available_salary_rules,
			'get_payslip_line': self.get_payslip_line,
			'get_salary_rule_total': self.get_salary_rule_total
		})

	def get_salary_rule_total(self, payslips, salary_rule_id):
		salary_rule_total = 0
		
		for payslip in payslips:
			for line in payslip.line_ids:
				if line.salary_rule_id.id == salary_rule_id:
					salary_rule_total += line.amount

		return salary_rule_total
	
	def get_payroll_headers(self, payslips):
		salary_rule_ids = []
		salary_rule_names = []

		for payslip in payslips:
			for line in payslip.line_ids:
				if not line.salary_rule_id.id in salary_rule_ids:
					salary_rule_ids.append(line.salary_rule_id.id)
		
		salary_rules = self.pool.get('hr.salary.rule').browse(self.cr, self.uid, salary_rule_ids)
		sorted_salary_rules = salary_rules.sorted(key=lambda r: r.sequence)
		
		for salary_rule in sorted_salary_rules:
			salary_rule_names.append(salary_rule.name.upper()
)
		return salary_rule_names

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

	def get_payslip_line(self, payslip, salary_rule_id):

		for line in payslip.line_ids:
			if line.salary_rule_id.id == salary_rule_id:
				if line.salary_rule_id.category_id.code == 'ALW':
					return line.amount*(-1)
				else:
					return line.amount
		
		return 0
			
class wrapped_reporte_planilla(osv.AbstractModel):
	_name = 'report.hr_bank_solusoft.report_reporte_planilla_template'
	_inherit = 'report.abstract_report'
	_template = 'hr_bank_solusoft.report_reporte_planilla_template'
	_wrapped_report_class = reporte_planilla
