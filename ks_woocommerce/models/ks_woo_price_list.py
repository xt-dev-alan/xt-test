# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class KsProductPricelistInherit(models.Model):
    _inherit = 'product.pricelist'

    ks_instance_id = fields.Many2one('ks.woocommerce.instances', string='WooCommerce Instance ID',
                                     help="""WooCommerce Instance: The Instance which will used this price list to update the price""")


class KsProductPricelistItemInherit(models.Model):
    _inherit = 'product.pricelist.item'

    ks_on_sale_price = fields.Boolean('WooCommerce OnSale Price',
                                      help="""OnSale Price: Enable if you want to update Sale Price of WooCommerce Product \n
                                                            Disable if you want to update Regular Price of WooCommerce Product""")
    ks_instance_id = fields.Many2one('ks.woocommerce.instances', related='pricelist_id.ks_instance_id',
                                     string='WooCommerce Instance',
                                     help="""WooCommerce Instance: The Instance which will used this price list to update the price""",
                                     readonly=1)
