# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    gateway_tag_ids = fields.Many2many('journal.gateway.tag', string="Shopify Gateways")
    default_shopify_journal = fields.Boolean(string="Default Shopify Journal")
