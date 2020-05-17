# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class KsWooRecordMapping(models.TransientModel):
    _name = 'ks.woo.record.mapping'
    _description = 'WooCommerce Record Mapping'

    ks_record_id = fields.Integer(readonly=True, string='Record Id')
    ks_woo_id = fields.Integer(string='Woo Id', default=0)
    ks_name = fields.Char(readonly=True, string='Name')
    ks_woo_instance = fields.Many2one('ks.woocommerce.instances', string='Woo Instance')


class KsWooModelMapping(models.TransientModel):
    _name = 'ks.woo.model.mapping'
    _description = 'WooCommerce Model Mapping'

    ks_model = fields.Many2one('ir.model', string="Model Name",
                               domain="[('model', 'in', ['product.product', 'product.template','product.category'])]")
    ks_model_name = fields.Char('Model Name', related='ks_model.model', readonly=True, store=True)
    ks_woo_instance = fields.Many2one('ks.woocommerce.instances', string='WooCommerce Instance')
    ks_binary = fields.Binary()
    ks_all_records = fields.Many2many('ks.woo.record.mapping')
    ks_temp_text = fields.Char(default='**Select the model to map the records', readonly=True)

    @api.onchange('ks_model', 'ks_woo_instance')
    def _onchange_ks_model(self):
        if self.ks_model_name:
            woo_id = 'ks_woo_id' if self.ks_model_name != 'product.product' else 'ks_woo_variant_id'
            domain = ['|', (woo_id, '=', 0), (woo_id, '=', False)]
            if self.ks_model_name == 'product.product':
                domain.append(('product_template_attribute_value_ids', '!=', False))
            if self.ks_woo_instance:
                domain.append(('ks_woo_instance_id', '=', self.ks_woo_instance.id))
            all_records = self.env[self.ks_model_name].search(domain)
            record_list = []
            if all_records:
                for each_rec in all_records:
                    record_list.append({
                        'ks_record_id': each_rec.id,
                        'ks_name': each_rec.name,
                        'ks_woo_id': each_rec.ks_woo_id if self.ks_model_name != 'product.product' else each_rec.ks_woo_variant_id,
                        'ks_woo_instance': each_rec.ks_woo_instance_id.id
                    })
                records = self.env['ks.woo.record.mapping'].create(record_list)
                ids = records.mapped('id')
                self.ks_all_records = [(6, 0, ids)]

    def ks_execute_all_records(self):
        if self.ks_model:
            try:
                editable_records = self.ks_all_records.filtered(lambda l: l.ks_woo_id and l.ks_woo_instance)
                if editable_records:
                    for each_rec in editable_records:
                        existing_record = self.env[self.ks_model_name].browse(each_rec.ks_record_id)
                        update_dict = {
                            'ks_woo_instance_id': each_rec.ks_woo_instance.id
                        }
                        if self.ks_model_name != 'product.product':
                            update_dict.update({
                                'ks_woo_id': each_rec.ks_woo_id
                            })
                        else:
                            update_dict.update({
                                'ks_woo_variant_id': each_rec.ks_woo_id
                            })
                        existing_record.write(update_dict)
            except Exception as e:
                _logger.error("Record Mapping Failed due to %s" % e)
        else:
            raise ValidationError('Please select the Model to map the existing records!!')
