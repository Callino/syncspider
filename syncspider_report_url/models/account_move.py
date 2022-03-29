# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('id')
    def _get_pdf_report_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.token_url = base_url + "/report/pdf/account.report_invoice/" + record.id

    pdf_report_url = fields.Char(string="PDF Report URL", compute="_get_pdf_report_url", store=True)
