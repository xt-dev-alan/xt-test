# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api
from num2words import num2words


class print_check(models.AbstractModel): 
    _name = 'report.dev_print_cheque.report_print_cheque'

    def get_date(self, date, obj):
        separator = obj.date_seprator
        year_format = 'Y' if obj.year_formate == 'yyyy' else 'y'

        if obj.date_formate == 'dd_mm':
            date_format = "%d{0}%m{0}%{1}".format(separator, year_format)
        else:
            date_format = "%m{0}%d{0}%{1}".format(separator, year_format)

        if date:
            date = date.strftime(date_format)
            return date
        return ''

    def get_partner_name(self,obj,p_text):
        return obj.partner_id


    def amount_word(self, obj):
        amt_word = obj.currency_id.with_context(lang=obj.partner_id.lang or 'es_ES').amount_to_text(obj.amount)
        lst = amt_word.split(' ')
        lst_len = len(lst)
        first_line = ''
        second_line = ''
        for l in range(0, lst_len):
            if lst[l] != 'euro':
                if obj.cheque_formate_id.word_in_f_line >= l:
                    if first_line:
                        first_line = first_line + ' ' + lst[l]
                    else:
                        first_line = lst[l]
                else:
                    if second_line:
                        second_line = second_line + ' ' + lst[l]
                    else:
                        second_line = lst[l]

        if obj.cheque_formate_id.is_star_word:
            first_line = '***' + first_line
            if second_line:
                second_line += '***'
            else:
                first_line=first_line+'***'

        first_line = first_line.replace(",", "")
        second_line = second_line.replace(",", "")

        return [first_line, second_line]




    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.payment'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'account.payment',
            'docs': docs,
#            'data': data,
            'get_date': self.get_date,
            'get_partner_name':self.get_partner_name,
            'amount_word':self.amount_word,
        }

class print_cheque_wizard(models.AbstractModel):
    _name = 'report.dev_print_cheque.cheque_report'

    def get_date(self, date):
        date = date.split('-')
        return date

    def amount_word(self, obj):
        amt = str(obj.amount)
        amt_lst = amt.split('.')
        amt_word = num2words(int(amt_lst[0]))
        lst = amt_word.split(' ')
        if float(amt_lst[1]) > 0:
            lst.append(' and '+amt_lst[1]+'/'+str(100))
        lst.append('only')
        lst_len = len(lst)
        lst_len = len(lst)
        first_line = ''
        second_line = ''
        for l in range(0, lst_len):
            if lst[l] != 'euro':
                if obj.cheque_formate_id.word_in_f_line >= l:
                    if first_line:
                        first_line = first_line + ' ' + lst[l]
                    else:
                        first_line = lst[l]
                else:
                    if second_line:
                        second_line = second_line + ' ' + lst[l]
                    else:
                        second_line = lst[l]

        if obj.cheque_formate_id.is_star_word:
            first_line = '***' + first_line
            if second_line:
                second_line += '***'
            else:
                first_line = first_line + '***'

        first_line = first_line.replace(",", "")
        second_line = second_line.replace(",", "")
        return [first_line, second_line]



    @api.multi
    def get_report_values(self, docids, data=None):
        docs = self.env['cheque.wizard'].browse(data['form'])
        return {
            'doc_ids': docs.ids,
            'doc_model': 'cheque.wizard',
            'docs': docs,
            'get_date': self.get_date,
            'amount_word':self.amount_word,
        }
            
    
        



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
