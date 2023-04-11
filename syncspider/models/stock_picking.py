# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    already_done = fields.Boolean(string="Bereits erledigt", default=False, copy=False)
    detailed_state = fields.Selection([
        ('draft', 'Entwurf'),
        ('waiting', 'Wartet auf anderen Vorgang'),
        ('confirmed', 'Warteliste'),
        ('partially_available', 'Teilweise Verfügbar'),
        ('assigned', 'Bereit'),
        ('done', 'Erledigt'),
        ('cancel', 'Abgebrochen'),
    ], string='Status Syncspider', compute='_compute_detailed_state',
        copy=False, index=True, readonly=True, store=True, tracking=True)

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if vals.get('state', '') == 'done':
            self.write({'already_done': True})
        if vals.get('date_done', False):
            self.write({'already_done': True})
        self._compute_detailed_state()
        return res

    @api.depends('move_type', 'immediate_transfer', 'move_line_ids', 'move_lines.state', 'move_lines.picking_id', 'already_done')
    def _compute_detailed_state(self):
        picking_moves_state_map = defaultdict(dict)
        picking_move_lines = defaultdict(set)
        for move in self.env['stock.move'].search([('picking_id', 'in', self.ids)]):
            picking_id = move.picking_id
            move_state = move.state
            picking_moves_state_map[picking_id.id].update({
                'any_draft': picking_moves_state_map[picking_id.id].get('any_draft', False) or move_state == 'draft',
                'all_cancel': picking_moves_state_map[picking_id.id].get('all_cancel', True) and move_state == 'cancel',
                'all_cancel_done': picking_moves_state_map[picking_id.id].get('all_cancel_done',
                                                                              True) and move_state in (
                                   'cancel', 'done'),
                'all_done_are_scrapped': picking_moves_state_map[picking_id.id].get('all_done_are_scrapped', True) and (
                    move.scrapped if move_state == 'done' else True),
                'any_cancel_and_not_scrapped': picking_moves_state_map[picking_id.id].get('any_cancel_and_not_scrapped',
                                                                                          False) or (
                                                           move_state == 'cancel' and not move.scrapped),
            })
            picking_move_lines[picking_id.id].add(move.id)
        for picking in self:
            picking_id = (picking.ids and picking.ids[0]) or picking.id
            if picking.already_done:
                picking.detailed_state = 'done'
                continue
            if not picking_moves_state_map[picking_id]:
                picking.detailed_state = 'draft'
            elif picking_moves_state_map[picking_id]['any_draft']:
                picking.detailed_state = 'draft'
            elif picking_moves_state_map[picking_id]['all_cancel']:
                picking.detailed_state = 'cancel'
            elif picking_moves_state_map[picking_id]['all_cancel_done']:
                if picking_moves_state_map[picking_id]['all_done_are_scrapped'] and picking_moves_state_map[picking_id]['any_cancel_and_not_scrapped']:
                    picking.detailed_state = 'cancel'
                else:
                    picking.detailed_state = 'done'
            else:
                relevant_move_state = self.env['stock.move'].browse(picking_move_lines[picking_id])._get_relevant_state_among_moves()
                picking.detailed_state = relevant_move_state

    def set_qty_and_mark_done(self):
        for picking in self:
            if picking.state == 'confirmed':
                picking.action_assign()
            for line in picking.move_ids_without_package:
                try:
                    line.write({'quantity_done': line.product_uom_qty, 'state': 'assigned'})
                except Exception as e:
                    for ml in picking.move_line_ids_without_package:
                        ml.write({'qty_done': ml.product_uom_qty, 'state': 'assigned'})
                    # _logger.exception("Cannot write line qty at this point.")
            picking.button_validate()
        return True