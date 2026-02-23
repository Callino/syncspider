# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)


class ShopifyGateway(models.Model):
    _name = 'shopify.gateway'
    _description = 'Shopify Gateway'

    name = fields.Char(string='Gateway')
    journal_id = fields.Many2one('account.journal', string='Journal')
    set_pickings_as_paid_authorized = fields.Boolean(string="Lieferscheine als Bezahlt markieren", default=False)
    payment_term_id = fields.Many2one('account.payment.term', string='Zahlungsbedingung')
