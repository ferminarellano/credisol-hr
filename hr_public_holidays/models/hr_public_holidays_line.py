# -*- coding: utf-8 -*-
# ©  2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# ©  2014 initOS GmbH & Co. KG <http://www.initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api
from openerp.exceptions import Warning as UserError


class HrPublicHolidaysLine(models.Model):
    _name = 'hr.holidays.public.line'
    _description = 'Public Holidays Lines'
    _order = "date, name desc"

    name = fields.Char(
        'Name',
        required=True,
    )
    date = fields.Date(
        'Date',
        required=True
    )
    year_id = fields.Many2one(
        'hr.holidays.public',
        'Calendar Year',
        required=True,
    )
    variable = fields.Boolean('Date may change')
    state_ids = fields.Many2many(
        'res.country.state',
        'hr_holiday_public_state_rel',
        'line_id',
        'state_id',
        'Related States'
    )

    @api.one
    @api.constrains('date', 'state_ids')
    def _check_date_state(self):
        if fields.Date.from_string(self.date).year != self.year_id.year:
            raise UserError(
                'La fecha de los feriados deben ser en el mismo año que el periodo al cual estan siendo asignados.'
            )
        if self.state_ids:
            domain = [('date', '=', self.date),
                      ('year_id', '=', self.year_id.id),
                      ('state_ids', '!=', False),
                      ('id', '!=', self.id)]
            holidays = self.search(domain)
            for holiday in holidays:
                if self.state_ids & holiday.state_ids:
                    raise UserError('No puede crear dos feriados en una misma fecha %s para un mismo departamento.' % self.date)
        domain = [('date', '=', self.date),
                  ('year_id', '=', self.year_id.id),
                  ('state_ids', '=', False)]
        if self.search_count(domain) > 1:
            raise UserError('No puede crear dos feriados en una misma fecha %s.' % self.date)
        return True
