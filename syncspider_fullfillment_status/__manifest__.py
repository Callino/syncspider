# -*- coding: utf-8 -*-
{
    'name': "Syncspider - Fullfillment Status",

    'summary': """
        """,

    'description': """
        Syncspider - Fullfillment Status
    """,

    'author': "Callino",
    'website': "http://www.callino.at",
    'category': 'Misc',
    'version': '13.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['syncspider', 'sale', 'stock', 'account'],

    # always loaded
    'data': [
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/stock_picking.xml'
    ],
    'qweb': [
    ],

}