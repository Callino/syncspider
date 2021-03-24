from odoo import api, fields, models
import json
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_template_json(self):
        jsondata = []
        for template in self:
            attributes = []
            for att_line in template.attribute_line_ids:
                attribute_values = []
                for value in att_line.attribute_id.value_ids:
                    attribute_values.append({
                        'value_id': value.id,
                        'value': value.name,
                        'active': value in att_line.value_ids,
                    })
                attributes.append({
                    'attribute_id': att_line.attribute_id.id,
                    'name': att_line.attribute_id.name,
                    'values': attribute_values,
                })
            jsondata.append({
                'product_tmpl_id': template.id,
                'default_code': template.default_code,
                'name': template.name,
                'attributes': attributes,
            })
        return json.dumps(jsondata)

    @api.model
    def set_template_json(self, jsonstring):
        jsondata = json.loads(jsonstring)
        templates = self.env['product.template']
        for json_template in jsondata:
            template = self.browse(json_template['product_tmpl_id'])
            templates += template
            for json_att in json_template['attributes']:
                _logger.info("Got Attributes: %s", json_att)
                att_line = template.attribute_line_ids.filtered(lambda line: line.attribute_id.id == json_att['attribute_id'])
                if not att_line:
                    # Seems to be a new attribute - so create a new att_line for it
                    pass
                else:
                    for value in json_att['values']:
                        if value['active']:
                            t_value = att_line.value_ids.filtered(lambda v: v.id == value['value_id'])
                            if not t_value:
                                att_line.value_ids += self.env['product.attribute.value'].browse(value['value_id'])
                        else:
                            t_value = att_line.value_ids.filtered(lambda v: v.id == value['value_id'])
                            if t_value:
                                att_line.value_ids -= self.env['product.attribute.value'].browse(value['value_id'])
        return templates.get_template_json()
