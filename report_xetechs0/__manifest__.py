# -*- coding: utf-8 -*-
{
    'name': "report_xetechs0",

    'summary': """
        Sale order quotation with no prices, includes 2 reports: products only, total only""",

    'description': """
        module developed to add a quotation report that does not display the prices or the total of the quantity, this could bug
        be used show what type of services/products a company has offer""",

    'author': "XETECHS -->atobar@xetechs.com",
    'website': "http://www.xetechs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sale',
    'version': '2.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'reports/report.xml',
        'reports/xetechs_report.xml',
        'reports/xetechs_report_total.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
