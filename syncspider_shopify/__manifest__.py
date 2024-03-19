# -*- coding: utf-8 -*-
{
    'name': "Syncspider Shopify",

    'description': """
        Adds Shopify fields an logic
    """,

    'author': "Syncspider (hello@syncspider.com)",
    'maintainer': "Syncspider (support@syncspider.com)",
    'website': "https://www.syncspider.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '16.0.1.0.0',
    "license": "LGPL-3",
    # any module necessary for this one to work correctly
    'depends': ['syncspider', 'sale'],

    # always loaded
    'data': [
        'views/sale_order.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}