# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)


class ShopifyGateway(models.Model):
    _name = 'shopify.gateway'

    name = fields.Char(string='Gateway')
    journal_id = fields.Many2one('account.journal', string='Journal')
