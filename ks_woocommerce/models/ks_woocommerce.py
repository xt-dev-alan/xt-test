# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from requests.exceptions import ConnectionError
from woocommerce import API as WCAPI


class KsWooCommerceInstance(models.Model):
    _name = 'ks.woocommerce.instances'
    _description = 'WooCommerce Instances Details'
    _rec_name = 'ks_name'

    ks_name = fields.Char('Woo Instance Name', required=True)
    ks_woo_store_url = fields.Char('WooCommerce Store URL', required=True)
    ks_customer_key = fields.Char('Customer Key', required=True)
    ks_customer_secret = fields.Char('Customer Secret', required=True)
    ks_verify_ssl = fields.Boolean('Verify SSL')
    ks_wc_version = fields.Selection([('wc/v3', '3.5.x or later'), ('wc/v2', '3.0.x or later'),
                                      ('wc/v1', '2.6.x or later')],
                                     string='WooCommerce Version', default='wc/v3', readonly=True,
                                     required=True)
    color = fields.Integer(default=10)
    ks_stock_field_type = fields.Many2one('ir.model.fields', 'Stock Field Type',
                                          domain="[('model_id', '=', 'product.product'),"
                                                 "('name', 'in', ['qty_available','virtual_available'])]")
    ks_instance_state = fields.Selection([('draft', 'Draft'), ('connected', 'Connected'), ('active', 'Active'),
                                          ('deactivate', 'Deactivate')], string="Woo Instance State", default="draft")
    ks_instance_connected = fields.Boolean(default=False)
    ks_company = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, readonly=1)
    ks_warehouse = fields.Many2one('stock.warehouse', 'Warehouse', domain="[('company_id', '=', ks_company)]")
    ks_woo_currency = fields.Many2one('res.currency', 'Currency')
    ks_multi_currency_option = fields.Boolean(string='Multi-Currency Option', default=False)
    ks_woo_multi_currency = fields.Many2many(comodel_name='res.currency', string='Multi-Currency')
    ks_import_order_state_config = fields.One2many('ks.woocommerce.status', 'ks_instance_id')
    ks_sales_team = fields.Many2one('crm.team', string="Sales Team")
    ks_sales_person = fields.Many2one('res.users', string="Sales Person")
    ks_use_custom_order_prefix = fields.Boolean(string='Use Custom Order Prefix')
    ks_order_prefix = fields.Char(string="Order Prefix")
    ks_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    ks_journal_id = fields.Many2one('account.journal', string='Payment Method',
                                    domain=[('type', 'in', ('bank', 'cash'))])
    ks_woo_count_orders = fields.Integer('Order Count', compute='_compute_count_of_woo_records')
    ks_woo_count_products = fields.Integer('Product Count', compute='_compute_count_of_woo_records')
    ks_woo_count_coupons = fields.Integer('Coupon Count', compute='_compute_count_of_woo_records')
    ks_woo_count_customers = fields.Integer('Customer Count', compute='_compute_count_of_woo_records')
    ks_woo_fees = fields.Many2one('product.product', 'Woo Fees')
    ks_woo_shipping = fields.Many2one('product.product', 'Woo Shipping')
    ks_auto_update_stock = fields.Boolean('Auto Update Product Stock?')
    ks_aus_cron_id = fields.Many2one('ir.cron', readonly=1)
    ks_aus_cron_last_updated = fields.Datetime('Last Updated [Product Stock]', readonly=True)
    ks_auto_update_order_status = fields.Boolean('Auto Update Order Status?')
    ks_auos_cron_id = fields.Many2one('ir.cron', readonly=1)
    ks_auos_cron_last_updated = fields.Datetime('Last Updated [Order Status]', readonly=True)
    ks_auto_import_order = fields.Boolean('Auto Import Order?')
    ks_aio_cron_id = fields.Many2one('ir.cron', readonly=1)
    ks_aio_cron_last_updated = fields.Datetime('Last Updated [Sale Order]', readonly=True)
    ks_auto_import_product = fields.Boolean('Auto Import Product?')
    ks_aip_cron_id = fields.Many2one('ir.cron', readonly=1)
    ks_aip_cron_last_updated = fields.Datetime('Last Updated [Product]', readonly=True)
    ks_woo_customer = fields.Many2one('res.partner', 'Woo Customer')
    ks_base_url = fields.Char(default=lambda self: self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
    ks_woo_pricelist = fields.Many2one('product.pricelist', string='Pricelist')
    ks_woo_auto_order_status = fields.Boolean('Auto Order Status Update')
    ks_woo_order_status_invoice = fields.Char(default='Invoice', readonly=True, string='Invoice Stage')
    ks_woo_order_status_shipment = fields.Char(default='Shipment', readonly=True, string='Shipment Stage')
    ks_options = fields.Char()
    ks_woo_order_invoice_selection = fields.Selection([('pending', 'Pending'), ('on-hold', 'On-Hold'),
                                                       ('processing', 'Processing'), ('completed', 'Completed')],
                                                      string='Invoice State')
    ks_woo_order_shipment_selection = fields.Selection([('pending', 'Pending'), ('on-hold', 'On-Hold'),
                                                        ('processing', 'Processing'), ('completed', 'Completed')],
                                                       string='Shipment State')

    # @api.onchange('ks_woo_order_invoice_selection')
    # def auto_order(self):
    #     ls_ks_options = ['pending','on-hold','processing','completed']
    #     if self.ks_woo_auto_order_status and len(self.ks_woo_order_invoice_selection) > 0:
    #         return {
    #             'domain': {
    #                 'ks_woo_currency': [('id', 'not in', ls_ks_options)]
    #             }
    #         }
    #     return {
    #         'domain': {
    #             'ks_woo_currency': [('id', 'in', [])]
    #         }
    #     }
    ks_woo_pricelist_ids = fields.Many2many('product.pricelist', string='Multi-Pricelist')

    @api.onchange('ks_woo_multi_currency', 'ks_multi_currency_option')
    def pricelist(self):
        if self.ks_multi_currency_option and len(self.ks_woo_multi_currency) > 0:
            return {
                'domain': {
                    'ks_woo_currency': [('id', 'in', self.ks_woo_multi_currency.ids)]
                }
            }
        elif not self.ks_multi_currency_option:
            return {
                'domain': {
                    'ks_woo_currency': [('id', 'in', self.env['res.currency'].search([]).ids)]
                }
            }
        return {
            'domain': {
                'ks_woo_currency': [('id', 'in', [])]
            }
        }

    @api.model
    def create(self, values):
        values.update({
            'ks_import_order_state_config': [
                (0, 0, {'ks_woo_states': 'on-hold', 'ks_odoo_state': 'draft'}),
                (0, 0, {'ks_woo_states': 'pending', 'ks_odoo_state': 'sale'}),
                (0, 0, {'ks_woo_states': 'processing', 'ks_odoo_state': 'sale', 'ks_create_invoice': True,
                        'ks_set_invoice_state': 'paid'}),
                (0, 0, {'ks_woo_states': 'completed', 'ks_odoo_state': 'sale', 'ks_create_invoice': True,
                        'ks_set_invoice_state': 'paid', 'ks_confirm_shipment': True})],
            'ks_woo_fees': self.env.ref('ks_woocommerce.ks_woo_fees').id,
            'ks_woo_shipping': self.env.ref('ks_woocommerce.ks_woo_shipping_fees').id,
            'ks_woo_customer': self.env.ref('ks_woocommerce.ks_woo_guest_customers').id
        })
        res = super(KsWooCommerceInstance, self).create(values)
        res.ks_manage_auto_job()
        return res

    # Creating Multi Currency Pricelist or Single Currency Pricelist based on the option

    def write(self, values):
        if values.get('ks_multi_currency_option') or values.get('ks_woo_multi_currency'):
            vals = []
            if values.get('ks_multi_currency_option'):
                if values.get('ks_woo_multi_currency') is not None:
                    for currency_id in values.get('ks_woo_multi_currency')[0][2]:
                        if currency_id != self.env['product.pricelist'].search(
                                [('ks_instance_id', '=', self.id), ('currency_id', '=', currency_id)]).currency_id.id:
                            currency_id = self.env['res.currency'].browse(currency_id)
                            price_list_data = {
                                'name': self.ks_name + ' ' + currency_id.name + ' Pricelist',
                                'currency_id': currency_id.id,
                                'company_id': self.ks_company.id,
                                'ks_instance_id': self.id,
                            }
                            vals.append(price_list_data)
                    ks_price_list_ids = self.env['product.pricelist'].create(vals)
                    values.update({'ks_woo_pricelist_ids': [(6, 0, ks_price_list_ids.ids)]})
                else:
                    for currency_id in self.ks_woo_multi_currency.ids:
                        if currency_id != self.env['product.pricelist'].search(
                                [('ks_instance_id', '=', self.id), ('currency_id', '=', currency_id)]).currency_id.id:
                            currency_id = self.env['res.currency'].browse(currency_id)
                            price_list_data = {
                                'name': self.ks_name + ' ' + currency_id.name + ' Pricelist',
                                'currency_id': currency_id.id,
                                'company_id': self.ks_company.id,
                                'ks_instance_id': self.id,
                            }
                            vals.append(price_list_data)
                    ks_price_list_ids = self.env['product.pricelist'].create(vals)
                    values.update({'ks_woo_pricelist_ids': [(6, 0, ks_price_list_ids.ids)]})
            else:
                if values.get('ks_woo_multi_currency') is not None:
                    for currency_id in values.get('ks_woo_multi_currency')[0][2]:
                        if currency_id != self.env['product.pricelist'].search(
                                [('ks_instance_id', '=', self.id), ('currency_id', '=', currency_id)]).currency_id.id:
                            currency_id = self.env['res.currency'].browse(currency_id)
                            price_list_data = {
                                'name': self.ks_name + ' ' + currency_id.name + ' Pricelist',
                                'currency_id': currency_id.id,
                                'company_id': self.ks_company.id,
                                'ks_instance_id': self.id,
                            }
                            vals.append(price_list_data)
                    ks_price_list_ids = self.env['product.pricelist'].create(vals)
                    values.update({'ks_woo_pricelist_ids': [(6, 0, ks_price_list_ids.ids)]})
        else:
            if values.get('ks_woo_currency'):
                if values.get('ks_woo_currency') not in self.ks_woo_pricelist.search([]).currency_id.ids:
                    price_list_data = {
                        'name': self.ks_name + ' ' + self.env['res.currency'].search(
                            [('id', '=', values.get('ks_woo_currency'))]).name + ' Pricelist',
                        'currency_id': values.get('ks_woo_currency'),
                        'company_id': self.ks_company.id,
                        'ks_instance_id': self.id
                    }
                    ks_price_list = self.env['product.pricelist'].create(price_list_data)
                    values.update({'ks_woo_pricelist': [(6, 0, ks_price_list)]})

        res = super(KsWooCommerceInstance, self).write(values)
        self.ks_manage_auto_job()
        return res

    def ks_manage_auto_job(self):
        if self.ks_instance_state != 'active':
            if self.ks_aio_cron_id.active:
                self.ks_aio_cron_id.active = False
            elif self.ks_aip_cron_id.active:
                self.ks_aip_cron_id.active = False
            elif self.ks_aus_cron_id.active:
                self.ks_aus_cron_id.active = False
            elif self.ks_auos_cron_id.active:
                self.ks_auos_cron_id.active = False
        if self.ks_auto_import_product:
            data = {
                'name': self.ks_name + ': ' + 'WooCommerce Auto Product Import from Woo to Odoo (Do Not Delete)',
                'interval_number': 2,
                'interval_type': 'hours',
                'user_id': self.env.user.id,
                'model_id': self.env.ref('product.model_product_template').id,
                'state': 'code',
                'active': False,
                'numbercall': -1
            }
            if not self.ks_aip_cron_id:
                self.ks_aip_cron_id = self.env['ir.cron'].create(data)
                self.ks_aip_cron_id.write({'code': 'model.ks_auto_import_product(' + str(self.ks_aip_cron_id.id) + ')'})
        else:
            if self.ks_aip_cron_id.active:
                self.ks_aip_cron_id.active = False

        if self.ks_auto_update_stock:
            data = {
                'name': self.ks_name + ': ' + 'WooCommerce Auto Product Stock Update from Odoo to Woo (Do Not Delete)',
                'interval_number': 2,
                'interval_type': 'hours',
                'user_id': self.env.user.id,
                'model_id': self.env.ref('product.model_product_template').id,
                'state': 'code',
                'active': False,
                'numbercall': -1
            }
            if not self.ks_aus_cron_id:
                self.ks_aus_cron_id = self.env['ir.cron'].create(data)
                self.ks_aus_cron_id.code = 'model.ks_auto_update_stock(' + str(self.ks_aus_cron_id.id) + ')'
        else:
            if self.ks_aus_cron_id.active:
                self.ks_aus_cron_id.active = False

        if self.ks_auto_import_order:
            data = {
                'name': self.ks_name + ': ' + 'WooCommerce Auto Order Import from Woo to Odoo (Do Not Delete)',
                'interval_number': 2,
                'interval_type': 'hours',
                'user_id': self.env.user.id,
                'model_id': self.env.ref('sale.model_sale_order').id,
                'state': 'code',
                'active': False,
                'numbercall': -1,
            }
            if not self.ks_aio_cron_id:
                self.ks_aio_cron_id = self.env['ir.cron'].create(data)
                self.ks_aio_cron_id.code = 'model.ks_auto_import_order(' + str(self.ks_aio_cron_id.id) + ')'
        else:
            if self.ks_aio_cron_id.active:
                self.ks_aio_cron_id.active = False

        if self.ks_auto_update_order_status:
            data = {
                'name': self.ks_name + ': ' + 'WooCommerce Auto Order Status Update from Odoo to Woo(Do Not Delete)',
                'interval_number': 2,
                'interval_type': 'hours',
                'user_id': self.env.user.id,
                'model_id': self.env.ref('sale.model_sale_order').id,
                'state': 'code',
                'active': False,
                'numbercall': -1,
            }
            if not self.ks_auos_cron_id:
                self.ks_auos_cron_id = self.env['ir.cron'].create(data)
                self.ks_auos_cron_id.code = 'model.ks_auto_update_order_status(' + str(self.ks_auos_cron_id.id) + ')'
        else:
            if self.ks_auos_cron_id.active:
                self.ks_auos_cron_id.active = False

    def _compute_count_of_woo_records(self):
        for rec in self:
            search_query = [('ks_woo_instance_id', '=', rec.id), ('ks_woo_id', '!=', False)]
            rec.ks_woo_count_orders = rec.env['sale.order'].search_count(search_query)
            rec.ks_woo_count_products = rec.env['product.template'].search_count(search_query)
            rec.ks_woo_count_coupons = rec.env['ks.woo.coupon'].search_count(search_query)
            rec.ks_woo_count_customers = rec.env['res.partner'].search_count(search_query)

    def open_form_action(self):
        view = self.env.ref('ks_woocommerce.ks_woo_instance_operation_form_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'WooCommerce Operations',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_model': 'ks.woo.instance.operation',
            'view_mode': 'form',
            'context': {'default_ks_woo_instances': [(6, 0, [self.id])], 'default_woo_instance': True},
            'target': 'new',
        }

    def ks_open_woo_orders(self):
        action = self.env.ref('ks_woocommerce.action_woocommerce_sale_order').read()[0]
        action['domain'] = [('ks_woo_instance_id', '=', self.id)]
        return action

    def ks_open_woo_products(self):
        action = self.env.ref('ks_woocommerce.action_woocommerce_product_templates').read()[0]
        action['domain'] = [('ks_woo_instance_id', '=', self.id)]
        return action

    def ks_open_woo_coupons(self):
        action = self.env.ref('ks_woocommerce.action_woocommerce_coupons').read()[0]
        action['domain'] = [('ks_woo_instance_id', '=', self.id)]
        return action

    def ks_open_woo_customers(self):
        action = self.env.ref('ks_woocommerce.action_woocommerce_res_partner').read()[0]
        action['domain'] = [('ks_woo_instance_id', '=', self.id)]
        return action

    def ks_open_woo_configuration(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'WooCommerce Operations',
            'view': 'form',
            'res_id': self.id,
            'res_model': 'ks.woocommerce.instances',
            'view_mode': 'form',
        }

    def ks_open_instance_logs(self):
        action = self.env.ref('ks_woocommerce.action_woocommerce_logs').read()[0]
        action['domain'] = [('ks_woo_instance_id', '=', self.id)]
        return action

    def ks_connect_to_woo_instance(self):
        try:
            wcapi = self.ks_api_authentication()
            if wcapi.get("").status_code == 200:
                message = 'Connection Successful'
                names = 'Success'
                self.ks_instance_connected = True
                self.ks_instance_state = 'connected'
            else:
                message = str(wcapi.get("").status_code) + ': ' + eval(wcapi.get("").text).get('message')
                names = 'Error'
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                         ks_status='success' if wcapi.get("").status_code in [200,
                                                                                                              201] else 'failed',
                                                         ks_type='system_status',
                                                         ks_woo_instance_id=self,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='connection',
                                                         response='Connection successful' if wcapi.get(
                                                             "").status_code in [200, 201] else wcapi.get("").text)
        except ConnectionError:
            raise ValidationError(
                "Couldn't Connect the instance !! Please check the network connectivity or the configuration parameters are "
                "correctly set.")
        return self.env['ks.message.wizard'].ks_pop_up_message(names=names, message=message)

    def ks_activate_instance(self):
        if self.ks_instance_connected and self.ks_instance_state == 'connected':
            self.ks_instance_state = 'active'
            return self.env['ks.message.wizard'].ks_pop_up_message(names='Success',
                                                                   message='Instance Activated')

    def ks_deactivate_instance(self):
        if self.ks_instance_connected and self.ks_instance_state == 'active':
            self.ks_instance_state = 'deactivate'
            return self.env['ks.message.wizard'].ks_pop_up_message(names='Success',
                                                                   message='Instance Deactivated')

    def ks_api_authentication(self):
        wcapi = WCAPI(
            url=self.ks_woo_store_url,
            consumer_key=self.ks_customer_key,
            consumer_secret=self.ks_customer_secret,
            wp_api=True,
            version=self.ks_wc_version,
            verify_ssl=self.ks_verify_ssl,
            timeout=50
        )
        return wcapi

    def ks_store_record_after_export(self, odoo_record, woo_record):
        odoo_record.ks_woo_id = woo_record.get('id') or ''
        if woo_record.get('date_modified'):
            odoo_record.ks_date_updated = datetime.strptime((woo_record.get('date_modified') or False).replace('T',
                                                                                                               ' '),
                                                            DEFAULT_SERVER_DATETIME_FORMAT)
        if woo_record.get('date_created'):
            odoo_record.ks_date_created = datetime.strptime((woo_record.get('date_created') or False).replace('T',
                                                                                                              ' '),
                                                            DEFAULT_SERVER_DATETIME_FORMAT)

    def ks_store_record_after_import(self, odoo_record, woo_record, instance):
        odoo_record.ks_woo_id = woo_record.get('id') or ''
        odoo_record.ks_woo_instance_id = instance.id

    def ks_instance_status_error(self):
        return self.env['ks.message.wizard'].ks_pop_up_message(names='Error',
                                                               message="WooCommerce instance must be in "
                                                                       "active state to perform operations.")


