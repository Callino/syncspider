# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import uuid
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_report_ident(self):
        for record in self:
            record.report_ident = uuid.uuid4()

    def _get_pdf_report_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.pdf_report_url = base_url + "/pdf/dl/%s/%s/%s/%i" % (record.report_ident, record._name, 'account.report_invoice', record.id)

    pdf_report_url = fields.Char(string="PDF Report URL", compute="_get_pdf_report_url", store=True)
    report_ident = fields.Char(string="Report Download Ident", compute="_get_report_ident", store=True)

    def read(self, fields=None, load="_classic_read"):
        for record in self:
            if not record.pdf_report_url:
                record._get_report_ident()
                record._get_pdf_report_url()
        return super(AccountMove, self).read(fields=fields, load=load)
