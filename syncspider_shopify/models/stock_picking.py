# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime
import logging
import json

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hook_id = fields.Many2one('sync.hook', string="Hook")
    bom_hook_id = fields.Many2one('sync.hook', string="Hook")

    def get_webhook_data(self, package):
        vals = {
            'order_nr': self.sale_id.name,
            'carrier_id': self.carrier_id.id if self.carrier_id else '0',
            'carrier': self.carrier_id.name if self.carrier_id else 'no_carrier',
            'complete': False if ((self.backorder_ids) or (self.sale_id.picking_ids.filtered(lambda f: f.state not in ('done', 'cancel')))) else True,
            'package': False,
        }
        package_vals = {
            "tracking_nr": package.name,
            "delivery_weight": package.shipping_weight,
            "package_products": []
        }
        for quant in package.quant_ids.filtered(lambda f: f.product_id.id not in self.move_ids.filtered(lambda f: f.bom_line_id).mapped('product_id').ids):
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
            if not package.quant_ids.filtered(lambda f: f.product_id.id not in self.move_ids.filtered(lambda f: f.bom_line_id).mapped('product_id').ids):
                continue
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

    def check_bom_lines_finished(self):
        if not self.sale_id:
            return
        if not self.sale_id.gateway:
            return
        if not 'MH' in self.sale_id.name:
            return
        for order_line in self.sale_id.order_line:
            if order_line.qty_delivered_method == 'stock_move':
                boms = order_line.move_ids.filtered(lambda m: m.state != 'cancel').mapped('bom_line_id.bom_id')
                if boms and (order_line.qty_delivered == order_line.product_uom_qty):
                    event_str = "Versand zu %s Rücksync, %s" % (order_line.name, datetime.now().strftime("%d.%m.%Y %H:%M"))
                    if not self.bom_hook_id:
                        webhook_url = self.env['ir.config_parameter'].sudo().get_param('picking_resync.webhook.url.bom')
                        hook = self.env['sync.hook'].sudo().create({
                            'name': "Rücksync %s" % (self.name or self.id),
                            'record_ref': self.name or self.id,
                            'model': 'stock.picking',
                            'record_id': self.id,
                            'webhook_url': webhook_url
                        })
                        self.bom_hook_id = hook
                    event = self.env['sync.event'].sudo().create({
                        'name': event_str,
                        'hook_id': self.bom_hook_id.id,
                        'nexttry': datetime.now(),
                        'payload': json.dumps({
                            "order_nr": self.sale_id.name,
                            "carrier_id": self.carrier_id.id if self.carrier_id else '0',
                            "carrier": self.carrier_id.name if self.carrier_id else 'no_carrier',
                            "product_id": order_line.product_id.id,
                            "quantity": order_line.qty_delivered,
                            "tracking": order_line.move_ids.mapped('move_line_ids').mapped('result_package_id').mapped('name')
                        })
                    })
                    event.run_async()
                    self.message_post(body=event_str)


    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for record in self:
            record.send_delivery_webhook()
            record.check_bom_lines_finished()
        return res