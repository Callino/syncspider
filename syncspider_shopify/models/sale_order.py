# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.fields import Command
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('gateway')
    def _get_shopify_gateway(self):
        for record in self:
            if not record.gateway:
                record.gateway_id = False
                continue
            if not record.gateway.strip():
                record.gateway_id = False
                continue
            gateway = self.env['shopify.gateway'].search([('name', '=', record.gateway.strip())], limit=1)
            if not gateway:
                gateway = self.env['shopify.gateway'].create({'name': record.gateway.strip()})
            record.gateway_id = gateway.id

    gateway = fields.Char(string="Gateway", readonly=True)
    gateway_id = fields.Many2one('shopify.gateway', string="Gateway Journal", compute="_get_shopify_gateway", store=True)
    payment_ref = fields.Char(string="Payment Reference", readonly=True)
    amount_received = fields.Float(string="Amount Received", readonly=True)
    shopify_amount_total = fields.Float(string="Shopify Amount Total", copy=False)
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
    shopify_delivery_method = fields.Char(string="Liefermethode", readonly=0)
    shopify_delivery_amount = fields.Float(string="Lieferbetrag", readonly=0)
    shopify_global_discount_amount = fields.Float(string="Monetärer Discount auf Auftrag", tracking=True, copy=False)
    shopify_global_discount_text = fields.Char(string="Text Discount auf Auftrag", tracking=True, copy=False)
    original_date = fields.Datetime(string="Originalbestelldatum")

    # Computed Shopify carrier mapping record (like gateway_id)
    @api.depends('shopify_delivery_method')
    def _compute_shopify_carrier(self):
        for record in self:
            if not record.shopify_delivery_method or not record.shopify_delivery_method.strip():
                record.shopify_carrier_id = False
                continue
            name = record.shopify_delivery_method.strip()
            mapping = self.env['shopify.carrier'].search([('name', '=', name)], limit=1)
            if not mapping:
                # Create placeholder mapping if missing (carrier can be set later via UI)
                mapping = self.env['shopify.carrier'].create({'name': name})
            record.shopify_carrier_id = mapping.id

    shopify_carrier_id = fields.Many2one(
        'shopify.carrier',
        compute='_compute_shopify_carrier',
        store=True,
        string='Shopify Carrier Mapping'
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SaleOrder, self).create(vals_list)
        for record in records:
            try:
                record.check_global_discount()
            except Exception as e:
                _logger.warning("Error setting order values: %s" % e)
            try:
                if record.amount_received:
                    record.amount_received = record.amount_received / 100
                if record.user_id.login == 'syncspider':
                    record.auto_downpayment = True
                    record.original_date = record.date_order
            except Exception as e:
                _logger.warning("Error setting order values: %s" % e)
        return records

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for order in self:
            try:
                order.check_global_discount()
            except Exception as e:
                _logger.warning("Error checking global discount: %s" % e)
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        order = super(SaleOrder, self).copy(default)
        reward_product = self.env['product.product'].search([('global_discount_product', '=', True)], limit=1)
        reward_lines = order.order_line.filtered(lambda f: f.product_id.id == reward_product.id)
        rounding_error_lines = order.order_line.filtered(lambda f: f.is_rounding_error_line)
        if rounding_error_lines:
            rounding_error_lines.unlink()
        if reward_lines:
            reward_lines.unlink()
        return order

    def action_confirm(self):
        orders_to_confirm = self.env['sale.order']
        for order in self:
            order.check_global_discount()
            can_confirm = order.check_shopify_amount_total()
            if can_confirm:
                orders_to_confirm += order
        res = super(SaleOrder, orders_to_confirm).action_confirm()
        for order in orders_to_confirm:
            if not order.user_id:
                continue
            if not order.user_id.login == 'syncspider':
                continue
            if "MH" not in order.name:
                continue
            if order.gateway == 'Bezahlung bei Abholung (Bar- oder Kartenzahlung)':
                continue
            if order.order_line.filtered(lambda f: f.is_downpayment):
                continue
            if order.auto_downpayment:
                order.auto_payment()
        return res

    def check_global_discount(self):
        for order in self:
            if order.shopify_global_discount_amount > 0.0:
                values = self.get_shopify_global_discount_values()
                if values:
                    if order.order_line.filtered(lambda f: f.product_id.id == values['product_id']):
                        order.order_line.filtered(lambda f: f.product_id.id == values['product_id']).write({
                            'price_unit': values['price_unit'],
                            'tax_id': values['tax_id'],
                        })
                    else:
                        order.write({'order_line': [(0, 0, values)]})

    def get_shopify_global_discount_values(self):
        reward_product = self.env['product.product'].search([('global_discount_product', '=', True)], limit=1)
        if not reward_product:
            return False
        sequence = max(self.order_line.filtered(lambda x: not x.is_reward_line).mapped('sequence'), default=10) + 1
        reward_line_values = {
            'name': self.shopify_global_discount_text or "Rabatt",
            'product_id': reward_product.id,
            'price_unit': -self.shopify_global_discount_amount,
            'product_uom_qty': 1.0,
            'product_uom': reward_product.uom_id.id,
            'sequence': sequence,
            'tax_id': [(6, 0, self.order_line.mapped('tax_id')[0].ids)] if self.order_line.mapped('tax_id') else [(6, 0, reward_product.taxes_id.ids)],
        }
        return reward_line_values

    def auto_payment(self):
        for order in self:
            amount = order.amount_received
            if not amount:
                amount = order.amount_total
            sapi = self.env['sale.advance.payment.inv'].with_context(active_ids=order.ids).create({
                'advance_payment_method': 'fixed',
                'fixed_amount': amount
            })
            sapi.sudo().create_invoices()
            if order.payment_ref:
                order.invoice_ids.write({'invoice_origin': order.payment_ref})
            if order.gateway_id.payment_term_id:
                order.payment_term_id = order.gateway_id.payment_term_id.id
            # disabled for review by customer
            order.invoice_ids.action_post()
            for invoice in order.invoice_ids:
                if not order.gateway_id.journal_id:
                    activity = self.env['mail.activity'].search([
                        ('activity_type_id', '=',
                         self.env.ref('syncspider_shopify.activity_assign_gateway').id),
                        ('res_id', '=', self.id),
                        ('res_model_id', '=', self.env['ir.model']._get('sale.order').id),
                    ])
                    if not activity:
                        self.env['mail.activity'].create({
                            'activity_type_id': self.env.ref('syncspider_shopify.activity_assign_gateway').id,
                            'user_id': self.user_id.id,
                            'summary': self.env.ref('syncspider_shopify.activity_assign_gateway').summary,
                            'res_id': self.id,
                            'res_model_id': self.env['ir.model']._get('sale.order').id,
                        })
                    continue
                if order.payment_status not in ["Paid", "Partially paid"]:
                    continue
                if (order.payment_status == "Partially paid") and not order.amount_received:
                    continue
                apr = self.env['account.payment.register'].with_context(active_model='account.move',
                                                                        active_ids=invoice.ids, no_payment_mail=True).create({
                    # 'communication': self.payment_ref,
                    'journal_id': order.gateway_id.journal_id.id,
                    'payment_date': order.original_date or order.date_order
                })
                apr.action_create_payments()
            #     template = self.env.ref(invoice._get_mail_template(), raise_if_not_found=False)
            #     if template:
            #         template.send_mail(invoice.id)

    def check_shopify_amount_total(self):
        """
        T13075 - check Odoo amount vs shopify amount, allow confirm either natively or with light adjustment, bigger adjustments need manual input
        :return:
        """
        self.ensure_one()
        if float_is_zero(self.shopify_amount_total, precision_digits=2):
            # no value given - continue as normal
            return True
        if float_compare(self.shopify_amount_total, self.amount_total, precision_digits=2) == 0.0:
            # no difference - continue as normal
            return True
        difference = round(self.shopify_amount_total - self.amount_total, 2)
        if abs(difference) > 0.05:  # abs cause it works in both directions
            # difference is too great - manual adjustment needed create acitivity
            activity = self.env['mail.activity'].search([
                ('activity_type_id', '=', self.env.ref('syncspider_shopify.activity_order_check_amount_total').id),
                ('res_id', '=', self.id),
                ('res_model_id', '=', self.env['ir.model']._get('sale.order').id),
            ])
            if not activity:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('syncspider_shopify.activity_order_check_amount_total').id,
                    'user_id': self.user_id.id,
                    'summary': self.env.ref('syncspider_shopify.activity_order_check_amount_total').summary,
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model']._get('sale.order').id,
                })
            return False
        else:
            # adjustment automated, create line
            product = self.env['product.product'].search([('rounding_line_product', '=', True)], limit=1)
            rounding_line = self.order_line.filtered(lambda f: f.product_id.id == product.id)
            if not rounding_line:
                if not product:
                    raise UserError(_('Kein Produkt für Rundungsdifferenzen gefunden.'))
                values = {
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'price_unit': difference,
                    'is_rounding_error_line': True
                }
                self.write({'order_line': [(0, 0, values)]})
                self.message_post(body="Zeile f. Rundungsdifferenz über %r &amp;euro; automatisch erstellt." % difference)
            else:
                rounding_line.write({'price_unit': difference})
                self.message_post(body="Zeile f. Rundungsdifferenz über %r &amp;euro; automatisch aktualisiert." % difference)
            # set line as last line so it wont show up somewhere in the middle
            self.order_line.filtered(lambda f: f.product_id.id == product.id).sequence = max(
                line.sequence for line in self.order_line) + 1
            return True
