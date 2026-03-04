# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime
import logging
import json

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hook_id = fields.Many2one('sync.hook', string="Hook")
    bom_hook_id = fields.Many2one('sync.hook', string="BOM Hook")

    def _get_fulfillment_webhook_url(self):
        """Get the webhook URL for fulfillment/delivery notifications."""
        if self.sale_id:
            webhook_url = self.env['sync.config'].get_webhook_url(self.sale_id.name)
            if webhook_url:
                return webhook_url
        # Fallback to global config parameter
        return self.env['ir.config_parameter'].sudo().get_param('picking_resync.webhook.url')

    def _get_bom_webhook_url(self):
        """Get the webhook URL for BOM completion notifications."""
        if self.sale_id:
            webhook_url = self.env['sync.config'].get_webhook_url_bom(self.sale_id.name)
            if webhook_url:
                return webhook_url
        # Fallback to global config parameter
        return self.env['ir.config_parameter'].sudo().get_param('picking_resync.webhook.url.bom')

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

    def _get_sync_config(self):
        """Get sync config for this picking's sale order."""
        if not self.sale_id:
            return False
        return self.env['sync.config'].get_config_for_order(self.sale_id.name)

    def send_delivery_webhook(self):
        if not self.sale_id:
            return
        sync_config = self._get_sync_config()
        if not sync_config or not sync_config.send_webhook:
            return
        for package in self.package_ids:
            if not package.quant_ids.filtered(lambda f: f.product_id.id not in self.move_ids.filtered(lambda f: f.bom_line_id).mapped('product_id').ids):
                continue
            values = self.get_webhook_data(package)
            event_str = "Versand zu %s Rücksync, %s" % (package.name, datetime.now().strftime("%d.%m.%Y %H:%M"))
            if not self.hook_id:
                webhook_url = self._get_fulfillment_webhook_url()
                if not webhook_url:
                    _logger.warning("No fulfillment webhook URL configured, skipping webhook for %s", self.name)
                    continue
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
        sync_config = self._get_sync_config()
        if not sync_config or not sync_config.send_webhook:
            return
        for order_line in self.sale_id.order_line:
            if order_line.product_id.detailed_type == 'product':
                boms = order_line.move_ids.filtered(lambda m: m.state != 'cancel').mapped('bom_line_id.bom_id')
                if boms and (order_line.qty_delivered == order_line.product_uom_qty):
                    event_str = "Versand zu %s Rücksync, %s" % (order_line.name, datetime.now().strftime("%d.%m.%Y %H:%M"))
                    if not self.bom_hook_id:
                        webhook_url = self._get_bom_webhook_url()
                        if not webhook_url:
                            _logger.warning("No BOM webhook URL configured, skipping webhook for %s", self.name)
                            continue
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