# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__
                            )

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ebay_category = fields.Char('Ebay Category', index=True)
    ebay_shop_category = fields.Char('Ebay Shop Category', index=True)
