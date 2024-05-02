# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    gateway = fields.Char(string="Gateway", readonly=True)
    payment_ref = fields.Char(string="Payment Reference", readonly=True)
    amount_received = fields.Float(string="Amount Received", readonly=True)
    payment_status = fields.Selection(selection=[
        ('Pending', _('Pending')),
        ('Authorized', _('Authorized')),
        ('Overdue', _('Overdue')),
        ('Expiring', _('Expiring')),
        ('Expired', _('Expired')),
        ('Paid', _('Paid')),
        ('Refunded', _('Refunded')),
        ('Partially refunded', _('Partially refunded')),
        ('Partially paid', _('Partially paid')),
        ('Voided', _('Voided')),
        ('Unpaid', _('Unpaid')),
    ], string="Payment Status", readonly=True)
    auto_downpayment = fields.Boolean(string="Automatische Anzahlung", default=False)
    shopify_delivery_method = fields.Char(string="Liefermethode", readonly=1)
    shopify_delivery_amount = fields.Float(string="Lieferbetrag", readonly=1)
    original_date = fields.Datetime(string="Originalbestelldatum")

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SaleOrder, self).create(vals_list)
        for record in records:
            try:
                if record.amount_received:
                    record.amount_received = record.amount_received / 100
                if record.user_id.login == 'syncspider':
                    record.auto_downpayment = True
                    record.original_date = record.date_order
            except Exception as e:
                _logger.warning("Error setting order values: %s" % e)
        return records

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if not order.user_id:
                continue
            if not order.user_id.login == 'syncspider':
                continue
            if order.payment_status not in ["Paid", "Partially paid"]:
                continue
            if (order.payment_status == "Partially paid") and not order.amount_received:
                continue
            if order.auto_downpayment:
                amount = order.amount_received
                if not amount:
                    amount = order.amount_total
                sapi = self.env['sale.advance.payment.inv'].with_context(active_ids=order.ids).create({
                    'advance_payment_method': 'fixed',
                    'fixed_amount': amount
                })
                sapi.sudo().create_invoices()
                if order.gateway == 'paypal' and order.payment_ref:
                    order.invoice_ids.write({'invoice_origin': order.payment_ref})
                # disabled for review by customer
                order.invoice_ids.action_post()
                for invoice in order.invoice_ids:
                    apr = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create({
                        # 'communication': self.payment_ref,
                        'payment_date': order.original_date or order.date_order
                    })
                    apr.action_create_payments()
                #     template = self.env.ref(invoice._get_mail_template(), raise_if_not_found=False)
                #     if template:
                #         template.send_mail(invoice.id)
        return res