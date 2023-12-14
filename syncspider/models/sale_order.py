# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def create_invoices(self):
        return self._create_invoices().ids
