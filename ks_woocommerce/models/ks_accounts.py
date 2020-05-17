# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class KsAccountTaxInherit(models.Model):
    _inherit = 'account.tax'

    ks_woo_id = fields.Integer('Woo Id',
                               readonly=True, default=0,
                               help="""Woo Id: Unique WooCommerce resource id for the tax on the specified 
                                       WooCommerce Instance""")
    ks_woo_instance_id = fields.Many2one('ks.woocommerce.instances',
                                         string='Woo Instance',
                                         help="""WooCommerce Instance: Ths instance of woocomerce to which this 
                                                 tax belongs to.""")
    ks_export_in_wo = fields.Boolean('Exported in Woo',
                                     readonly=True,
                                     store=True,
                                     compute='_ks_compute_export_in_woo',
                                     help="""Exported in Woo: If enabled, the Woo Tax is synced with the specified 
                                        WooCommerce Instance""")

    @api.depends('ks_woo_id')
    def _ks_compute_export_in_woo(self):
        """
        This will make enable the Exported in Woo if record has the WooCommerce Id

        :return: None
        """
        for rec in self:
            rec.ks_export_in_wo = bool(rec.ks_woo_id)


class KsAccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    ks_woo_payment_id = fields.Many2one('ks.woo.payment.gateway', 'Woo Payment Gateway',
                                        help="""Woo Payment Gateway: The WooCommerce payment gateway through which the 
                                        payment has been completed for the Woo Orders"""
                                        )
    ks_woo_sale_order_id = fields.Many2one('sale.order', string='Woo Order',
                                           help="""Woo Order: The WooCommerce Order""", readonly=1)
    ks_woo_instance_id = fields.Many2one('ks.woocommerce.instances', track_visibility='onchange',
                                         string='Woo Instance',
                                         help="""WooCommerce Instance: Ths instance of woocomerce to which this 
                                                 product variant belongs to.""")

    def post(self):
        super(KsAccountPaymentInherit, self).post()
        instance_id = self.env['sale.order'].search([('id', '=', self.ks_woo_sale_order_id.id)]).ks_woo_instance_id.id
        if self.env['ks.woocommerce.instances'].search([('id','=',instance_id)]).ks_woo_auto_order_status:
            self.env['sale.order'].search([('id', '=', self.ks_woo_sale_order_id.id)]).ks_woo_status = self.env['ks.woocommerce.instances'].search([('id','=',instance_id)]).ks_woo_order_invoice_selection

    @api.model
    def default_get(self, fields):
        """
        This will add the woo payment gateway and sale order for manual payment into the account payment
        """
        rec = super(KsAccountPaymentInherit, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            if invoice['ks_woo_order_id']:
                ks_woo_sale_order_id = invoice['ks_woo_order_id'][0]
                woo_order = self.env['sale.order'].search([('id', '=', ks_woo_sale_order_id)], limit=1)
                if woo_order:
                    rec['ks_woo_sale_order_id'] = woo_order.id
                    rec['ks_woo_payment_id'] = woo_order.ks_woo_payment_gateway.id
        return rec

    @api.onchange("ks_woo_payment_id")
    def _ks_assign_woo_payment_journal(self):
        """
        This will change the journal id according to payment gateway of Woo
        """
        if self.ks_woo_payment_id:
            if self.ks_woo_payment_id.ks_journal_id:
                self.journal_id = self.ks_woo_payment_id.ks_journal_id
            else:
                if self.ks_woo_sale_order_id:
                    if self.ks_woo_sale_order_id.ks_woo_instance_id.ks_journal_id:
                        self.journal_id = self.ks_woo_sale_order_id.ks_woo_instance_id.ks_journal_id


class KsAccountInvoiceInherit(models.Model):
    _inherit = 'account.move'

    ks_woo_order_id = fields.Many2one('sale.order', string='Woo Order', help="""Woo Order: The WooCommerce Order""",
                                      readonly=1)


class KsStockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(KsStockPickingInherit, self).button_validate()
        ks_instance_id = self.env['ks.woocommerce.instances'].search([('id', '=', self.sale_id.ks_woo_instance_id.id)])
        if ks_instance_id.ks_woo_auto_order_status:
            self.env['sale.order'].search([('id', '=', self.sale_id.id)]).ks_woo_status = ks_instance_id.ks_woo_order_shipment_selection