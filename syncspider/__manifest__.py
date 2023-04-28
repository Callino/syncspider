# -*- coding: utf-8 -*-
{
    'name': "Syncspider Integration",

    'description': """
        Provide webhooks to integrate with syncspider
    """,

    'author': "Syncspider (hello@syncspider.com)",
    'maintainer': "Syncspider (support@syncspider.com)",
    'website': "https://www.syncspider.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '14.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'stock', 'sale'],

    # always loaded
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv',
        'views/sync_hook.xml',
        'data/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}