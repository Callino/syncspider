# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json
import threading
import requests
from requests.exceptions import Timeout
from datetime import datetime, timedelta


class SyncHook(models.Model):
    _name = 'sync.hook'
    _description = 'Sync Hook'
    _order = 'sequence ASC'

    @api.depends('record_ref')
    def _compute_name(self):
        for record in self:
            record.name = record.record_ref
            
    name = fields.Char('Name', compute='_compute_name', store=True)
    sequence = fields.Integer('Sequence', default=0)
    record_ref = fields.Char(string="Record Referenz", required=True)
    model = fields.Char(string="Model", required=False, index=True)
    record_id = fields.Integer('Record ID', index=True, default=None)
    on_create = fields.Boolean('Trigger on create', default=False)
    on_delete = fields.Boolean('Trigger on delete', default=True)
    on_update = fields.Boolean('Trigger on update', default=True)
    webhook_url = fields.Char('Webhook', required=True)
    event_ids = fields.One2many('sync.event', 'hook_id', string='Events')

    @api.model
    def _update_vals(self, vals):
        if 'record_ref' in vals:
            if ',' in vals['record_ref']:
                (modelname, record_id) = vals['record_ref'].split(",")
            else:
                modelname = vals['record_ref']
                record_id = None
            try:
                vals['record_id'] = int(record_id)
            except:
                pass
            vals['model'] = modelname

    @api.model
    def create(self, vals):
        self._update_vals(vals)
        return super(SyncHook, self).create(vals)

    @api.multi
    def write(self, vals):
        self._update_vals(vals)
        return super(SyncHook, self).write(vals)

    @api.multi
    def create_event(self, operation, record):
        self.ensure_one()
        # Create write event
        event = self.env['sync.event'].create({
            'name': "%s on %s" % (operation.title(), self.name),
            'hook_id': self.id,
            'payload': json.dumps({
                'event': operation,
                'model': self.model,
                'record_id': record.id
            }),
        })
        event.run_async()

class SyncEvent(models.Model):
    _name = 'sync.event'
    _description = 'Sync Event'

    name = fields.Char('Name')
    hook_id = fields.Many2one('sync.hook', string="Sync Hook", required=True, ondelete='cascade')
    done = fields.Boolean('Done', default=False)
    failed = fields.Boolean('Failed', default=False)
    trycount = fields.Integer('Try count', default=0)
    nexttry = fields.Datetime('Nexttry')
    payload = fields.Text('Payload')
    done_timestamp = fields.Datetime('Timestamp')
    last_http_code = fields.Char('HTTP Code')
    last_http_response = fields.Text('HTTP Response')

    def _do_http_request(self, events):
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = events.pool.cursor()
            events = events.with_env(events.env(cr=new_cr))
            for event in events:
                try:
                    response = requests.post(event.hook_id.webhook_url, json=json.loads(event.payload), timeout=(2, 10))
                    if response.status_code != 200:
                        event.write({
                            'trycount': event.trycount + 1,
                            'nexttry': datetime.now() + timedelta(minutes=5*(event.trycount+1)),
                            'last_http_response': response.text,
                            'last_http_code': response.status_code,
                            'failed': True,
                            'done': False,
                        })
                    else:
                        event.write({
                            'nexttry': None,
                            'last_http_response': response.text,
                            'last_http_code': response.status_code,
                            'failed': False,
                            'done': True,
                        })
                except Timeout:
                    event.write({
                        'trycount': event.trycount + 1,
                        'nexttry': datetime.now() + timedelta(minutes=5 * (event.trycount + 1)),
                        'last_http_response': 'Timeout',
                        'failed': True,
                        'done': False,
                    })
                except Exception as e:
                    event.write({
                        'nexttry': datetime.now() + timedelta(minutes=5 * (event.trycount + 1)),
                        'trycount': event.trycount + 1,
                        'last_http_response': str(e),
                        'failed': True,
                        'done': False,
                    })

            new_cr.commit()
            new_cr.close()
            return {}

    @api.multi
    def run_async(self):
        # We do start a new environment in a new thread - and try the http request in this thread
        http_request = threading.Timer(interval=5, function=self._do_http_request, kwargs={'events': self})
        http_request.start()

    @api.model
    def cron_run_events(self):
        events = self.search([
            ('nexttry', '<', datetime.now()),
            ('trycount', '<', 5),
        ])
        if events:
            events.run_async()
