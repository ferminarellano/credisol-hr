# -*- coding: utf-8 -*-
# ©  2015 iDT LABS (http://www.@idtlabs.sl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from dateutil import tz
from datetime import date, timedelta, datetime
import math


class HrHolidays(models.Model):
	_inherit = 'hr.holidays'

	@api.model
	def _check_date_helper(self, employee_id, date):
		status_id = self.holiday_status_id.id or self.env.context.get('holiday_status_id',False)
		if employee_id and status_id:
			employee = self.env['hr.employee'].browse(employee_id)
			status = self.env['hr.holidays.status'].browse(status_id)
			if date and (not employee.work_scheduled_on_day(
					self._datetime_to_local_timezone(fields.Datetime.from_string(date)),
					public_holiday=status.exclude_public_holidays,
					schedule=status.exclude_rest_days)):
				return False
		return True

	@api.multi
	def onchange_employee(self, employee_id):
		res = super(HrHolidays, self).onchange_employee(employee_id)
		date_from = self.date_from or self.env.context.get('date_from')
		date_to = self.date_to or self.env.context.get('date_to')
		if (date_to and date_from) and (date_from <= date_to):
			if not self._check_date_helper(employee_id, date_from):
				raise ValidationError(_("No puede programar la fecha inicial en un feriado o día de descanso"))
			if not self._check_date_helper(employee_id, date_to):
				raise ValidationError(_("No puede programar la fecha final en un feriado o día de descanso"))
			duration = self._compute_number_of_days(employee_id,
													date_to,
													date_from)
			res['value']['number_of_days_temp'] = duration
		return res

	@api.multi
	def onchange_date_from(self, date_to, date_from):
		res = super(HrHolidays, self).onchange_date_from(date_to, date_from)
		employee_id = self.employee_id.id or self.env.context.get(
			'employee_id',
			False)
		if not self._check_date_helper(employee_id, date_from):
			raise ValidationError(_("No puede programar la fecha inicial en un feriado o día de descanso"))
		if (date_to and date_from) and (date_from <= date_to):
			diff_day = self._compute_number_of_days(employee_id,
													date_to,
													date_from)
			res['value']['number_of_days_temp'] = diff_day
		return res

	@api.multi
	def onchange_date_to(self, date_to, date_from):
		res = super(HrHolidays, self).onchange_date_to(date_to, date_from)
		employee_id = self.employee_id.id or self.env.context.get(
			'employee_id',
			False)
		if not self._check_date_helper(employee_id, date_to):
			raise ValidationError(_("No puede programar la fecha final en un feriado o día de descanso"))
		if (date_to and date_from) and (date_from <= date_to):
			diff_day = self._compute_number_of_days(employee_id,
													date_to,
													date_from)
			res['value']['number_of_days_temp'] = diff_day
		return res
		
	@api.multi
	def onchange_holiday_status_id(self, employee_id, date_to, date_from):
		res = {'value': {}}
		employee_id = self.employee_id.id or self.env.context.get('employee_id', False)
		
		if not self._check_date_helper(employee_id, date_from):
			raise ValidationError(_("No puede programar la fecha inicial en un feriado o día de descanso"))
		
		if not self._check_date_helper(employee_id, date_to):
			raise ValidationError(_("No puede programar la fecha final en un feriado o día de descanso"))
									
		if (date_to and date_from) and (date_from <= date_to):
			diff_day = self._compute_number_of_days(employee_id, date_to, date_from)
			res['value']['number_of_days_temp'] = diff_day
		return res
		
	def _datetime_to_local_timezone(self, utc_datetime):
		local_timezone = tz.gettz('America/Tegucigalpa')
		utc_timezone = tz.gettz('UTC')
		gmt = utc_datetime.replace(tzinfo=utc_timezone)
		local_timezone_date = gmt.astimezone(local_timezone)
		return local_timezone_date
		
	def _get_number_of_days(self, date_from, date_to):
		DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
		from_dt = self._datetime_to_local_timezone(datetime.strptime(date_from, DATETIME_FORMAT))
		to_dt = self._datetime_to_local_timezone(datetime.strptime(date_to, DATETIME_FORMAT))
		number_of_days = 0
		
		daygenerator = (from_dt + timedelta(x) for x in xrange((to_dt - from_dt).days+1))
		
		for day in daygenerator:
			if day.weekday() < 5:
				number_of_days += 1
			elif day.weekday() == 5:
				number_of_days += 0.5
				
		return number_of_days
		
	def _compute_number_of_days(self, employee_id, date_to, date_from):
		days = self._get_number_of_days(date_from, date_to)
			
		status_id = self.holiday_status_id.id or self.env.context.get('holiday_status_id', False)
		
		if employee_id and date_from and date_to and status_id:
			employee = self.env['hr.employee'].browse(employee_id)
			status = self.env['hr.holidays.status'].browse(status_id)
			date_from = self._datetime_to_local_timezone(fields.Datetime.from_string(date_from))
			date_to = self._datetime_to_local_timezone(fields.Datetime.from_string(date_to))
			date_dt = date_from
			
			while date_dt <= date_to: 
				if not employee.work_scheduled_on_day(date_dt, status.exclude_public_holidays, status.exclude_rest_days):
					if date_dt.weekday() < 5:
						days -= 1
					elif date_dt.weekday() == 5:
						days -= 0.5
						
				date_dt += relativedelta(days=1) # le suma un dia a la fecha. 
				
		return days
		
		
		
		
		
		
