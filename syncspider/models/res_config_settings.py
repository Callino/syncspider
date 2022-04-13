# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_asin = fields.Boolean("ASIN für Produkte Aktivieren", implied_group='syncspider.group_asin')
    group_distribution_channels = fields.Boolean("Vertriebskanäle für Produkte Aktivieren", implied_group='syncspider.group_distribution_channels')
