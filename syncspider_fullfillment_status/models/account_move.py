# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('invoice_line_ids.sale_line_ids.order_id.fullfillment_status')
    def _get_fullfillment_status(self):
        for record in self:
            orders = record.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
            if not orders:
                record.fullfillment_status = False
                continue
            if len(orders) > 1:
                record.fullfillment_status = orders[0].fullfillment_status
                continue
            record.fullfillment_status = orders.fullfillment_status

    def _set_fullfillment_status(self):
        for record in self:
            orders = record.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
            orders.write({'fullfillment_status': record.fullfillment_status})
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
