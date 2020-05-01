# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class report_xetechs0(models.Model):
#     _name = 'report_xetechs0.report_xetechs0'
#     _description = 'report_xetechs0.report_xetechs0'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
