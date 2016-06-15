# -*- coding: utf-8 -*-
##############################################################################
#
#    account_report_partnerbalance module for OpenERP, Extra Accounting Report Partner Balance
#    Copyright (C) 2016 SYLEAM Info Services (<http://www.syleam.fr>)
#              Sebastien LANGE <sebastien.lange@syleam.fr>
#
#    This file is a part of account_extra_report_partnerbalance
#
#    account_report_partnerbalance is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    account_report_partnerbalance is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import fields, models


class AccountPartnerBalance(models.TransientModel):
    _inherit = "account.common.partner.report"
    _name = "account.report.partner.balance"
    _description = "Account Partner Balance"

    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], help='If empty, get all partners')
    account_ids = fields.Many2many(comodel_name='account.account', string='Accounts', domain=[('internal_type', 'in', ('receivable', 'payable'))], help='If empty, get all accounts')

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({
            'partner_ids': self.partner_ids.mapped('id'),
            'account_ids': self.account_ids.mapped('id'),
        })
        return self.env['report'].get_action(self, 'account_report_partnerbalance.report_partnerbalance', data=data)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
