# -*- coding: utf-8 -*-
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class DistributionChannelTag(models.Model):
    _name = 'distribution.channel.tag'
    _order = 'sequence'

    sequence = fields.Integer(name="Sequenz")
    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')
