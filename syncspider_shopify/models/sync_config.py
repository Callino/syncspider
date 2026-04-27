# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SyncConfig(models.Model):
    _name = 'sync.config'
    _description = 'Sync Configuration'

    name = fields.Char(string="Name", required=True)
    order_prefix = fields.Char(
        string="Auftragspräfix",
        required=True,
        help="Präfix für Aufträge (z.B. 'MH', 'SD')",
    )
    send_webhook = fields.Boolean(
        string="Webhook senden",
        default=True,
        help="Webhook bei Versand/BOM-Fertigstellung senden",
    )
    webhook_url = fields.Char(
        string="Webhook URL (Fulfillment)",
        help="URL für Versand-Webhook Benachrichtigungen",
    )
    webhook_url_bom = fields.Char(
        string="Webhook URL (BOM)",
        help="URL für BOM-Fertigstellungs-Webhook Benachrichtigungen",
    )
    auto_payment = fields.Boolean(
        string="Automatische Zahlung",
        default=False,
        help="Zahlungen automatisch erstellen. Ursprünglich: 'MH' in order.name",
    )
    allow_autoconfirm = fields.Boolean(
        string="Autoconfirm erlauben",
        default=False,
        help="Automatische Bestätigung von Aufträgen erlauben. Ursprünglich: 'MH' in self.name",
    )
    skip_vat_check = fields.Boolean(
        string="UID-Prüfung überspringen",
        default=False,
        help="UID-Pflichtprüfung bei Rechnungserstellung überspringen. Ursprünglich: 'MH' in order.name",
    )
    use_market_brand_fiscal_position = fields.Boolean(
        string="Marken-Fiskalposition verwenden",
        default=False,
        help="Fiskalposition aus Market Brand bei Änderung setzen. Ursprünglich: 'SD' in self.name",
    )
    auto_send_down_payment_invoice = fields.Boolean(
        string="Anzahlungsrechnung automatisch versenden",
        default=False,
        help="Beim Bestätigen einer Anzahlungsrechnung wird diese automatisch per Mail an den Kunden versendet.",
    )
    auto_send_remaining_invoice = fields.Boolean(
        string="Schlussrechnung mit Restbetrag automatisch versenden",
        default=False,
        help="Sobald eine Anzahlungsrechnung bezahlt ist, wird die Schlussrechnung auch dann automatisch gepostet und versendet, wenn noch ein Restbetrag offen ist (sonst nur bei 100% Anzahlung).",
    )
    invoice_mail_template_id = fields.Many2one(
        'mail.template',
        string="Rechnungs-Mailvorlage",
        domain="[('model', '=', 'account.move')]",
        help="Optional: Mailvorlage, die beim automatischen Versand von Rechnungen verwendet wird. Wenn leer, wird das Standard-Rechnungstemplate (account.email_template_edi_invoice) verwendet.",
    )
    active = fields.Boolean(string="Aktiv", default=True)

    _sql_constraints = [
        ('prefix_uniq', 'unique(order_prefix)', 'Jedes Präfix darf nur einmal konfiguriert werden!')
    ]

    @api.model
    def get_config_for_order(self, order_name):
        """Get the sync config matching the order name prefix.
        Returns the config record or False if no match.
        """
        if not order_name:
            return False
        configs = self.search([('active', '=', True)])
        for config in configs:
            if config.order_prefix and config.order_prefix in order_name:
                return config
        return False

    @api.model
    def get_webhook_url(self, order_name):
        """Get the fulfillment webhook URL for an order.
        Returns False if no config exists or no URL configured.
        """
        config = self.get_config_for_order(order_name)
        if config and config.webhook_url:
            return config.webhook_url
        return False

    @api.model
    def get_webhook_url_bom(self, order_name):
        """Get the BOM webhook URL for an order.
        Returns False if no config exists or no URL configured.
        """
        config = self.get_config_for_order(order_name)
        if config and config.webhook_url_bom:
            return config.webhook_url_bom
        return False