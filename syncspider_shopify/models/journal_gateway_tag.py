# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class JournalGatewayTag(models.Model):
    _name = 'journal.gateway.tag'

    name = fields.Char(string="Name")
    gateway = fields.Char(string="Gateway")
