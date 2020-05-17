# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class KsWooProductVariant(models.Model):
    _inherit = 'product.product'

    ks_woo_variant_id = fields.Integer('Woo Variant Id', track_visibility='onchange', default=0,
                                       readonly=True,
                                       help="""Woo Id: Unique WooCommerce resource id for the product variant on the 
                                       specified WooCommerce Instance""")
    ks_date_variant_created = fields.Datetime('Variant Created On',
                                              readonly=True,
                                              help="Created On: Date on which the WooCommerce Product has been created")
    ks_date_variant_updated = fields.Datetime('Variant Updated On',
                                              readonly=True,
                                              help="Updated On: Date on which the WooCommerce Product has been last "
                                                   "updated")
    ks_woo_variant_description = fields.Html(string='Description',
                                             help="""Description: An optional description for 
                                                                           this wooCommerce product variant""")
    ks_variant_exported_in_woo = fields.Boolean('Variant Exported in Woo',
                                                readonly=True,
                                                store=True,
                                                compute='_ks_compute_export_in_woo',
                                                help="""Exported in Woo: If enabled, the product is synced with the specified 
                                                WooCommerce Instance""")
    ks_woo_variant_reg_price = fields.Float('Woo Regular Price', readonly=True)
    ks_woo_variant_sale_price = fields.Float('Woo Sale price', readonly=True)
    ks_length = fields.Float()
    ks_width = fields.Float()
    ks_height = fields.Float()

    @api.depends('ks_woo_variant_id')
    def _ks_compute_export_in_woo(self):
        """
        This will make enable the Exported in Woo if record has the WooCommerce Id

        :return: None
        """
        for rec in self:
            rec.ks_variant_exported_in_woo = bool(rec.ks_woo_variant_id)

    @api.onchange('ks_length', 'ks_width', 'ks_height')
    def ks_onchange_l_b_h(self):
        """
        This will calculate the value for Volume with respective of ks_length, ks_width and ks_height

        :return: None
        """
        self.volume = float(self.ks_length if self.ks_length else 0) * float(
            self.ks_width if self.ks_width else 0) * float(
            self.ks_height if self.ks_height else 0)

    def ks_prepare_product_variant_data(self, json_data):
        data = {
            "active": True,
            "default_code": json_data.get('sku') or '',
            "weight": json_data.get('weight') or '',
            "ks_length": json_data.get('dimensions').get('length') or '',
            "ks_height": json_data.get('dimensions').get('height') or '',
            "ks_width": json_data.get('dimensions').get('width') or '',
            "volume": float(json_data.get('dimensions').get('length') or 0.0) * float(
                json_data.get('dimensions').get('height') or 0.0) * float(
                json_data.get('dimensions').get('width') or 0.0),
            "image_variant_1920": self.env['product.template'].ks_image_read_from_url(json_data.get('image')),
            "ks_woo_variant_id": json_data.get('id') or '',
            "ks_date_variant_created": datetime.strptime((json_data.get('date_created')).replace('T', ' '),
                                                         DEFAULT_SERVER_DATETIME_FORMAT) if json_data.get(
                'date_created') else False,
            "ks_date_variant_updated": datetime.strptime((json_data.get('date_modified')).replace('T', ' '),
                                                         DEFAULT_SERVER_DATETIME_FORMAT) if json_data.get(
                'date_created') else False,
            "ks_woo_variant_description": json_data.get('description') or '',
        }
        return data

    def ks_update_price_on_product_variant(self, json_data):
        self.ks_woo_variant_reg_price = float(json_data.get('regular_price') or 0.0)
        self.ks_woo_variant_sale_price = float(json_data.get('sale_price') or 0.0)
        # if self.ks_woo_instance_id.ks_woo_pricelist:
        #     self.env['product.template'].ks_update_price_on_price_list(json_data,
        #                                                                self.ks_woo_instance_id.ks_woo_pricelist, self)
        if not self.ks_woo_instance_id.ks_multi_currency_option:
            if self.ks_woo_instance_id.ks_woo_pricelist:
                self.env['product.template'].ks_update_price_on_price_list(json_data,
                                                                           self.ks_woo_instance_id.ks_woo_pricelist,
                                                                           self)
        else:
            ks_data = self.env['product.pricelist'].search(
                [('currency_id', '=',
                  self.ks_woo_instance_id.ks_woo_currency.id),
                 ('ks_instance_id', '=', self.ks_woo_instance_id.id)])
            self.env['product.template'].ks_update_price_on_price_list(json_data, ks_data,
                                                                       self)
