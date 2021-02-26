# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fullfillment_status = fields.Selection(selection=[
        ('waiting', _('warten auf Abholung')),
        ('picked_up', _('abgeholt')),
        ('sent', _('versendet')),
        ('retourned', _('retourniert'))], string="Fullfillment Status")
