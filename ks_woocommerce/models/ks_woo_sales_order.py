# -*- coding: utf-8 -*-
from datetime import datetime
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from requests.exceptions import ConnectionError

_logger = logging.getLogger( __name__ )


class KsSaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    ks_woo_id = fields.Integer('Woocommerce Id', readonly=True, default=0)
    ks_woo_instance_id = fields.Many2one('ks.woocommerce.instances',
                                         string='Woo Instance',
                                         help="""WooCommerce Instance: Ths instance of woocomerce to which this 
                                                 product variant belongs to.""")
    ks_woo_status = fields.Selection([('on-hold', 'On-Hold'), ('pending', 'Pending'), ('processing', 'Processing'),
                                      ('cancelled', 'Cancelled'), ('refunded', 'Refunded'), ('completed', 'Completed')],
                                     string="Woo Status", default='pending')
    ks_woo_coupons = fields.Many2many('ks.woo.coupon', string="WooCommerce Coupons", readonly=True)
    ks_exported_in_woo = fields.Boolean('Exported in Woo',
                                        readonly=True,
                                        store=True,
                                        compute='_ks_compute_export_in_woo',
                                        help="""Exported in Woo: If enabled, the product is synced with the specified 
                                            WooCommerce Instance""")
    ks_woo_payment_gateway = fields.Many2one('ks.woo.payment.gateway', string="Woo Payment Gateway")
    ks_date_created = fields.Datetime('Created On',
                                      readonly=True,
                                      help="Created On: Date on which the WooCommerce Sale Order has been created")
    ks_date_updated = fields.Datetime('Updated On',
                                      readonly=True,
                                      help="Updated On: Date on which the WooCommerce Sale Order has been last updated")
    ks_customer_ip_address = fields.Char(string='Customer IP', readonly=True,
                                         help="Customer IP: WooCommerce Customer's IP address")
    ks_woo_transaction_id = fields.Char(string='Transaction Id', readonly=True,
                                        help="Transaction Id: Unique transaction ID of WooCommerce Sale Order")

    @api.model
    def create(self, vals):
        if vals.get('ks_woo_instance_id') and vals.get('ks_woo_id'):
            woo_instance = self.env['ks.woocommerce.instances'].search([('id', '=', vals.get('ks_woo_instance_id'))])
            if woo_instance and woo_instance.ks_use_custom_order_prefix:
                if woo_instance.ks_order_prefix:
                    woo_prefix = woo_instance.ks_order_prefix.upper()
                    vals['name'] = woo_prefix + ' #' + str(vals.get('ks_woo_id'))
        return super(KsSaleOrderInherit, self).create(vals)

    def action_confirm(self):
        super(KsSaleOrderInherit, self).action_confirm()
        if self.ks_woo_instance_id and self.ks_woo_id:
            self.date_order = self.ks_date_created
        return True

    def ks_update_woo_order_status(self):
        for each_rec in self:
            if each_rec.ks_woo_instance_id and each_rec.ks_woo_instance_id.ks_instance_state == 'active':
                try:
                    wcapi = each_rec.ks_woo_instance_id.ks_api_authentication()
                    if wcapi.get("").status_code in [200, 201]:
                        woo_status_response = wcapi.put("orders/%s" % each_rec.ks_woo_id,
                                                        {"status": each_rec.ks_woo_status})
                        self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=each_rec.ks_woo_id,
                                                                     ks_status='success' if woo_status_response.status_code in [
                                                                         200, 201] else 'failed',
                                                                     ks_type='order',
                                                                     ks_woo_instance_id=each_rec.ks_woo_instance_id,
                                                                     ks_operation='odoo_to_woo',
                                                                     ks_operation_type='update',
                                                                     response='Order [' + each_rec.name + ']  status has been succesfully updated' if woo_status_response.status_code in [
                                                                         200,
                                                                         201] else 'The status update operation failed for Order [' + each_rec.name + '] due to ' + eval(
                                                                         woo_status_response.text).get('message'))
                    else:
                        self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                     ks_status='success' if wcapi.get(
                                                                         "").status_code in [
                                                                                                200,
                                                                                                201] else 'failed',
                                                                     ks_type='system_status',
                                                                     ks_woo_instance_id=each_rec.ks_woo_instance_id,
                                                                     ks_operation='odoo_to_woo',
                                                                     ks_operation_type='connection',
                                                                     response='Connection successful' if wcapi.get(
                                                                         "").status_code in [200, 201] else wcapi.get(
                                                                         "").text)
                except ConnectionError:
                    self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=each_rec.ks_woo_instance_id,
                                                                        type='order',
                                                                        operation='odoo_to_woo',
                                                                        ks_woo_id=each_rec.ks_woo_id)
                except Exception as e:
                    self.env['ks.woo.sync.log'].ks_exception_log(record=each_rec, type="order",
                                                                 operation_type="update",
                                                                 instance_id=each_rec.ks_woo_instance_id,
                                                                 operation="odoo_to_woo", exception=e)
            else:
                self.env['ks.woo.sync.log'].ks_no_instance_log(each_rec, 'order')

    def ks_cancel_sale_order_in_woo(self):
        if self.ks_woo_instance_id and self.ks_woo_instance_id.ks_instance_state == 'active':
            try:
                wcapi = self.ks_woo_instance_id.ks_api_authentication()
                if wcapi.get("").status_code in [200, 201]:
                    if self.ks_woo_instance_id.ks_instance_state == 'active':
                        woo_cancel_response = wcapi.put("orders/%s" % self.ks_woo_id, {"status": "cancelled"})
                        if woo_cancel_response.status_code in [200, 201]:
                            self.ks_woo_status = 'cancelled'
                            woo_cancel_status = 'success'
                        else:
                            woo_cancel_status = 'failed'
                        self.env['ks.woo.sync.log'].create_log_param(
                            ks_woo_id=self.ks_woo_id,
                            ks_status=woo_cancel_status,
                            ks_type='order',
                            ks_woo_instance_id=self.ks_woo_instance_id,
                            ks_operation='odoo_to_woo',
                            ks_operation_type='create',
                            response='Order [' + self.name + '] has been succesfully cancelled' if woo_cancel_status == 'success' else 'The cancel operation failed for Order [' + self.name + '] due to ' + eval(
                                woo_cancel_response.text).get('message'),
                        )
                    else:
                        return self.env['ks.message.wizard'].ks_pop_up_message(names='Error',
                                                                               message='The instance must be in '
                                                                                       'active state to perform '
                                                                                       'the operations')
                else:
                    self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                 ks_status='success' if wcapi.get("").status_code in [
                                                                     200,
                                                                     201] else 'failed',
                                                                 ks_type='system_status',
                                                                 ks_woo_instance_id=self.ks_woo_instance_id,
                                                                 ks_operation='odoo_to_woo',
                                                                 ks_operation_type='connection',
                                                                 response='Connection successful' if wcapi.get(
                                                                     "").status_code in [200, 201] else wcapi.get(
                                                                     "").text)
            except ConnectionError:
                raise ValidationError("Couldn't Connect the Instance[ %s ]  !! Please check the network connectivity"
                                      " or the configuration parameters are not "
                                      "correctly set" % self.ks_woo_instance_id.ks_name)
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=self, type="order",
                                                             operation_type="cancel",
                                                             instance_id=self.ks_woo_instance_id,
                                                             operation="odoo_to_woo", exception=e)
        else:
            self.env['ks.woo.sync.log'].ks_no_instance_log(self, 'product')

    @api.depends('ks_woo_id')
    def _ks_compute_export_in_woo(self):
        """
        This will make enable the Exported in Woo if record has the WooCommerce Id

        :return: None
        """
        for rec in self:
            rec.ks_exported_in_woo = bool(rec.ks_woo_id)

    @api.model
    def ks_export_order_to_woo(self):
        for order in self:
            if order.ks_woo_instance_id and order.ks_woo_instance_id.ks_instance_state == 'active':
                try:
                    wcapi = order.ks_woo_instance_id.ks_api_authentication()
                    if wcapi.get("").status_code:
                        if not order.ks_woo_id:
                            json_data = self.prepare_product_order_data_to_export_in_woo(order)
                            woo_response = wcapi.post("orders", json_data)
                            woo_product_record = woo_response.json()
                            if woo_response.status_code in [200, 201]:
                                order.write({
                                    'ks_date_created': datetime.strptime(
                                        (woo_product_record.get('date_created') or False).replace('T',
                                                                                                  ' '),
                                        DEFAULT_SERVER_DATETIME_FORMAT),
                                    'ks_date_updated': datetime.strptime(
                                        (woo_product_record.get('date_modified') or False).replace('T',
                                                                                                   ' '),
                                        DEFAULT_SERVER_DATETIME_FORMAT),
                                    'ks_woo_id': woo_product_record.get('id') or ''
                                })
                                order.ks_woo_id = woo_product_record.get('id')
                            woo_export_status = 'success' if woo_response.status_code in [200, 201] else 'failed'
                            self.env['ks.woo.sync.log'].create_log_param(
                                ks_woo_id=woo_product_record.get('id') or '' if woo_response.status_code in [200,
                                                                                                             201] else False,
                                ks_status=woo_export_status,
                                ks_type='order',
                                ks_woo_instance_id=order.ks_woo_instance_id,
                                ks_operation='odoo_to_woo',
                                ks_operation_type='create',
                                response='Order [' + order.name + '] has been succesfully exported' if woo_export_status == 'success' else 'The export operation failed for Order [' + order.name + '] due to ' + eval(
                                    woo_response.text).get('message'),
                            )
                        else:
                            self.env['ks.woo.sync.log'].create_log_param(
                                ks_woo_id=order.ks_woo_id,
                                ks_status='failed',
                                ks_type='order',
                                ks_woo_instance_id=order.ks_woo_instance_id,
                                ks_operation='odoo_to_woo',
                                ks_operation_type='create',
                                response='Order [' + order.name + '] is already exported'
                            )
                    else:
                        self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                     ks_status='success' if wcapi.get(
                                                                         "").status_code in [
                                                                                                200,
                                                                                                201] else 'failed',
                                                                     ks_type='system_status',
                                                                     ks_woo_instance_id=order.ks_woo_instance_id,
                                                                     ks_operation='odoo_to_woo',
                                                                     ks_operation_type='connection',
                                                                     response='Connection successful' if wcapi.get(
                                                                         "").status_code in [200, 201] else wcapi.get(
                                                                         "").text)
                except ConnectionError:
                    self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=order.ks_woo_instance_id,
                                                                        type='order',
                                                                        operation='odoo_to_woo',
                                                                        ks_woo_id=order.ks_woo_id)
                except Exception as e:
                    self.env['ks.woo.sync.log'].ks_exception_log(record=order, type="order",
                                                                 operation_type="create",
                                                                 instance_id=order.ks_woo_instance_id,
                                                                 operation="odoo_to_woo", exception=e)
            else:
                self.env['ks.woo.sync.log'].create_log_param(
                    ks_woo_id=False,
                    ks_status='failed',
                    ks_type='order',
                    ks_woo_instance_id=order.ks_woo_instance_id,
                    ks_operation='odoo_to_woo',
                    ks_operation_type='create',
                    response='For exporting in WooCommerce the Orders [' + order.name + '] must have instance Id selected and in active state.',
                )

    def prepare_product_order_data_to_export_in_woo(self, order_data):
        data = {
            'customer_note': order_data.note,
            'line_items': self._get_order_woo_lines(order_data.order_line),
            'status': order_data.ks_woo_status,
        }
        if order_data.partner_id:
            cust_data = self._ks_manage_cutomer(order_data.partner_id)
            if cust_data:
                data.update(cust_data)
        return data

    def _ks_manage_cutomer(self, customer):
        if not customer.ks_woo_id:
            customer.ks_update_customer_to_woo()
        data = customer._ks_prepare_customer_data(customer.create_json_data())
        json_data = {
            'customer_id': customer.ks_woo_id,
            'billing': data['billing'] if data['billing'] else '',
            'shipping': data['billing'] if data['billing'] else '',
        }
        return json_data

    def _get_order_woo_lines(self, order_line_data):
        line_data = []
        for order_line in order_line_data:
            line_data.append({
                "id": order_line.ks_woo_id,
                "name": order_line.name,
                "product_id": order_line.product_id.ks_woo_id,
                "variation_id": order_line.product_id.ks_woo_variant_id,
                "quantity": order_line.product_uom_qty,
                "subtotal": str(order_line.price_unit * order_line.product_uom_qty),
                "total": str(order_line.price_reduce_taxexcl * order_line.product_uom_qty),
                "sku": order_line.product_id.default_code if order_line.product_id.default_code else '',
            })
        return line_data

    @api.model
    def ks_import_order_to_odoo(self):
        """
        This will get all the woocommerce sale order data with status selected on instance settings and create or update
         the sale order on odoo
        :param wcapi: The WooCommerce API instance
        :param instance_id: The WooCommerce instance
        :return:
        """
        instance_id = self.env['ks.woocommerce.instances'].search([('id', '=', self.ks_woo_instance_id.id)], limit=1)
        if instance_id.ks_instance_state == 'active':
            try:
                wcapi = self.ks_woo_instance_id.ks_api_authentication()
                if wcapi.get("").status_code in [200, 201]:
                    woo_orders_record = []
                    woo_order_response = wcapi.get("orders/%s" % self.ks_woo_id)
                    if woo_order_response.status_code in [200, 201]:
                        woo_orders_record_all = woo_order_response.json()
                        if woo_orders_record_all.get('status') in instance_id.ks_import_order_state_config.filtered(
                                lambda r: r.ks_sync is True).mapped('ks_woo_states'):
                            woo_orders_record.append(woo_orders_record_all)
                            #
                        for each_record in woo_orders_record:
                            self.ks_manage_sale_order_data(each_record, wcapi, instance_id)
                    else:
                        self.env['ks.woo.sync.log'].create_log_param(
                            ks_woo_id=False,
                            ks_status='failed',
                            ks_type='order',
                            ks_woo_instance_id=instance_id,
                            ks_operation='woo_to_odoo',
                            ks_operation_type='fetch',
                            response=str(woo_order_response.status_code) + eval(woo_order_response.text).get('message'),
                        )
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='order',
                                                                    operation='woo_to_odoo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="order",
                                                             operation_type="import",
                                                             instance_id=instance_id,
                                                             operation="woo_to_odoo", exception=e)
        else:
            return self.env['ks.message.wizard'].ks_pop_up_message(names='Error', message='The instance must be in '
                                                                                          'active state to perform '
                                                                                          'the operations')

    def ks_sync_sale_order(self, wcapi, instance_id):
        """
        This will get all the woocommerce sale order data with status selected on instance settings and create or update
         the sale order on odoo
        :param wcapi: The WooCommerce API instance
        :param instance_id: The WooCommerce instance
        :return:
        """
        if instance_id.ks_instance_state == 'active':
            multi_api_call = True
            per_page = 100
            page = 1
            try:
                while (multi_api_call):

                    ## HEREEE!!!!!!!!!!!!!!!!!!!!!! I FOUND THE LINE 
                    woo_order_response = wcapi.get("orders", params={"per_page": per_page, "page": page})
                    woo_orders_record_all = woo_order_response.json()
                    woo_orders_record = []

                    for each_woo_orders_record in woo_orders_record_all:
                        if each_woo_orders_record.get('status') in instance_id.ks_import_order_state_config.filtered(
                                lambda r: r.ks_sync is True).mapped('ks_woo_states'):
                            woo_orders_record.append(each_woo_orders_record)

                    for each_record in woo_orders_record:
                        self.ks_manage_sale_order_data(each_record, wcapi, instance_id)

                    total_api_calls = woo_order_response.headers._store.get('x-wp-totalpages')[1]
                    remaining_api_calls = int(total_api_calls) - page
                    if remaining_api_calls > 0:
                        page += 1
                    else:
                        multi_api_call = False
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='order',
                                                                    operation='woo_to_odoo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="order",
                                                             operation_type="import",
                                                             instance_id=instance_id,
                                                             operation="woo_to_odoo", exception=e)
        else:
            return self.env['ks.message.wizard'].ks_pop_up_message(names='Error', message='The instance must be in '
                                                                                          'active state to perform '
                                                                                          'the operations')

    def ks_manage_sale_order_data(self, json_data, wcapi, instance_id):
        sale_order_exist = self.search([('ks_woo_id', '=', json_data.get('id')),
                                        ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
        if not sale_order_exist.ks_date_updated == datetime.strptime(json_data.get('date_modified'),
                                                                     '%Y-%m-%dT%H:%M:%S'):
            if instance_id.ks_multi_currency_option:
                ks_currency_ids = instance_id.ks_woo_multi_currency
                currency_name = instance_id.ks_woo_multi_currency.mapped('name')

                if json_data.get('currency') in currency_name:
                    for ks_currency in ks_currency_ids:
                        if ks_currency.name == json_data.get('currency'):
                            self.ks_create_update_woo_order(json_data, sale_order_exist, wcapi, instance_id)
                            break
                else:
                    e = 'Please select currency "' + str(json_data.get('currency')) + '" from Instance Configuration'
                    raise Exception(e)
            else:
                self.ks_create_update_woo_order(json_data, sale_order_exist, wcapi, instance_id)
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='success',
                ks_type='order',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='update',
                response='The order data already exist in the database with no mdofications'
            )

    def ks_create_update_woo_order(self, json_data, sale_order_exist, wcapi, instance_id):
        sale_order_data = self.prepare_sale_order_data_for_odoo(json_data, wcapi, instance_id)
        valid_order = True
        for i in sale_order_data.get('order_line'):
            if not i[2]['product_id']:
                valid_order = False
        if valid_order:
            if sale_order_exist:
                if sale_order_exist.state == 'done':
                    sale_order_exist.action_unlock()
                sale_order_exist.write(sale_order_data)
                sale_order_exist.ks_manage_taxes(json_data)
                ks_operation_type = 'update'
            else:
                sale_order_exist = self.create(sale_order_data)
                sale_order_exist.ks_manage_taxes(json_data)
                ks_operation_type = 'create'

            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=json_data.get('id'),
                ks_status='success',
                ks_type='order',
                ks_woo_instance_id=instance_id,
                ks_operation='woo_to_odoo',
                ks_operation_type=ks_operation_type,
                response='Order [' + sale_order_exist.name + '] has been succesfully created' if ks_operation_type == 'create' else 'Order [' + sale_order_exist.name + '] has been succesfully updated',
            )
            if sale_order_exist.ks_woo_status == 'cancel':
                sale_order_exist.action_cancel()
            sale_order_exist.ks_process_the_sale_order(json_data.get('status'), json_data)
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=json_data.get('id'),
                ks_status='failed',
                ks_type='order',
                ks_woo_instance_id=instance_id,
                ks_operation='woo_to_odoo',
                ks_operation_type='create' if not sale_order_exist else 'update',
                response='Order creation is failed due to some data missing in WooCommerce' if not sale_order_exist else
                'Order creation is failed due to some data missing in WooCommerce'
            )

    def ks_process_the_sale_order(self, woo_status, json_data):
        order_process_step = self.ks_assign_order_step(woo_status)
        order_status = self.ks_check_the_order_processing_status(woo_status, order_process_step)
        if order_status:
            if self.order_line.mapped('product_id'):
                self.order_line.mapped('product_id').write({
                    'invoice_policy': 'order'
                })
                if order_process_step.get('action_confirm') != 'draft' and order_process_step.get('action_confirm'):
                    self.action_confirm()
            if self.invoice_status != 'invoiced' and self.order_line:
                ks_sale_inv_id = self.env['sale.advance.payment.inv'].create(
                    {'advance_payment_method': 'delivered'})
                ks_sale_inv_id = ks_sale_inv_id.with_context(active_id=self.id, active_ids=self.ids)
                if order_process_step.get('create_invoices'):
                    ks_sale_inv_id.create_invoices()
                if order_process_step.get('invoice_state') in ['open', 'paid']:
                    self.invoice_ids[0].action_post()
                if order_process_step.get('invoice_state') == 'paid':
                    invoice_id = self.invoice_ids[0]
                    method = invoice_id.journal_id.inbound_payment_method_ids
                    ks_values = {'amount': self.amount_total,
                                 'journal_id': self.ks_woo_payment_gateway.ks_journal_id.id if self.ks_woo_payment_gateway.ks_journal_id else self.ks_woo_instance_id.ks_journal_id.id,
                                 'currency_id': invoice_id.currency_id.id,
                                 'payment_date': invoice_id.create_date,
                                 'payment_method_id': method[0].id or False,
                                 'payment_type': "inbound",
                                 'invoice_ids': [(6, 0, invoice_id.ids)],
                                 'partner_type': 'customer',
                                 'partner_id': self.partner_id.id,
                                 'communication': invoice_id.invoice_payment_ref or invoice_id.ref or invoice_id.name,
                                 'ks_woo_payment_id': self.ks_woo_payment_gateway.id if self.ks_woo_payment_gateway else False
                                 }
                    ks_payment_card = self.env['account.payment'].create(ks_values)
                    ks_payment_card._onchange_amount()
                    ks_payment_card._compute_payment_difference()
                    ks_payment_id = ks_payment_card.with_context(active_id=invoice_id.id,
                                                                 active_ids=invoice_id.ids)
                    ks_payment_id.post()
            elif self.invoice_status == 'invoiced' and 'draft' in self.invoice_ids.mapped('state'):
                self.invoice_ids[0].action_post()
                if order_process_step.get('invoice_state') == 'paid':
                    invoice_id = self.invoice_ids[0]
                    method = invoice_id.journal_id.inbound_payment_method_ids
                    ks_values = {'amount': self.amount_total,
                                 'journal_id': self.ks_woo_payment_gateway.ks_journal_id.id if self.ks_woo_payment_gateway.ks_journal_id else self.ks_woo_instance_id.ks_journal_id.id,
                                 'currency_id': invoice_id.currency_id.id,
                                 'payment_date': invoice_id.create_date,
                                 'payment_method_id': method[0].id or False,
                                 'payment_type': "inbound",
                                 'invoice_ids': [(6, 0, invoice_id.ids)],
                                 'partner_type': 'customer',
                                 'partner_id': self.partner_id.id,
                                 'communication': invoice_id.invoice_payment_ref or invoice_id.ref or invoice_id.name,
                                 'ks_woo_payment_id': self.ks_woo_payment_gateway.id if self.ks_woo_payment_gateway else False
                                 }
                    ks_payment_card = self.env['account.payment'].create(ks_values)
                    ks_payment_card._onchange_amount()
                    ks_payment_card._compute_payment_difference()
                    ks_payment_id = ks_payment_card.with_context(active_id=invoice_id.id,
                                                                 active_ids=invoice_id.ids)
                    ks_payment_id.post()

            if order_process_step.get('confirm_shipment'):
                for ks_picking in self.picking_ids:
                    if ks_picking.state in ('cancel', 'done'):
                        continue
                    picking_id = ks_picking
                    ks_counter = self.ks_product_stock_picking_done(picking_id.move_lines)
                    if ks_counter == 1:
                        picking_id.button_validate()
        else:
            if self.state == 'sale':
                picking_list = self.picking_ids.mapped('state')
                create_picking = all(elem == 'cancel' for elem in picking_list) if picking_list else False
                if not self.picking_ids or create_picking:
                    self.order_line._action_launch_procurement_rule()

    def ks_assign_order_step(self, woo_status):
        order_configure_record = self.env['ks.woocommerce.status'].search([('ks_woo_states', '=', woo_status),
                                                                           ('ks_instance_id', '=',
                                                                            self.ks_woo_instance_id.id)])
        configure_data = {
            'action_confirm': order_configure_record.ks_odoo_state,
            'create_invoices': order_configure_record.ks_create_invoice,
            'invoice_state': order_configure_record.ks_set_invoice_state,
            'confirm_shipment': order_configure_record.ks_confirm_shipment
        }

        return configure_data

    def ks_product_stock_picking_done(self, stock_qty):
        ks_local_counter = 0
        for ks_move_line in stock_qty:  # for validating initial == demand
            if ks_move_line.quantity_done == 0:
                ks_move_line.quantity_done = ks_move_line.product_uom_qty
                ks_local_counter += 1
        if ks_local_counter == 0:
            return 0
        else:
            return 1

    def ks_check_the_order_processing_status(self, woo_status, order_process_step):
        create_invoice = order_process_step.get('create_invoices')
        odoo_state = self.state
        current_state = self.ks_mapped_order_status(woo_status)
        if current_state and self.state != current_state:
            if odoo_state != 'draft':
                if odoo_state == 'cancel':
                    self.action_draft()
                    self.ks_woo_status = woo_status
                    return True
                elif odoo_state == 'sale':
                    if current_state != 'done':
                        try:
                            self.action_cancel()
                            self.action_draft()
                            self.ks_woo_status = woo_status
                            return True
                        except Exception as e:
                            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=self.ks_woo_id,
                                                                         ks_status='failed',
                                                                         ks_type='order',
                                                                         ks_operation_type=False,
                                                                         ks_woo_instance_id=self.ks_woo_instance_id,
                                                                         ks_operation='woo_to_odoo',
                                                                         response='Order [' + self.name + '] can not be processed in Odoo due to %s' % e)
                            return False
            else:
                self.ks_woo_status = woo_status
                return True
        elif create_invoice:
            self.ks_woo_status = woo_status
            return True
        else:
            self.ks_woo_status = woo_status
            return False

    def ks_mapped_order_status(self, woo_state):
        current_state = ''
        order_configure_record = self.env['ks.woocommerce.status'].search([('ks_woo_states', '=', woo_state),
                                                                           ('ks_instance_id', '=',
                                                                            self.ks_woo_instance_id.id)])
        current_state = order_configure_record.ks_odoo_state
        return current_state

    def prepare_sale_order_data_for_odoo(self, each_record, wcapi, instance_id):
        data = {
            "ks_woo_id": each_record.get('id'),
            "ks_woo_instance_id": instance_id.id,
            'note': each_record.get('customer_note'),
            'currency_id': instance_id.ks_woo_currency.id,
            'partner_id': self._get_customer_id(each_record.get('customer_id'), wcapi, instance_id),
            'partner_invoice_id': self._get_customer_id(each_record.get('customer_id'), wcapi, instance_id,
                                                        invoice_address=each_record.get('billing')),
            'partner_shipping_id': self._get_customer_id(each_record.get('customer_id'), wcapi, instance_id,
                                                         shipping_address=each_record.get('shipping')),
            'order_line': self._get_order_lines(each_record, wcapi, instance_id),
            'warehouse_id': instance_id.ks_warehouse.id,
            'company_id': instance_id.ks_company.id,
            'team_id': instance_id.ks_sales_team.id,
            'user_id': instance_id.ks_sales_person.id,
            'ks_woo_payment_gateway': self._get_payment_gateway(each_record, instance_id),
            'ks_date_created': datetime.strptime((each_record.get('date_created')).replace('T', ' '),
                                                 DEFAULT_SERVER_DATETIME_FORMAT) if each_record.get(
                'date_created') else False,
            'ks_date_updated': datetime.strptime((each_record.get('date_modified')).replace('T', ' '),
                                                 DEFAULT_SERVER_DATETIME_FORMAT) if each_record.get(
                'date_modified') else False,
            'date_order': datetime.strptime((each_record.get('date_created')).replace('T', ' '),
                                            DEFAULT_SERVER_DATETIME_FORMAT) if each_record.get(
                'date_created') else False,
            'payment_term_id': instance_id.ks_payment_term_id.id,
            'ks_customer_ip_address': each_record.get('customer_ip_address'),
            'ks_woo_transaction_id': each_record.get('transaction_id')
        }
        coupon_ids = self._get_woo_coupons(each_record.get('coupon_lines'), instance_id)
        data.update({
            'ks_woo_coupons': [(6, 0, coupon_ids)] if coupon_ids else False
        })
        if not instance_id.ks_multi_currency_option:
            data.update({
                'pricelist_id': self.env['product.pricelist'].search([('currency_id','=',self.env['res.currency'].search([('id', '=', instance_id.ks_woo_currency.id)]).id),('ks_instance_id','=',instance_id.id)]).id
            })
        else:
            data.update({
                'pricelist_id': self.env['product.pricelist'].search([('currency_id','=',self.env['res.currency'].search([('id', '=', instance_id.ks_woo_currency.id)]).id),('ks_instance_id','=',instance_id.id)]).id
                })
        return data

    def ks_manage_taxes(self, sale_order_data):
        for each_record in sale_order_data.get('line_items'):
            sale_order_line_exist = self.env['sale.order.line'].search([('ks_woo_id', '=', each_record.get('id')),
                                                                        ('order_id', '=', self.id)], limit=1)
            if sale_order_line_exist:
                sale_order_line_exist.price_tax = each_record.get('subtotal_tax') or 0

        for each_rec in sale_order_data.get('fee_lines'):
            sale_order_line_exist = self.env['sale.order.line'].search([('ks_woo_id', '=', each_rec.get('id')),
                                                                        ('order_id', '=', self.id)], limit=1)
            if sale_order_line_exist:
                sale_order_line_exist.price_tax = each_rec.get('subtotal_tax') or 0
        for rec in sale_order_data.get('shipping_lines'):
            sale_order_line_exist = self.env['sale.order.line'].search([('ks_woo_id', '=', rec.get('id')),
                                                                        ('order_id', '=', self.id)], limit=1)
            if sale_order_line_exist:
                sale_order_line_exist.price_tax = rec.get('subtotal_tax') or 0
        self.amount_tax = sale_order_data.get('total_tax') or 0
        self.amount_total = self.amount_tax + self.amount_untaxed

    def _get_payment_gateway(self, each_record, instance_id):
        if each_record.get('payment_method') and each_record.get('payment_method_title'):
            payment_gateway = self.env['ks.woo.payment.gateway'].search([
                ('ks_woo_pg_id', '=', each_record.get('payment_method')), ('ks_woo_instance_id', '=', instance_id.id)],
                limit=1)
            if not payment_gateway:
                payment_gateway = self.env['ks.woo.payment.gateway'].create({
                    'ks_woo_pg_id': each_record.get('payment_method') or '',
                    'ks_woo_instance_id': instance_id.id,
                    'ks_title': each_record.get('payment_method_title') or ''
                })
            return payment_gateway.id

    def _get_woo_coupons(self, woo_coupon_lines, instance_id):
        coupon_ids = []
        for each_coupon in woo_coupon_lines:
            coupon_exist_in_odoo = self.env['ks.woo.coupon'].search(
                [('ks_coupon_code', '=', each_coupon.get('code')),
                 ('ks_woo_instance_id', '=', instance_id.id)],
                limit=1)
            if coupon_exist_in_odoo:
                coupon_ids.append(coupon_exist_in_odoo.id)
            else:
                coupon_id = self.env['ks.woo.coupon'].create({
                    'ks_woo_id': each_coupon.get('id'),
                    'ks_amount': float(each_coupon.get('discount') or 0),
                    'ks_coupon_code': each_coupon.get('code') or '',
                    'ks_woo_instance_id': instance_id.id
                }).id
                coupon_ids.append(coupon_id)
        return coupon_ids

    def _get_order_lines(self, json_data, wcapi, instance_id):
        order_lines = []
        for each_record in json_data.get('line_items'):
            sale_order_exist = self.search([('ks_woo_id', '=', json_data.get('id')),
                                            ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
            sale_order_line_exist = self.env['sale.order.line'].search([('ks_woo_id', '=', each_record.get('id')),
                                                                        ('order_id', '=', sale_order_exist.id)],
                                                                       limit=1)
            product = self._get_product_ids(each_record.get('variation_id'),
                                            each_record.get('product_id'), each_record,
                                            instance_id, wcapi)
            line_items_data = {
                'ks_woo_id': each_record.get('id'),
                'name': each_record.get('name'),
                'product_id': product.id,
                'product_uom_qty': each_record.get('quantity'),
                'price_unit': float(each_record.get('subtotal') or 0) / float(
                    each_record.get('quantity') or 0) if float(each_record.get('quantity') or 0) > 0 else 0,
                'ks_discount_amount': self.ks_calculate_percent_from_amont(float(each_record.get('subtotal') or 0),
                                                                           float(each_record.get('total') or 0)),
                'product_uom': product.uom_id.id,
                'tax_id': [(6, 0, self.get_tax_ids(json_data.get('tax_lines'), each_record.get('taxes'),
                                                   instance_id, wcapi))]
            }
            if sale_order_line_exist:
                order_lines.append((1, sale_order_line_exist.id, line_items_data))
            else:
                order_lines.append((0, 0, line_items_data))

        for each_rec in json_data.get('fee_lines'):
            sale_order_exist = self.search([('ks_woo_id', '=', json_data.get('id')),
                                            ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
            sale_order_line_exist = self.env['sale.order.line'].search([('ks_woo_id', '=', each_rec.get('id')),
                                                                        ('order_id', '=', sale_order_exist.id)],
                                                                       limit=1)

            fee_lines_data = {
                'ks_woo_id': each_rec.get('id'),
                'name': each_rec.get('name'),
                'product_id': self.env.ref('ks_woocommerce.ks_woo_fees').id,
                'product_uom': self.env.ref('ks_woocommerce.ks_woo_fees').uom_id.id,
                'product_uom_qty': 1,
                'price_unit': float(each_rec.get('amount') or each_rec.get('total') or 0),
                'tax_id': [(6, 0, self.get_tax_ids(json_data.get('tax_lines'), each_rec.get('taxes'),
                                                   instance_id, wcapi))]
            }
            if sale_order_line_exist:
                order_lines.append((1, sale_order_line_exist.id, fee_lines_data))
            else:
                order_lines.append((0, 0, fee_lines_data))

        for each_rec in json_data.get('shipping_lines'):
            sale_order_exist = self.search([('ks_woo_id', '=', json_data.get('id')),
                                            ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
            sale_order_line_exist = self.env['sale.order.line'].search([('ks_woo_id', '=', each_rec.get('id')),
                                                                        ('order_id', '=', sale_order_exist.id)],
                                                                       limit=1)

            shipping_lines_data = {
                'ks_woo_id': each_rec.get('id'),
                'name': each_rec.get('method_id') + "[Woo]",
                'product_id': self.env.ref('ks_woocommerce.ks_woo_shipping_fees').id,
                'product_uom': self.env.ref('ks_woocommerce.ks_woo_shipping_fees').uom_id.id,
                'product_uom_qty': 1,
                'price_unit': float(each_rec.get('total') or 0),
                'tax_id': [(6, 0, self.get_tax_ids(json_data.get('tax_lines'), each_rec.get('taxes'),
                                                   instance_id, wcapi))]
            }
            if sale_order_line_exist:
                order_lines.append((1, sale_order_line_exist.id, shipping_lines_data))
            else:
                order_lines.append((0, 0, shipping_lines_data))

        return order_lines

    def ks_calculate_percent_from_amont(self, subtotal, total):
        discount_amount = subtotal - total
        return discount_amount

    def get_tax_ids(self, tax, order_line_tax, instance_id, wcapi):
        if tax:
            taxes = []
            for ol_tax in order_line_tax:
                for each_record in tax:
                    tax_exist = self.env['account.tax'].search([('ks_woo_id', '=', each_record.get('rate_id')),
                                                                ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
                    try:
                        woo_tax_response = wcapi.get('taxes/%s' % each_record.get('rate_id'))
                        if woo_tax_response.status_code in [200, 201]:
                            woo_tax_record = woo_tax_response.json()
                            woo_tax_data = {
                                'name': each_record.get('rate_code') + "[Woo - " + instance_id.ks_name + ' ' + str(
                                    instance_id.id) + ']',
                                'ks_woo_id': woo_tax_record.get('id'),
                                'ks_woo_instance_id': instance_id.id,
                                'amount': float(woo_tax_record.get('rate') or 0),
                                'amount_type': 'percent',
                                'company_id': instance_id.ks_company.id,
                                'type_tax_use': 'sale',
                                'active': True
                            }
                            if tax_exist:
                                tax_exist.write(woo_tax_data)
                            else:
                                tax_exist = self.env['account.tax'].create(woo_tax_data)
                            current_tax_total = float(each_record.get('tax_total') or 0)
                            if current_tax_total and ol_tax.get('id') == each_record.get('rate_id'):
                                taxes.append(tax_exist.id)
                    except ConnectionError:
                        self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                            type='order_tax',
                                                                            operation='woo_to_odoo',
                                                                            ks_woo_id=each_record.get('rate_id'))
            return taxes if taxes else []
        else:
            return []

    def _get_product_ids(self, variation_id, product_id, json_data, instance_id, wcapi):
        _logger.info( json_data )
        if product_id:
            product_exist = self.ks_check_product_exist(variation_id, product_id, instance_id)
            if not product_exist:
                try:
                    woo_product_response = wcapi.get("products/%s" % product_id)
                    if woo_product_response.status_code in [200, 201]:
                        woo_product_record = woo_product_response.json()
                        self.env['product.template'].ks_mangae_woo_product(woo_product_record, wcapi, instance_id)
                        product_exist = self.ks_check_product_exist(variation_id, product_id, instance_id)
                except ConnectionError:
                    self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                        type='product',
                                                                        operation='woo_to_odoo',
                                                                        ks_woo_id=product_id)
        else:
            product_exist = self.env['product.product'].search([('ks_woo_instance_id', '=', instance_id.id),
                                                                ('ks_woo_id', '=', json_data.get('id')),
                                                                ('ks_woo_variant_id', '=', variation_id),
                                                                ('ks_update_false', '=', True),
                                                                ('active', '=', False),
                                                                ('default_code', '=', json_data.get('sku') )], limit=1)
            if not product_exist:
                product_exist = self.env['product.product'].create({
                    'ks_woo_id': json_data.get('id'),
                    'ks_woo_variant_id': variation_id,
                    'ks_woo_instance_id': instance_id.id,
                    'name': json_data.get('name'),
                    'price': float(json_data.get('subtotal') or 0),
                    'ks_update_false': True,
                    'ks_woo_product_type': 'simple',
                    'type': 'product',
                    'active': False
                })
                if product_exist:
                    product_exist.product_tmpl_id.active = False

        return product_exist

    def ks_check_product_exist(self, variation_id, product_id, instance_id):
        product_exist = self.env['product.product'].search([('ks_woo_instance_id', '=', instance_id.id),
                                                            ('ks_woo_id', '=', product_id),
                                                            ('ks_woo_variant_id', '=', variation_id),
                                                            ('default_code', '=', json_data.get('sku') )], limit=1)
        if not product_exist:
            product_exist = self.env['product.product'].search([('ks_woo_instance_id', '=', instance_id.id),
                                                                ('ks_woo_id', '=', product_id),
                                                                ('default_code', '=', json_data.get('sku') )], limit=1)
        return product_exist

    def _get_customer_id(self, woo_cust_id, wcapi, instance_id, invoice_address=False, shipping_address=False):
        json_data = {"billing": invoice_address,
                     "shipping": shipping_address}
        customer_data = self.env['res.partner']._ks_prepare_woo_customer_data(json_data)
        if woo_cust_id == 0:
            woo_customer_exist = self.env.ref('ks_woocommerce.ks_woo_guest_customers')
        else:
            woo_customer_exist = self.env['res.partner'].search([('ks_woo_id', '=', woo_cust_id),
                                                                 ('ks_woo_instance_id', '=', instance_id.id)], limit=1)

            if not woo_customer_exist:
                try:
                    woo_customer_response = wcapi.get("customers/%s" % woo_cust_id)
                    if woo_customer_response.status_code in [200, 201]:
                        woo_customer_record = woo_customer_response.json()
                        woo_customer_exist = self.env['res.partner'].create(
                            self.env['res.partner']._prepare_create_data(
                                self.env['res.partner']._ks_prepare_woo_customer_data(woo_customer_response.json())))
                        woo_customer_exist.ks_woo_id = woo_customer_record.get('id')
                        woo_customer_exist.ks_woo_instance_id = instance_id.id
                except ConnectionError:
                    self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                        type='customer',
                                                                        operation='woo_to_odoo',
                                                                        ks_woo_id=woo_cust_id)
        partner_id = woo_customer_exist._update_partner_details(customer_data)
        if partner_id:
            return partner_id
        return woo_customer_exist.id if woo_customer_exist else False

    def _prepare_invoice(self):
        # Override
        # For adding the sale order reference to invoices if its a WooCommerce Order
        res = super(KsSaleOrderInherit, self)._prepare_invoice()
        if self.ks_woo_id:
            res.update({"ks_woo_order_id": self.id})
        return res

    def ks_auto_import_order(self, cron_id=False):
        if not cron_id:
            if self._context.get('params'):
                cron_id = self._context.get('params').get('id')
        instance_id = self.env['ks.woocommerce.instances'].search(
            [('ks_aio_cron_id', '=', cron_id), ('ks_auto_import_order', '=', True)], limit=1)
        if instance_id.ks_instance_state == 'active':
            try:
                wcapi = instance_id.ks_api_authentication()
                if wcapi.get("").status_code in [200, 201]:
                    self.ks_sync_sale_order(wcapi, instance_id)
                    instance_id.ks_aio_cron_last_updated = fields.datetime.now()
                else:
                    self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                 ks_status='success' if wcapi.get("").status_code in [
                                                                     200,
                                                                     201] else 'failed',
                                                                 ks_type='system_status',
                                                                 ks_woo_instance_id=instance_id,
                                                                 ks_operation='odoo_to_woo',
                                                                 ks_operation_type='connection',
                                                                 response='Connection successful' if wcapi.get(
                                                                     "").status_code in [200, 201] else wcapi.get(
                                                                     "").text)
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='order',
                                                                    operation='woo_to_odoo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="Order",
                                                             operation_type="import",
                                                             instance_id=instance_id,
                                                             operation="woo_to_odoo", exception=e)
        else:
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                         ks_status='failed',
                                                         ks_type='order',
                                                         ks_woo_instance_id=instance_id,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='create',
                                                         response='Auto Import Sale Order Job: Did not Found the WooCommerce Instance' if not instance_id else
                                                         "Auto Import Sale Order Job: WooCommerce instance is not in active state to perform this operation")

    def ks_update_order_status_in_woo(self):
        for each_rec in self:
            if each_rec.ks_woo_instance_id and each_rec.ks_woo_instance_id.ks_instance_state == 'active':
                try:
                    wcapi = each_rec.ks_woo_instance_id.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        each_rec.ks_update_order_status(each_rec.ks_woo_instance_id, wcapi)
                    else:
                        self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                     ks_status='success' if wcapi.get(
                                                                         "").status_code in [
                                                                                                200,
                                                                                                201] else 'failed',
                                                                     ks_type='system_status',
                                                                     ks_woo_instance_id=each_rec.ks_woo_instance_id,
                                                                     ks_operation='odoo_to_woo',
                                                                     ks_operation_type='connection',
                                                                     response='Connection successful' if wcapi.get(
                                                                         "").status_code in [200, 201] else wcapi.get(
                                                                         "").text)
                except ConnectionError:
                    self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=each_rec.ks_woo_instance_id,
                                                                        type='order',
                                                                        operation='odoo_to_woo',
                                                                        ks_woo_id=each_rec.ks_woo_id)
                except Exception as e:
                    self.env['ks.woo.sync.log'].ks_exception_log(record=each_rec, type="order",
                                                                 operation_type="update",
                                                                 instance_id=each_rec.ks_woo_instance_id,
                                                                 operation="odoo_to_woo", exception=e)
            else:
                self.env['ks.woo.sync.log'].ks_no_instance_log(each_rec, 'coupon')

    def ks_update_order_status(self, instance_id, wcapi):
        order_records = self.env['sale.order'].search(
            [('ks_woo_instance_id', '=', instance_id.id),
             ('ks_woo_id', '!=', False)])
        if wcapi.get("").status_code in [200, 201]:
            orders = []
            for each_order in order_records:
                orders.append({
                    'id': each_order.ks_woo_id,
                    'status': each_order.ks_woo_status
                })
            try:
                woo_response = wcapi.post("orders/batch", {'update': orders})
                self.ks_batch_update_response(woo_response, instance_id)
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='order',
                                                                    operation='odoo_to_woo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="order",
                                                             operation_type="update",
                                                             instance_id=instance_id,
                                                             operation="odoo_to_woo", exception=e)
        else:
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                         ks_type='system_status',
                                                         ks_status='success' if wcapi.get("").status_code in [
                                                             200, 201] else 'failed',
                                                         ks_woo_instance_id=instance_id,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='connection',
                                                         response=str(wcapi.get("").status_code) + ': ' + eval(
                                                             wcapi.get("").text).get('message'))

    def ks_auto_update_order_status(self, cron_id=False):
        if not cron_id:
            if self._context.get('params'):
                cron_id = self._context.get('params').get('id')
        instance_id = self.env['ks.woocommerce.instances'].search([('ks_auos_cron_id', '=', cron_id)], limit=1)
        if instance_id.ks_instance_state == 'active':
            try:
                wcapi = instance_id.ks_api_authentication()
                if wcapi.get("").status_code in [200, 201]:
                    self.ks_update_order_status(instance_id, wcapi)
                    instance_id.ks_auos_cron_last_updated = fields.datetime.now()
                else:
                    self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                 ks_status='success' if wcapi.get("").status_code in [
                                                                     200,
                                                                     201] else 'failed',
                                                                 ks_type='system_status',
                                                                 ks_woo_instance_id=instance_id,
                                                                 ks_operation='odoo_to_woo',
                                                                 ks_operation_type='connection',
                                                                 response='Connection successful' if wcapi.get(
                                                                     "").status_code in [200, 201] else wcapi.get(
                                                                     "").text)
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='order',
                                                                    operation='odoo_to_woo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="order",
                                                             operation_type="update",
                                                             instance_id=instance_id,
                                                             operation="odoo_to_woo", exception=e)
        else:
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                         ks_status='failed',
                                                         ks_type='order',
                                                         ks_woo_instance_id=instance_id,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='create',
                                                         response='Auto Update Sale Order Status Job: Did not Found the WooCommerce Instance' if not instance_id else
                                                         "Auto Update Sale Order Status Job: WooCommerce instance is not in active state to perform this operation")

    def ks_batch_update_response(self, woo_response, instance):
        if woo_response.status_code in [200, 201]:
            woo_records = woo_response.json()
            for each_rec in woo_records.get('update'):
                if each_rec.get('error'):
                    ks_status = "failed"
                    ks_woo_id = each_rec.get('id')
                    response = 'The Order status update operation for Woo Id [' + str(
                        each_rec.get('id')) + '] failed due to ' + each_rec.get('error').get('message')
                else:
                    ks_status = "success"
                    ks_woo_id = each_rec.get('id')
                    response = 'The status has been successfully updated for Order with Woo Id [' + str(
                        each_rec.get('id')) + ']'

                self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=ks_woo_id,
                                                             ks_status=ks_status,
                                                             ks_type='order',
                                                             ks_woo_instance_id=instance,
                                                             ks_operation='odoo_to_woo',
                                                             ks_operation_type='batch_update',
                                                             response=response)
        else:
            ks_status = "failed"
            ks_woo_id = False
            response = 'Orders status update operation failed due to ' + eval(woo_response.text).get('message')
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=ks_woo_id,
                                                         ks_status=ks_status,
                                                         ks_type='order',
                                                         ks_woo_instance_id=instance,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='batch_update',
                                                         response=response)


class KsSaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    ks_woo_id = fields.Integer('Woocommerce Id', readonly=True)
    ks_discount_amount = fields.Float(string='Discount Amount', digits=(16, 4))

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'ks_discount_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        super(KsSaleOrderLineInherit, self)._compute_amount()
        for line in self:
            if line.ks_discount_amount:
                price = line.price_unit
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'] - line.ks_discount_amount,
                    'price_subtotal': taxes['total_excluded'] - line.ks_discount_amount,
                })