class KsWooOrderStatus(models.Model):
    _name = 'ks.woocommerce.status'
    _description = 'WooCommerce Order Status'

    ks_woo_states = fields.Selection([('on-hold', 'On-hold'), ('pending', 'Pending'),
                                      ('processing', 'Processing'), ('completed', 'Completed')], readonly=True,
                                     string='Woo State')
    ks_sync = fields.Boolean('Sync')
    ks_odoo_state = fields.Selection([('draft', 'Quotation'), ('sale', 'Sale Order')],
                                     string='Odoo state')
    ks_create_invoice = fields.Boolean(string='Create Invoice')
    ks_set_invoice_state = fields.Selection(
        [('false', 'False'), ('draft', 'Draft'), ('open', 'Open'), ('paid', 'Paid')],
        string='Set Invoice state', default=False)
    ks_confirm_shipment = fields.Boolean(string='Confirm Shipment')
    ks_instance_id = fields.Many2one('ks.woocommerce.instances', string="WooCommerce Instance")

    @api.onchange('ks_odoo_state')
    def _onchange_ks_odoo_state(self):
        if self.ks_odoo_state == 'draft':
            self.ks_create_invoice = self.ks_confirm_shipment = False
            self.ks_set_invoice_state = 'false'

    @api.onchange('ks_create_invoice')
    def _onchnage_ks_create_invoice(self):
        if self.ks_create_invoice:
            if self.ks_odoo_state == 'draft':
                raise ValidationError('You can not create invoice if order is in Quotation State !')
        else:
            self.ks_set_invoice_state = 'false'
