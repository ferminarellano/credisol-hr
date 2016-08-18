# -*- coding: utf-8 -*-
# ©  2015 iDT LABS (http://www.@idtlabs.sl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    exclude_rest_days = fields.Boolean(
        'Excluir dias de descanso',
        help="Si esta seleccionado, los dias de descanso no serán tomados en cuenta para el calculo de ausencias.",
    )
    exclude_public_holidays = fields.Boolean(
        'Excluir feriados nacionales o regionales',
        help="Si esta seleccionado, los días feriados no serán tomados en cuenta para el cálculo de ausencias. ",
    )
