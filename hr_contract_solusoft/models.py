import time
from itertools import ifilter
from datetime import date, datetime
from openerp.osv import osv
from openerp.report import report_sxw

class hr_contract_report(report_sxw.rml_parse):
	UNIDADES = ('','UN ','DOS ','TRES ','CUATRO ','CINCO ','SEIS ','SIETE ','OCHO ','NUEVE ','DIEZ ','ONCE ','DOCE ','TRECE ','CATORCE ','QUINCE ','DIECISEIS ','DIECISIETE ','DIECIOCHO ','DIECINUEVE ','VEINTE ')
	DECENAS = ('VEINTI','TREINTA ','CUARENTA ','CINCUENTA ','SESENTA ','SETENTA ','OCHENTA ','NOVENTA ','CIEN ')
	CENTENAS = ('CIENTO ','DOSCIENTOS ','TRESCIENTOS ','CUATROCIENTOS ','QUINIENTOS ','SEISCIENTOS ','SETECIENTOS ','OCHOCIENTOS ','NOVECIENTOS ')
	UNITS = (('',''),('MIL ','MIL '),('MILLON ','MILLONES '),('MIL MILLONES ','MIL MILLONES '),('BILLON ','BILLONES '),('MIL BILLONES ','MIL BILLONES '),('TRILLON ','TRILLONES '),('MIL TRILLONES','MIL TRILLONES'),('CUATRILLON','CUATRILLONES'),('MIL CUATRILLONES','MIL CUATRILLONES'),('QUINTILLON','QUINTILLONES'),('MIL QUINTILLONES','MIL QUINTILLONES'),('SEXTILLON','SEXTILLONES'),('MIL SEXTILLONES','MIL SEXTILLONES'),('SEPTILLON','SEPTILLONES'),('MIL SEPTILLONES','MIL SEPTILLONES'),('OCTILLON','OCTILLONES'),('MIL OCTILLONES','MIL OCTILLONES'),('NONILLON','NONILLONES'),('MIL NONILLONES','MIL NONILLONES'),('DECILLON','DECILLONES'),('MIL DECILLONES','MIL DECILLONES'),('UNDECILLON','UNDECILLONES'),('MIL UNDECILLONES','MIL UNDECILLONES'),('DUODECILLON','DUODECILLONES'),('MIL DUODECILLONES','MIL DUODECILLONES'),)
	MONEDAS = (
		{'country': u'Honduras', 'currency': 'HNL', 'singular': u'LEMPIRA', 'plural': u'LEMPIRAS', 'symbol': u'L'},
		{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
		{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'}
	)
		
	def __init__(self, cr, uid, name, context): 
		super(hr_contract_report, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_age': self._get_age,
			'get_marital': self._get_marital,
			'to_word': self._to_word,
			'date_to_word': self._date_to_word
		})
		
	def _date_to_word(self, contract):
		fecha_inicio = datetime.strptime(contract.date_start, '%Y-%m-%d')
		dia = fecha_inicio.day
		anio = fecha_inicio.year
		mes = fecha_inicio.month
		meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
		
		return self._to_word(dia) + ' dias del mes de ' + meses[(mes-1)] + ' del ' + str(anio)
			
	def _get_age(self,born, date_start):
		birth = datetime.strptime(born,"%Y-%m-%d").date()
		today = datetime.strptime(date_start,"%Y-%m-%d").date()
		return today.year - birth.year - ((today.month,today.day) < (birth.month, birth.day))
		
	def _get_marital(self, marital_status, gender):
		if marital_status == 'Soltero(a)' or marital_status == 'single':
			return 'soltero' if gender == 'male' else 'soltera'

		if marital_status == 'Casado (a)' or marital_status == 'married':
			return 'casado' if gender == 'male' else 'casada'

		if marital_status == 'Viudo(a)' or marital_status == 'widower':
			return 'viudo' if gender == 'male' else 'viuda'
			
		if marital_status == 'Divorciado' or marital_status == 'divorced':
			return 'divorciado' if gender == 'male' else 'divorciada'
			
		if marital_status == 'Union Libre' or marital_status == 'union':
			return 'en unión libre'
		return 'X'+marital_status+'X'
		
	def hundreds_word(self,number):
		converted = ''
		if not (0 < number < 1000):
			return 'No es posible convertir el numero a letras'

		number_str = str(number).zfill(9)
		cientos = number_str[6:]

		if(cientos):
			if(cientos == '001'):
				converted += 'UN '
			elif(int(cientos) > 0):
				converted += '%s ' % self.convert_group(cientos)

		return converted.title().strip()
		
	def convert_group(self,n):
		output = ''

		if(n == '100'):
			output = "CIEN "
		elif(n[0] != '0'):
			output = self.CENTENAS[int(n[0]) - 1]

		k = int(n[1:])
		if(k <= 20):
			output += self.UNIDADES[k]
		else:
			if((k > 30) & (n[2] != '0')):
				output += '%sy %s' % (self.DECENAS[int(n[1]) - 2], self.UNIDADES[int(n[2])])
			else:
				output += '%s%s' % (self.DECENAS[int(n[1]) - 2], self.UNIDADES[int(n[2])])

		return output
	def _to_word(self, number, mi_moneda=None):
		if mi_moneda != None:
			try:
				moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
				if number < 2:
					moneda = moneda['singular']
				else:
					moneda = moneda['plural']
			except:
				return "Tipo de moneda inválida XX"+number+"XX"
		else:
			moneda = ""

		human_readable = []
		num_units = format(number,',').split(',')
		#print num_units
		for i,n in enumerate(num_units):
			if int(n) != 0:
				words = self.hundreds_word(int(n))
				units = self.UNITS[len(num_units)-i-1][0 if int(n) == 1 else 1]
				human_readable.append([words,units])

		#filtrar MIL MILLONES - MILLONES -> MIL - MILLONES
		for i,item in enumerate(human_readable):
			try:
				if human_readable[i][1].find(human_readable[i+1][1]):
					human_readable[i][1] = human_readable[i][1].replace(human_readable[i+1][1],'')
			except IndexError:
				pass
		human_readable = [item for sublist in human_readable for item in sublist]
		human_readable.append(moneda)
		return ' '.join(human_readable).replace('  ',' ').title().strip()
		

class report_hr_contract(osv.AbstractModel):
	_name = 'report.hr_contract_solusoft.report_contrato_permanente_template'
	_inherit = 'report.abstract_report'
	_template = 'hr_contract_solusoft.report_contrato_permanente_template'
	_wrapped_report_class = hr_contract_report
