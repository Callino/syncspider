# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json
import threading
import requests
from requests.exceptions import Timeout
from datetime import datetime, timedelta


class MoveLabelPackage(models.Model):
    _name = 'move.label.package'

    @api.onchange
    def onchange_move(self):
        if self.move_id:
            self.name = "Paket #%i" % len(self.move_id.move_package_ids)

    name = fields.Char(string="Name", default="Paket #")
    weight = fields.Float(string="Gewicht (kg)", required=True)
    move_id = fields.Many2one('account.move', string="Move")