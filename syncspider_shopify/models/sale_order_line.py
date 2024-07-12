# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_rounding_error_line = fields.Boolean(string="Rundungskorrekturzeile")
