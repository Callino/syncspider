# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    gateway = fields.Char(string="Gateway", readonly=True)
    amount_received = fields.Float(string="Amount Received", readonly=False)
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

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if not order.user_id:
                continue
            if not order.user_id.login == 'syncspider':
                continue
            if order.auto_downpayment:
                sapi = self.env['sale.advance.payment.inv'].with_context(active_ids=order.ids).create({
                    'advance_payment_method': 'fixed',
                    'fixed_amount': order.amount_received
                })
                sapi.sudo().create_invoices()
                order.invoice_ids.action_post()
                for invoice in order.invoice_ids:
                    template = self.env.ref(invoice._get_mail_template(), raise_if_not_found=False)
                    if template:
                        template.send_mail(invoice.id)
        return res