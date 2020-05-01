# -*- coding: utf-8 -*-
# from odoo import http


# class ReportXetechs0(http.Controller):
#     @http.route('/report_xetechs0/report_xetechs0/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_xetechs0/report_xetechs0/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_xetechs0.listing', {
#             'root': '/report_xetechs0/report_xetechs0',
#             'objects': http.request.env['report_xetechs0.report_xetechs0'].search([]),
#         })

#     @http.route('/report_xetechs0/report_xetechs0/objects/<model("report_xetechs0.report_xetechs0"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_xetechs0.object', {
#             'object': obj
#         })
