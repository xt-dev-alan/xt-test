# -*- coding: utf-8 -*-

{
    'name': 'Pawn Shop',
    'version': '1.0.1',
    'author': 'Xetechs GT',
    'website': 'https://xetechs.com',
    'license': 'LGPL-3',
    'depends': [
        'sale_management',
        'stock'
    ],
    'data': [
        'data/product_data.xml',
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/pawn_views.xml'
    ]
}