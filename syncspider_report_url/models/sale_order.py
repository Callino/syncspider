# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_invoices_json(self):
        inv_list = []
        for record in self:
            for invoice in record.invoice_ids:
                if not invoice.first_export_date:
                    invoice.first_export_date = datetime.now()
                inv_list.append({
                    'order_id': record.id,
                    'invoice_id': invoice.id,
                    'invoice_number': invoice.name,
                    'pdf_url': invoice.pdf_report_url,
                    'first_export_date': datetime.strftime(invoice.first_export_date, "%Y-%m%d %H:%M:%S"),
                })
        self.write({'invoices': json.dumps(inv_list)})

    invoices = fields.Text(string="Rechnungsinfo", compute="_get_invoices_json", store=False)
