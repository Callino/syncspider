# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def set_qty_and_mark_done(self):
        for picking in self:
            for line in picking.move_ids_without_package:
                try:
                    line.write({'quantity_done': line.product_uom_qty, 'state': 'assigned'})
                except Exception as e:
                    _logger.info("Cannot write line qty at this point.")
            picking.button_validate()