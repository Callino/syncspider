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
    company_id = fields.Many2one(
        'res.company',
        string='Unternehmen',
        default=lambda self: self.env.company,
        help='Das Unternehmen, zu dem dieses Gateway gehört. '
             'Journal und Zahlungsbedingung müssen zur selben Company gehören. '
             'Pro Company-Shop ein eigenes Gateway anlegen.',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('company_id', '=', company_id)]",
    )
    set_pickings_as_paid_authorized = fields.Boolean(string="Lieferscheine als Bezahlt markieren", default=False)
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Zahlungsbedingung',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    use_payment_ref = fields.Boolean(string="Zahlungsreferenz verwenden", default=False)