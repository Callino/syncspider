# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__
                            )

class ProductProduct(models.Model):
    _inherit = 'product.product'

    ebay_category = fields.Char('Ebay Category', index=True)
    ebay_shop_category = fields.Char('Ebay Shop Category', index=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ebay_category = fields.Char('Ebay Category', compute='_compute_ebay_category', inverse='_set_ebay_category', store=True)
    ebay_shop_category = fields.Char('Ebay Shop Category', compute='_compute_ebay_shop_category', inverse='_set_ebay_shop_category', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.ebay_category')
    def _compute_ebay_category(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.ebay_category = template.product_variant_ids.ebay_category
        for template in (self - unique_variants):
            template.ebay_category = False

    def _set_ebay_category(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.ebay_category = template.ebay_category

    @api.depends('product_variant_ids', 'product_variant_ids.ebay_category')
    def _compute_ebay_shop_category(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.ebay_shop_category = template.product_variant_ids.ebay_shop_category
        for template in (self - unique_variants):
            template.ebay_shop_category = False

    def _set_ebay_shop_category(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.ebay_shop_category = template.ebay_shop_category
