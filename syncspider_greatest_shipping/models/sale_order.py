# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_greatest_shipping_date(self):
        for record in self:
            if record.picking_ids:
                record.greatest_shipping_date = record.picking_ids.sorted(key=lambda r: r.scheduled_date)[len(record.picking_ids)-1].scheduled_date
            else:
                record.greatest_shipping_date = False


    greatest_shipping_date = fields.Datetime(compute="_get_greatest_shipping_date", string="Greatest Shipping Date")
