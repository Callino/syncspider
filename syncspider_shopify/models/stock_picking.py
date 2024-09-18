# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime
import logging
import json

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hook_id = fields.Many2one('sync.hook', string="Hook")

    def get_webhook_data(self, package):
        vals = {
            'order_nr': self.sale_id.name,
            'carrier': self.carrier_id.name if self.carrier_id else 'no_carrier',
            'complete': False if self.backorder_ids else True,
            'package': False,
        }
        package_vals = {
            "tracking_nr": package.name,
            "delivery_weight": package.shipping_weight,
            "package_products": []
        }
        for quant in package.quant_ids:
            package_vals['package_products'].append({
                'product_id': quant.product_id.id,
                'qty': quant.quantity,
            })
        vals['package'] = package_vals
        return json.dumps(vals)

    def send_delivery_webhook(self):
        if not self.sale_id:
            return
        if not self.sale_id.gateway:
            return
        if not 'MH' in self.sale_id.name:
            return
        for package in self.package_ids:
            values = self.get_webhook_data(package)
            event_str = "Versand zu %s Rücksync, %s" % (package.name, datetime.now().strftime("%d.%m.%Y %H:%M"))
            if not self.hook_id:
                webhook_url = self.env['ir.config_parameter'].sudo().get_param('picking_resync.webhook.url')
                hook = self.env['sync.hook'].sudo().create({
                    'name': "Rücksync %s" % (self.name or self.id),
                    'record_ref': self.name or self.id,
                    'model': 'stock.picking',
                    'record_id': self.id,
                    'webhook_url': webhook_url
                })
                self.hook_id = hook
            event = self.env['sync.event'].sudo().create({
                'name': event_str,
                'hook_id': self.hook_id.id,
                'nexttry': datetime.now(),
                'payload': values
            })
            event.run_async()
            self.message_post(body=event_str)
        return

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if res == True:
            for record in self:
                record.send_delivery_webhook()
        return res