# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('sale_id.fullfillment_status')
    def _get_fullfillment_status(self):
        for record in self:
            record.fullfillment_status = record.sale_id.fullfillment_status

    def _set_fullfillment_status(self):
        for record in self:
            record.sale_id.write({'fullfillment_status': record.fullfillment_status})
            return True

    fullfillment_status = fields.Selection(selection=[
        ('waiting', _('warten auf Abholung')),
        ('picked_up', _('abgeholt')),
        ('sent', _('versendet')),
        ('retourned', _('retourniert'))],
        string="Fullfillment Status",
        compute="_get_fullfillment_status",
        inverse="_set_fullfillment_status",
        store=True)
