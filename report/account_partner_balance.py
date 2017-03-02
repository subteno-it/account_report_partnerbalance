# -*- coding: utf-8 -*-
##############################################################################
#
#    account_extra_report_partnerbalance module for OpenERP, Extra Accounting Report Partner Balance
#    Copyright (C) 2016 SYLEAM Info Services (<http://www.syleam.fr>)
#              Sebastien LANGE <sebastien.lange@syleam.fr>
#
#    This file is a part of account_extra_report_partnerbalance
#
#    account_extra_report_partnerbalance is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    account_extra_report_partnerbalance is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import time
from openerp import api, models


class ReportPartnerBalance(models.AbstractModel):
    _name = 'report.account_report_partnerbalance.report_partnerbalance'

    def _get_partner_ids(self, data, account):
        if data['form'].get('partner_ids'):
            partner_ids = data['form'].get('partner_ids')
        else:
            query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
            params = [tuple(data['computed']['move_state']), account.id] + query_get_data[2]
            query = """
                SELECT DISTINCT "account_move_line".partner_id
                FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
                WHERE "account_move_line".partner_id IS NOT NULL
                    AND "account_move_line".account_id = account.id
                    AND am.id = "account_move_line".move_id
                    AND am.state IN %s
                    AND "account_move_line".account_id = %s
                    AND NOT account.deprecated
                    AND """ + query_get_data[1]
            self.env.cr.execute(query, tuple(params))
            partner_move_ids = [res['partner_id'] for res in self.env.cr.dictfetchall() if res['partner_id'] is not 'None']
            query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}), initial_bal=True, date_to=False)._query_get()

            params = [tuple(data['computed']['move_state']), account.id] + query_get_data[2]
            query = """SELECT DISTINCT "account_move_line".partner_id, sum(debit - credit) AS sum
                    FROM """ + query_get_data[0] + """, account_move AS m
                    WHERE m.id = "account_move_line".move_id
                        AND m.state IN %s
                        AND account_id = %s
                        AND """ + query_get_data[1] + """ GROUP BY "account_move_line".partner_id"""
            self.env.cr.execute(query, tuple(params))
            partner_initial_move_ids = [res['partner_id'] for res in self.env.cr.dictfetchall() if res['partner_id'] is not 'None' and float(res['sum'] or 0.) != 0.]
            partner_ids = list(set(partner_move_ids) | set(partner_initial_move_ids))
        return partner_ids

    def _lines(self, data, account):
        partner_ids = self._get_partner_ids(data, account)
        full_account = []
        obj_partner = self.env['res.partner']
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.name))
        for partner in partners:
            r = {}
            r['partner'] = partner.ref and "[%s] %s" % (partner.ref, partner.name) or partner.name
            for field in ['initial', 'debit', 'credit', 'debit - credit']:
                if field == 'initial':
                    query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}), initial_bal=True, date_to=False)._query_get()
                    params = [partner.id, tuple(data['computed']['move_state']), account.id] + query_get_data[2]
                    query = """SELECT sum(debit - credit)
                            FROM """ + query_get_data[0] + """, account_move AS m
                            WHERE "account_move_line".partner_id = %s
                                AND m.id = "account_move_line".move_id
                                AND m.state IN %s
                                AND account_id = %s
                                AND """ + query_get_data[1] + """ GROUP BY "account_move_line".partner_id"""
                else:
                    query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
                    params = [partner.id, tuple(data['computed']['move_state']), account.id] + query_get_data[2]
                    query = """SELECT sum(""" + field + """)
                            FROM """ + query_get_data[0] + """, account_move AS m
                            WHERE "account_move_line".partner_id = %s
                                AND m.id = "account_move_line".move_id
                                AND m.state IN %s
                                AND account_id = %s
                                AND """ + query_get_data[1] + """ GROUP BY "account_move_line".partner_id"""
                self.env.cr.execute(query, tuple(params))
                result = self.env.cr.fetchone()
                r[field] = result is not None and result[0] or 0.0
            if not (r['initial'] == 0.0 and r['credit'] == 0.0 and r['debit'] == 0.0 and r['debit - credit'] == 0.0):
                full_account.append(r)
        return full_account

    def _sum_account(self, data, account, field):
        if field not in ['initial', 'debit', 'credit', 'debit - credit']:
            return
        result = 0.0
        partner_ids = self._get_partner_ids(data, account)
        if not partner_ids:
            return result
        if field == 'initial':
            query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}), initial_bal=True, date_to=False)._query_get()

            params = [account.id, tuple(data['computed']['move_state']), tuple(partner_ids)] + query_get_data[2]
            query = """SELECT sum(debit - credit)
                    FROM """ + query_get_data[0] + """, account_move AS m
                    WHERE "account_move_line".account_id = %s
                        AND m.id = "account_move_line".move_id
                        AND m.state IN %s
                        AND "account_move_line".partner_id IN %s
                        AND """ + query_get_data[1]
        else:
            query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()

            params = [account.id, tuple(data['computed']['move_state']), tuple(partner_ids)] + query_get_data[2]
            query = """SELECT sum(""" + field + """)
                    FROM """ + query_get_data[0] + """, account_move AS m
                    WHERE "account_move_line".account_id = %s
                        AND m.id = "account_move_line".move_id
                        AND m.state IN %s
                        AND "account_move_line".partner_id IN %s
                        AND """ + query_get_data[1]
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.multi
    def render_html(self, data):
        data['computed'] = {}

        obj_account = self.env['account.account']
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        if data['form'].get('account_ids'):
            account_ids = data['form'].get('account_ids')
        else:
            self.env.cr.execute("""
                SELECT a.id
                FROM account_account a
                WHERE a.internal_type IN %s
                AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
            account_ids = [a for (a,) in self.env.cr.fetchall()]
        if data['form'].get('partner_ids'):
            self.env.cr.execute("""
                SELECT DISTINCT account_id
                FROM account_move_line aml
                WHERE aml.partner_id IN %s
                AND aml.account_id IN %s""", (tuple(data['form']['partner_ids']), tuple(account_ids)))
            account_ids = [a for (a,) in self.env.cr.fetchall()]
        accounts = obj_account.browse(account_ids)
        accounts = sorted(accounts, key=lambda x: (x.code))

        docargs = {
            'doc_ids': account_ids,
            'doc_model': self.env['account.account'],
            'data': data,
            'docs': accounts,
            'time': time,
            'lines': self._lines,
            'sum_account': self._sum_account,
        }
        return self.env['report'].render('account_report_partnerbalance.report_partnerbalance', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
