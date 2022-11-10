from odoo import models
import logging

_logger = logging.getLogger(__name__)


def _check_syncspider(self, operation):
    # Check if one of the models does have a syncspider hook
    try:
        if self._name in ['sync.hook', 'sync.event']:
            return
        if 'sync.hook' not in self.env:
            return
        for record in self:
            if operation == "write":
                hook = self.env['sync.hook'].sudo().search([
                    ('model', '=', self._name),
                    ('on_update', '=', True),
                    '|',
                    '|',
                    ('record_id', '=', record.id),
                    ('record_id', '=', 0),
                    ('record_id', '=', None),
                ], limit=1)
            elif operation == "unlink":
                hook = self.env['sync.hook'].sudo().search([
                    ('model', '=', self._name),
                    ('on_delete', '=', True),
                    '|',
                    '|',
                    ('record_id', '=', record.id),
                    ('record_id', '=', 0),
                    ('record_id', '=', None),
                ], limit=1)
            elif operation == "create":
                hook = self.env['sync.hook'].sudo().search([
                    ('model', '=', self._name),
                    ('on_create', '=', True),
                    '|',
                    ('record_id', '=', None),
                    ('record_id', '=', 0),
                ], limit=1)
            if hook:
                hook.create_event(operation, record)
    except Exception as e:
        _logger.error("Exception on write to find syncspider hook: %s", e)
        return


