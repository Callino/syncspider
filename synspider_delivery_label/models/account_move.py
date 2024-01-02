# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime
import logging
import requests
import base64
import json

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    delivery_weight = fields.Float(string="Versandgewicht")
    delivery_tariff = fields.Selection(selection=[
        ('b2b_AT', _('Paketpremium Österreich B2B (Österreich B2B)')),
        ('b2c_AT', _('Paketpremium Select Österreich (Österreich B2C)')),
        ('DE', _('Paket Plus International Outbound (Deutschland B2C und B2B)')),
        ('rest', _('Premium International Outbound B2B (Rest-EU B2B und B2C)'))
    ], string="Versandtarif")
    hook_id = fields.Many2one('sync.hook', string="Hook")

    @api.model_create_single
    def create(self, vals):
        country_at = self.env.ref("base.at").id
        country_de = self.env.ref("base.de").id
        invoice = super(AccountMove, self).create(vals)
        if invoice.partner_shipping_id.country_id.id not in [country_at, country_de]:
            invoice.delivery_tariff = 'rest'
        elif invoice.partner_shipping_id.country_id.id == country_de:
            invoice.delivery_tariff = 'DE'
        elif hasattr(invoice.partner_shipping_id, "b2b_b2c_type"):
            if invoice.partner_shipping_id.b2b_b2c_type == "b2c":
                invoice.delivery_tariff = 'b2c_AT'
            if invoice.partner_shipping_id.b2b_b2c_type == "b2b":
                invoice.delivery_tariff = 'b2b_AT'
        return invoice

    def get_webhook_data(self):
        return json.dumps({
            'delivery_address': {
                'firstname': self.partner_shipping_id.firstname,
                'lastname': self.partner_shipping_id.lastname,
                'company': self.partner_shipping_id.parent_id.name if self.partner_shipping_id.parent_id else False,
                'street': self.partner_shipping_id.street,
                'street_nr': self.partner_shipping_id.street_number,
                'zip': self.partner_shipping_id.zip,
                'city': self.partner_shipping_id.city,
                'country_id': self.partner_shipping_id.country_id.name if self.partner_shipping_id.country_id else False,
            },
            'delivery_weight': self.delivery_weight,
            'delivery_tariff': dict(self._fields['delivery_tariff'].selection).get(self.delivery_tariff),
            'invoice': self.name
        })

    def send_delivery_webhook(self):
        values = self.get_webhook_data()
        label_str = "Versandlabel erstellt, %s, Gewicht %r, %s" % (datetime.now().strftime("%d.%m.%Y %H:%M"), self.delivery_weight, dict(self._fields['delivery_tariff'].selection).get(self.delivery_tariff))
        if not self.hook_id:
            webhook_url = self.env['ir.config_parameter'].sudo().get_param('label.webhook.url')
            hook = self.env['sync.hook'].sudo().create({
                'name': "Labels %s" % self.name,
                'record_ref': self.name,
                'model': 'account.move',
                'record_id': self.id,
                'webhook_url': webhook_url
            })
            self.hook_id = hook
        event = self.env['sync.event'].sudo().create({
            'name': label_str,
            'hook_id': self.hook_id.id,
            'nexttry': datetime.now(),
            'payload': self.get_webhook_data()
        })
        event.run_async()
        self.message_post(body=label_str)
        return