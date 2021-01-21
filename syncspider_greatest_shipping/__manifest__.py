# -*- coding: utf-8 -*-
{
    'name': "Syncspider - Greatest shipping Date",

    'summary': """
        """,

    'description': """
        Syncspider - Greatest shipping Date
    """,

    'author': "Callino",
    'website': "http://www.callino.at",
    'category': 'Misc',
    'version': '13.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['syncspider', 'sale', 'stock'],

    # always loaded
    'data': [
        'views/sale_order.xml'
    ],
    'qweb': [
    ],

}