# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ShopifyCarrier(models.Model):
    _name = 'shopify.carrier'
    _description = 'Shopify Delivery Method to Carrier Mapping'

    name = fields.Char(string='Shopify Delivery Method', required=True, help="Name from Shopify's delivery method")
    carrier_id = fields.Many2one('delivery.carrier', string='Delivery Carrier')

    @api.model
    def get_or_create_by_name(self, name, vals=None):
        """Find a mapping by exact Shopify delivery method `name` or create it.

        :param name: Shopify delivery method label
        :param vals: Optional dict of values to set when creating (e.g., {'carrier_id': id})
        :return: recordset (shopify.carrier single record)
        """
        if not name:
            return self.browse()
        clean = name.strip()
        rec = self.search([('name', '=', clean)], limit=1)
        if rec:
            return rec
        vals = dict(vals or {})
        vals.setdefault('name', clean)
        return self.create(vals)
