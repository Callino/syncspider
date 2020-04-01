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


orig_write = models.Model.write

def model_write(self, vals):
    _check_syncspider(self, "write")
    return orig_write(self, vals)

models.Model.write = model_write


orig_unlink = models.Model.unlink

def model_unlink(self):
    _check_syncspider(self, "unlink")
    return orig_unlink(self)

models.Model.unlink = model_unlink


orig_create = models.Model._create

def model_create(self, data_list=None):
    record = orig_create(self, data_list)
    _check_syncspider(record, "create")
    return record

models.Model._create = model_create
