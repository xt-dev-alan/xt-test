import json

from odoo import models, fields
from requests.exceptions import ConnectionError


class KsQueueManager(models.TransientModel):
    _name = 'ks.woo.queue.jobs'
    _description = 'This is used to Sync all the record in queues'
    _rec_name = 'ks_name'
    _order = 'id desc'

    ks_model = fields.Selection([('product_template', 'Product Template'), ('product_product', 'Product Variants'),
                                 ('sale_order', 'Sale Order'), ('customer', 'Customer'), ('coupon', 'Coupon'),
                                 ('attribute', 'Attributes'), ('tag', 'Tags'), ('category', 'Category'),
                                 ('stock', 'Stock'), ('payment_gateway', 'Payment Gateway')], string='Model')
    ks_name = fields.Char('Name')
    ks_operation = fields.Selection([('woo_to_odoo','Woo To Odoo'),('odoo_to_woo','Odoo To Woo')], string= "Operation Performed" )
    ks_type = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Operation")
    state = fields.Selection([('new', 'New'), ('progress', 'In Progress'), ('done', 'Done'), ('failed', 'Failed')],
                             string='State')
    ks_woo_id = fields.Char('WooCommerce ID')
    ks_record_id = fields.Integer('Record ID')
    ks_instance_id = fields.Many2one('ks.woocommerce.instances', 'Woo Instance')
    ks_data = fields.Text('WooCommerce Data')

    def ks_process_queue_jobs(self):
        if not self.id:
            self = self.search([('state', 'in', ['new', 'failed', 'progress'])])
        for record in self:
            wcapi = record.ks_instance_id.ks_api_authentication()
            if record.ks_model == 'product_template':
                record.state = 'progress'
                record.env.cr.commit()
                try:
                    if record.ks_operation == 'odoo_to_woo':
                        product_record = record.env['product.template'].browse(record.ks_record_id)
                        product_record.ks_update_product_to_woo()
                    else:
                        product_data = json.loads(record.ks_data)
                        record.env['product.template'].ks_mangae_woo_product(product_data, wcapi, record.ks_instance_id)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='product',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'customer':
                record.state = 'progress'
                record.env.cr.commit()
                try:
                    if record.ks_operation == 'odoo_to_woo':
                        customer_record = record.env['res.partner'].browse(record.ks_record_id)
                        customer_record.ks_update_customer_to_woo()
                    else:
                        customer_data = json.loads(record.ks_data)
                        record.env['res.partner'].ks_manage_customer_woo_data(record.ks_instance_id, customer_data)
                    record.state = 'done'
                    record.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='customer',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'tag':
                record.state = 'progress'
                record.env.cr.commit()
                try:
                    if record.ks_operation == 'odoo_to_woo':
                        tag_record = record.env['ks.woo.product.tag'].browse(record.ks_record_id)
                        tag_record.ks_update_product_tag_to_woo()
                    else:
                        product_tag_data = json.loads(record.ks_data)
                        record.env['ks.woo.product.tag'].ks_manage_product_tags(product_tag_data, record.ks_instance_id)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='tags',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'coupon':
                record.state = 'progress'
                self.env.cr.commit()
                try:
                    if record.ks_operation == 'odoo_to_woo':
                        coupon_record = record.env['ks.woo.coupon'].browse(record.ks_record_id)
                        coupon_record.ks_update_coupon_to_woo()
                    else:
                        coupons_data = json.loads(record.ks_data)
                        record.env['ks.woo.coupon'].ks_manage_coupon_woo_data(record.ks_instance_id, coupons_data)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='tags',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'payment_gateway':
                record.state = 'progress'
                record.env.cr.commit()
                try:
                    if record.ks_operation == 'odoo_to_woo':
                        payment_gateway_record = record.env['ks.woo.payment.gateway'].browse(record.ks_record_id)
                        payment_gateway_record.ks_update_coupon_to_woo()
                    else:
                        payment_gateway_data = json.loads(record.ks_data)
                        record.env['ks.woo.payment.gateway'].ks_manage_payment_gateway(record.ks_instance_id,
                                                                                       payment_gateway_data)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='tags',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'attribute':
                record.state = 'progress'
                self.env.cr.commit()
                try:
                    if record.ks_operation == 'odoo_to_woo':
                        attribute_record = record.env['product.attribute'].browse(record.ks_record_id)
                        attribute_record.ks_update_product_attribute_to_woo()
                    else:
                        product_attribute_data = json.loads(record.ks_data)
                        record.env['product.attribute'].ks_update_product_attribute_from_woo(
                            product_attribute_data, wcapi, record.ks_instance_id)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='attribute',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'category':
                record.state = 'progress'
                self.env.cr.commit()
                try:
                    if record.ks_operation == 'odoo_to_woo':
                        category_record = self.env['product.category'].browse(record.ks_record_id)
                        category_record.ks_update_product_category_to_woo()
                    else:
                        product_category_data = json.loads(record.ks_data)
                        record.env['product.category'].ks_update_category_woocommerce(
                            wcapi, record.ks_instance_id, product_category_data)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='category',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'sale_order':
                record.state = 'progress'
                sale_order_data = json.loads(record.ks_data)
                try:
                    record.env['sale.order'].ks_manage_sale_order_data(
                        sale_order_data, wcapi, record.ks_instance_id)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='order',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()
            elif record.ks_model == 'stock':
                record.state = 'progress'
                stock_data = [json.loads(record.ks_data)]
                try:
                    record.env['product.template'].ks_manage_inventory_adjustments(
                        stock_data, record.ks_instance_id, wcapi)
                    record.state = 'done'
                    self.env.cr.commit()
                except Exception as e:
                    record.state = 'failed'
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=record.ks_woo_id,
                        ks_status='failed',
                        ks_type='stock',
                        ks_woo_instance_id=record.ks_instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response=e,
                    )
                    self.env.cr.commit()

    def ks_sync_product_tag_to_queue(self, wcapi, instance_id):
        multi_api_call = True
        per_page = 100
        page = 1
        while (multi_api_call):
            try:
                woo_tag_response = wcapi.get("products/tags", params={"per_page": per_page, "page": page})
                if woo_tag_response.status_code in [200, 201]:
                    all_woo_tag_records = woo_tag_response.json()
                    vals = []
                    for product_tag in all_woo_tag_records:
                        ks_woo_id = product_tag.get('id')
                        product_tag_data = {
                            'ks_name': product_tag.get('name'),
                            'ks_model': 'tag',
                            'state': 'new',
                            'ks_type': 'import',
                            'ks_instance_id': instance_id.id,
                            'ks_woo_id': ks_woo_id,
                            'ks_operation': 'woo_to_odoo',
                            'ks_data': json.dumps(product_tag),
                        }
                        vals.append(product_tag_data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='product',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Product Tag Record has been successfully added to queue',
                    )
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='tags',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(woo_tag_response.status_code) + eval(woo_tag_response.text).get('message'),
                    )
                total_api_calls = woo_tag_response.headers._store.get('x-wp-totalpages')[1]
                remaining_api_calls = int(total_api_calls) - page
                if remaining_api_calls > 0:
                    page += 1
                else:
                    multi_api_call = False
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='tags',
                                                                    operation='woo_to_odoo')

    def ks_sync_product_woocommerce_in_queue(self, wcapi, instance_id):
        multi_api_call = True
        per_page = 100
        page = 1
        try:
            while (multi_api_call):
                woo_product_response = wcapi.get("products", params={"per_page": per_page, "page": page})
                if woo_product_response.status_code in [200, 201]:
                    woo_products_record = woo_product_response.json()
                    vals = []
                    for product_record in woo_products_record:
                        ks_woo_product_id = product_record.get('id')
                        product_data = {
                            'ks_name': product_record.get('name'),
                            'ks_model': 'product_template',
                            'state': 'new',
                            'ks_type': 'import',
                            'ks_instance_id': instance_id.id,
                            'ks_woo_id': ks_woo_product_id,
                            'ks_operation': 'woo_to_odoo',
                            'ks_data': json.dumps(product_record),
                        }
                        vals.append(product_data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='product',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Product Record has been successfully added to queue',
                    )
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='product',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(woo_product_response.status_code) + eval(woo_product_response.text).get('message'),
                    )

                total_api_calls = woo_product_response.headers._store.get('x-wp-totalpages')[1]
                remaining_api_calls = int(total_api_calls) - page
                if remaining_api_calls > 0:
                    page += 1
                else:
                    multi_api_call = False
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                type='product',
                                                                operation='woo_to_odoo')
        except Exception as e:
            self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="product",
                                                         operation_type="import",
                                                         instance_id=instance_id,
                                                         operation="woo_to_odoo", exception=e)

    def ks_sync_customer_woocommerce_in_queue(self, wcapi, instance_id):
        """
        This will Sync the customer from woo to Odoo (Create and Update the customer on Odoo).

        :param wcapi: The WooCommerce API instance
        :param instance_id: The WooCommerce instance
        :return: None
        """
        multi_api_call = True
        per_page = 100
        page = 1
        while (multi_api_call):
            try:
                customer_response = wcapi.get("customers", params={"per_page": per_page, "page": page})
                if customer_response.status_code in [200, 201]:
                    woo_all_customer_record = customer_response.json()
                    vals = []
                    for customer_record in woo_all_customer_record:
                        ks_woo_id = customer_record.get('id')
                        product_data = {
                            'ks_name': customer_record.get('first_name'),
                            'ks_model': 'customer',
                            'state': 'new',
                            'ks_type': 'import',
                            'ks_instance_id': instance_id.id,
                            'ks_woo_id': ks_woo_id,
                            'ks_operation': 'woo_to_odoo',
                            'ks_data': json.dumps(customer_record),
                        }
                        vals.append(product_data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='customer',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Customers Record has been successfully added to queue',
                    )
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='customer',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(customer_response.status_code) + eval(customer_response.text).get('message'),
                    )
                total_api_calls = customer_response.headers._store.get('x-wp-totalpages')[1]
                remaining_api_calls = int(total_api_calls) - page
                if remaining_api_calls > 0:
                    page += 1
                else:
                    multi_api_call = False
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id, type='customer',
                                                                    operation='woo_to_odoo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="customer",
                                                             operation_type="import", instance_id=instance_id,
                                                             operation="woo_to_odoo", exception=e)

    def ks_sync_product_attribute_woocommerce_to_queue(self, wcapi, instance_id):
        try:
            attribute_response = wcapi.get("products/attributes")
            if attribute_response.status_code in [200, 201]:
                all_woo_attributes_records = attribute_response.json()
                vals = []
                for attribute_record in all_woo_attributes_records:
                    ks_woo_id = attribute_record.get('id')
                    data = {
                        'ks_name': attribute_record.get('name'),
                        'ks_model': 'attribute',
                        'state': 'new',
                        'ks_type': 'import',
                        'ks_instance_id': instance_id.id,
                        'ks_woo_id': ks_woo_id,
                        'ks_operation': 'woo_to_odoo',
                        'ks_data': json.dumps(attribute_record),
                    }
                    vals.append(data)
                if vals:
                    self.create(vals)
                self.env['ks.woo.sync.log'].create_log_param(
                    ks_woo_id=False,
                    ks_status='success',
                    ks_type='attribute',
                    ks_woo_instance_id=instance_id,
                    ks_operation='woo_to_odoo',
                    ks_operation_type='create',
                    response='Attribute value has been successfully added to queue',
                )
            else:
                self.env['ks.woo.sync.log'].create_log_param(
                    ks_woo_id=False,
                    ks_status='failed',
                    ks_type='attribute',
                    ks_woo_instance_id=instance_id,
                    ks_operation='woo_to_odoo',
                    ks_operation_type='fetch',
                    response=str(attribute_response.status_code) + eval(attribute_response.text).get('message'),
                )
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id, type='attribute',
                                                                operation='woo_to_odoo')

    def ks_sync_coupon_from_woo_to_queue(self, wcapi, instance_id):
        multi_api_call = True
        per_page = 100
        page = 1
        while (multi_api_call):
            try:
                woo_coupon_response = wcapi.get("coupons", params={"per_page": per_page, "page": page})
                if woo_coupon_response.status_code in [200, 201]:
                    all_woo_coupon_records = woo_coupon_response.json()
                    vals = []
                    for coupon_record in all_woo_coupon_records:
                        ks_woo_id = coupon_record.get('id')
                        product_data = {
                            'ks_name': coupon_record.get('code'),
                            'ks_model': 'coupon',
                            'state': 'new',
                            'ks_type': 'import',
                            'ks_instance_id': instance_id.id,
                            'ks_woo_id': ks_woo_id,
                            'ks_operation': 'woo_to_odoo',
                            'ks_data': json.dumps(coupon_record),
                        }
                        vals.append(product_data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='coupon',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Coupons Record has been successfully added to queue',
                    )
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='coupon',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(woo_coupon_response.status_code) + eval(woo_coupon_response.text).get('message'),
                    )
                total_api_calls = woo_coupon_response.headers._store.get('x-wp-totalpages')[1]
                remaining_api_calls = int(total_api_calls) - page
                if remaining_api_calls > 0:
                    page += 1
                else:
                    multi_api_call = False
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='coupon',
                                                                    operation='woo_to_odoo')

    def ks_sync_payment_gateway_in_queue(self, wcapi, instance_id):
        if instance_id.ks_wc_version != 'wc/v1':
            try:
                p_g_response = wcapi.get("payment_gateways")
                if p_g_response.status_code in [200, 201]:
                    all_woo_payment_gateway = p_g_response.json()
                    vals = []
                    for gateway_record in all_woo_payment_gateway:
                        ks_woo_id = gateway_record.get('id')
                        product_data = {
                            'ks_name': gateway_record.get('title', ''),
                            'ks_model': 'payment_gateway',
                            'state': 'new',
                            'ks_type': 'import',
                            'ks_instance_id': instance_id.id,
                            'ks_woo_id': ks_woo_id,
                            'ks_operation': 'woo_to_odoo',
                            'ks_data': json.dumps(gateway_record),
                        }
                        vals.append(product_data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='payment_gateway',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Payment Gateway Record has been successfully added to queue',
                    )
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='payment_gateway',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(p_g_response.status_code) + eval(p_g_response.text).get('message'),
                    )
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='payment_gateway',
                                                                    operation='woo_to_odoo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="payment_gateway",
                                                             operation_type="import", instance_id=instance_id,
                                                             operation="woo_to_odoo", exception=e)
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='failed',
                ks_type='payment_gateway',
                ks_woo_instance_id=instance_id,
                ks_operation='woo_to_odoo',
                ks_operation_type='fetch',
                response="Payment Gateway can't be synced for the Woo Instance which has version as 2.6.x or later "
                         "because for this version individual payment gateway API route is not available."
            )

    def ks_sync_product_category_to_queue(self, wcapi, instance_id):
        try:
            multi_api_call = True
            per_page = 100
            page = 1
            while (multi_api_call):
                all_woo_category_response = wcapi.get("products/categories",
                                                      params={"per_page": per_page, "page": page})
                if all_woo_category_response.status_code in [200, 201]:
                    all_woo_category_records = all_woo_category_response.json()
                    vals = []
                    for category_record in all_woo_category_records:
                        ks_woo_id = category_record.get('id')
                        product_data = {
                            'ks_name': category_record.get('name'),
                            'ks_model': 'category',
                            'state': 'new',
                            'ks_type': 'import',
                            'ks_instance_id': instance_id.id,
                            'ks_woo_id': ks_woo_id,
                            'ks_operation': 'woo_to_odoo',
                            'ks_data': json.dumps(category_record),
                        }
                        vals.append(product_data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='category',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Product Category Record has been successfully added to queue',
                    )
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='category',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(all_woo_category_response.status_code) + eval(all_woo_category_response.text).get(
                            'message'),
                    )
                total_api_calls = all_woo_category_response.headers._store.get('x-wp-totalpages')[1]
                remaining_api_calls = int(total_api_calls) - page
                if remaining_api_calls > 0:
                    page += 1
                else:
                    multi_api_call = False
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                type='product',
                                                                operation='woo_to_odoo')
        except Exception as e:
            self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="product",
                                                         operation_type="import",
                                                         instance_id=instance_id,
                                                         operation="woo_to_odoo", exception=e)

    def ks_sync_sale_order_to_queue(self, wcapi, instance_id):
        if instance_id.ks_instance_state == 'active':
            multi_api_call = True
            per_page = 100
            page = 1
            try:
                while (multi_api_call):
                    woo_order_response = wcapi.get("orders", params={"per_page": per_page, "page": page})
                    woo_orders_record_all = woo_order_response.json()
                    vals = []
                    for sale_order_record in woo_orders_record_all:
                        if sale_order_record.get('status') in instance_id.ks_import_order_state_config.filtered(
                                lambda r: r.ks_sync is True).mapped('ks_woo_states'):
                            ks_woo_id = sale_order_record.get('id')
                            sale_order_data = {
                                'ks_name': sale_order_record.get('name'),
                                'ks_model': 'sale_order',
                                'state': 'new',
                                'ks_type': 'import',
                                'ks_instance_id': instance_id.id,
                                'ks_woo_id': ks_woo_id,
                                'ks_operation': 'woo_to_odoo',
                                'ks_data': json.dumps(sale_order_record),
                            }
                            vals.append(sale_order_data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='order',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Orders has been successfully added to queue',
                    )

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

    def ks_import_stock_woocommerce_in_queue(self, wcapi, instance_id):
        """
        This will get the woocommerce product data and update the products stock quantity on odoo

        :param wcapi: The WooCommerce API instance
        :param instance_id: The WooCommerce instance
        :return: None
        """
        multi_api_call = True
        per_page = 100
        page = 1
        product_records = []
        while (multi_api_call):
            try:
                woo_product_response = wcapi.get("products", params={"per_page": per_page, "page": page})
                if woo_product_response.status_code in [200, 201]:
                    woo_products_record = woo_product_response.json()
                    vals = []
                    for product_record in woo_products_record:
                        ks_woo_id = product_record.get('id')
                        data = {
                            'ks_name': product_record.get('name'),
                            'ks_model': 'stock',
                            'state': 'new',
                            'ks_type': 'import',
                            'ks_instance_id': instance_id.id,
                            'ks_woo_id': ks_woo_id,
                            'ks_operation': 'woo_to_odoo',
                            'ks_data': json.dumps(product_record),
                        }
                        vals.append(data)
                    if vals:
                        self.create(vals)
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='success',
                        ks_type='attribute',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='create',
                        response='Product Stock value has been successfully added to queue',
                    )
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='stock',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(woo_product_response.status_code) + eval(woo_product_response.text).get('message'),
                    )

                total_api_calls = woo_product_response.headers._store.get('x-wp-totalpages')[1]
                remaining_api_calls = int(total_api_calls) - page
                if remaining_api_calls > 0:
                    page += 1
                else:
                    multi_api_call = False
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='stock',
                                                                    operation='woo_to_odoo',
                                                                    ks_woo_id=False)

    def ks_update_product_tag_to_queue(self, tag_records, instance_id):
        """
        This will Sync the tag from Odoo to woo (Create and Update the customer on Odoo).

            :param tag_records: tag_records
            :return: None
        """
        vals = []
        for each_record in tag_records:
            product_tag_data = {
                'ks_name': each_record.ks_name,
                'ks_model': 'tag',
                'state': 'new',
                'ks_type': 'export',
                'ks_instance_id': instance_id.id,
                'ks_record_id': each_record.id,
                'ks_woo_id': each_record.ks_woo_id,
                'ks_operation': 'odoo_to_woo',
            }
            vals.append(product_tag_data)
        if vals:
            self.create(vals)
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='success',
                ks_type='tags',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='update',
                response='Product Tag Record has been successfully added to queue',
            )
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='failed',
                ks_type='tags',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='fetch',
                response='Product Tag Record has been failed to add in queue',
            )

    def ks_update_customer_woocommerce_in_queue(self, records, instance_id):
        """
        This will Sync the customer from Odoo to woo (Create and Update the customer on Odoo).

            :param records: customer_records
            :return: None
        """
        vals = []
        for each_record in records:
            product_customer_data = {
                'ks_name': each_record.display_name,
                'ks_model': 'customer',
                'state': 'new',
                'ks_type': 'export',
                'ks_instance_id': instance_id.id,
                'ks_record_id': each_record.id,
                'ks_woo_id': each_record.ks_woo_id,
                'ks_operation': 'odoo_to_woo',
            }
            vals.append(product_customer_data)
        if vals:
            self.create(vals)
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='success',
                ks_type='customer',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Customers Record has been successfully added to queue',
                )
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='failed',
                ks_type='customer',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='fetch',
                response='Customers Record has been failed to add in queue',
            )

    def ks_update_coupon_to_queue(self, records, instance_id):
        """
        This will Sync the coupon from Odoo to woo (Create and Update the customer on Odoo).

            :param records: coupon_records
            :return: None
        """
        vals = []
        for each_record in records:
            product_data = {
                'ks_name': '',
                'ks_model': 'coupon',
                'state': 'new',
                'ks_type': 'export',
                'ks_instance_id': instance_id.id,
                'ks_record_id': each_record.id,
                'ks_woo_id': each_record.ks_woo_id,
                'ks_operation': 'odoo_to_woo',
            }
            vals.append(product_data)
        if vals:
            self.create(vals)
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='success',
                ks_type='coupon',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Coupons Record has been successfully added to queue',
            )
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='failed',
                ks_type='coupon',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='fetch',
                response='Coupons Record has been failed to added in queue',
            )

    def ks_update_product_category_to_queue(self, category_records, instance_id):
        """
        This will Sync the category from Odoo to woo (Create and Update the customer on Odoo).

            :param category_records: category_records
            :return: None
        """
        vals = []
        for each_record in category_records:
            product_category_data = {
                'ks_name': each_record.name,
                'ks_model': 'category',
                'state': 'new',
                'ks_type': 'export',
                'ks_instance_id': instance_id.id,
                'ks_record_id': each_record.id,
                'ks_woo_id': each_record.ks_woo_id,
                'ks_operation': 'odoo_to_woo',
            }
            vals.append(product_category_data)
        if vals:
            self.create(vals)
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='success',
                ks_type='category',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Category Record has been successfully added to queue',
                )
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='failed',
                ks_type='Category',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Category Record has been failed to add in queue',
                )

    def ks_update_product_attribute_to_queue(self, records, instance_id):
        """
        This will Sync the category from Odoo to woo (Create and Update the customer on Odoo).

            :param records: attribute_records
            :return: None
        """
        vals = []
        for each_record in records:
            product_attribute_data = {
                'ks_name': each_record.name,
                'ks_model': 'attribute',
                'state': 'new',
                'ks_type': 'export',
                'ks_instance_id': instance_id.id,
                'ks_record_id': each_record.id,
                'ks_woo_id': each_record.ks_woo_id,
                'ks_operation': 'odoo_to_woo',
            }
            vals.append(product_attribute_data)
        if vals:
            self.create(vals)
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='success',
                ks_type='attribute',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Attribute Record has been successfully added to queue',
                )
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='failed',
                ks_type='attribute',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Attribute Record has been failed to add in queue',
                )

    def ks_update_product_to_queue(self, records, instance_id):
        """
        This will Sync the category from Odoo to woo (Create and Update the customer on Odoo).

            :param records: attribute_records
            :return: None
        """
        vals = []
        for each_record in records:
            product_data = {
                'ks_name': each_record.name,
                'ks_model': 'product_template',
                'state': 'new',
                'ks_type': 'export',
                'ks_instance_id': instance_id.id,
                'ks_record_id': each_record.id,
                'ks_woo_id': each_record.ks_woo_id,
                'ks_operation': 'odoo_to_woo',
            }
            vals.append(product_data)
        if vals:
            self.create(vals)
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='success',
                ks_type='product',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Product Record has been successfully added to queue',
                )
        else:
            self.env['ks.woo.sync.log'].create_log_param(
                ks_woo_id=False,
                ks_status='failed',
                ks_type='product',
                ks_woo_instance_id=instance_id,
                ks_operation='odoo_to_woo',
                ks_operation_type='create',
                response='Product Record has been failed to add in queue',
            )
