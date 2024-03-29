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
            used_attribute_ids = []
            for json_att in json_template['attributes']:
                used_attribute_ids.append(json_att['attribute_id'])
                att_line = template.attribute_line_ids.filtered(lambda line: line.attribute_id.id == json_att['attribute_id'])
                if not att_line:
                    # Seems to be a new attribute - so create a new att_line for it
                    values = []
                    for value in json_att['values']:
                        if not value['active']:
                            continue
                        values.append((4, value['value_id']))
                    template.attribute_line_ids = [(0, 0, {
                        'attribute_id': json_att['attribute_id'],
                        'value_ids': values,
                    })]
                    continue
                for value in json_att['values']:
                    if value['active']:
                        t_value = att_line.value_ids.filtered(lambda v: v.id == value['value_id'])
                        if not t_value:
                            att_line.value_ids += self.env['product.attribute.value'].browse(value['value_id'])
                    else:
                        t_value = att_line.value_ids.filtered(lambda v: v.id == value['value_id'])
                        if t_value:
                            att_line.value_ids -= self.env['product.attribute.value'].browse(value['value_id'])
            for att_line in template.attribute_line_ids.filtered(lambda al: al.attribute_id.id not in used_attribute_ids):
                att_line.unlink()
        templates.create_variant_ids()
        return templates.get_template_json()
