# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api
from requests.exceptions import ConnectionError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class KsProductTag(models.Model):
    _name = 'ks.woo.coupon'
    _description = 'WooCommerce Coupons'
    _rec_name = 'ks_coupon_code'

    ks_woo_id = fields.Integer('WooCommerce Id', default=0, readonly=True)
    ks_coupon_code = fields.Char('Coupon Code', required=True)
    ks_woo_instance_id = fields.Many2one('ks.woocommerce.instances', string='Instance', required=True)
    ks_company = fields.Many2one('res.company', 'Company', related='ks_woo_instance_id.ks_company')
    ks_amount = fields.Float('Amount')
    ks_discount_type = fields.Selection([('fixed_cart', 'Fixed Cart Discount'), ('percent', 'Percentage Discount'),
                                         ('fixed_product', 'Fixed Product Discount')], default="fixed_cart",
                                        string="Discount Type")
    ks_description = fields.Text(string="Description")
    ks_free_shipping = fields.Boolean(string="Allow Free Shipping")
    ks_expiry_date = fields.Date(string="Expiry Date")
    ks_minimum_amount = fields.Float(string='Minimum Spend')
    ks_maximum_amount = fields.Float(string='Maximum Spend')
    ks_individual_use = fields.Boolean(string='Individual Use')
    ks_exclude_sale_items = fields.Boolean(string='Exclude Sale Items')
    ks_allowed_email = fields.Char(string="Allowed emails")
    ks_include_product_ids = fields.Many2many("product.product", 'ks_woo_product_include_product_product_rel',
                                              'product_product_id', 'ks_include_product_ids_id', string="Products",
                                              domain="[('ks_woo_id', '!=', False), ('ks_woo_instance_id', '=', ks_woo_instance_id)]")
    ks_exclude_product_ids = fields.Many2many("product.product", 'ks_woo_product_exclude_product_product_rel',
                                              'product_product_id', 'ks_exclude_product_ids_id', string="Exclude Products",
                                              domain="[('ks_woo_id', '!=', False), ('ks_woo_instance_id', '=', ks_woo_instance_id)]")
    ks_include_categories = fields.Many2many("product.category", 'ks_woo_coupon_include_product_category_rel',
                                             'product_category_id', 'ks_include_categories_id',
                                             string="Product Categories",
                                             domain="[('ks_woo_id', '!=', False), ('ks_woo_instance_id', '=', ks_woo_instance_id)]")
    ks_exclude_categories = fields.Many2many("product.category", 'ks_woo_coupon_exclude_product_category_rel',
                                             'product_category_id', 'ks_exclude_categories_id',
                                             string="Exclude Product Categories",
                                             domain="[('ks_woo_id', '!=', False), ('ks_woo_instance_id', '=', ks_woo_instance_id)]")
    ks_usage_limit = fields.Integer(string="Usage limit per coupon")
    ks_usage_limit_per_user = fields.Integer(string="Usage limit per user")
    ks_limit_usage_to_x_items = fields.Integer(string="Limit usage to X items")
    ks_date_created = fields.Datetime('Created On',
                                      readonly=True,
                                      help="Created On: Date on which the WooCommerce Coupon has been created")
    ks_date_updated = fields.Datetime('Updated On',
                                      readonly=True,
                                      help="Updated On: Date on which the WooCommerce Coupon has been last updated")
    ks_export_in_woo = fields.Boolean('Exported in woo', readonly=True, compute='_compute_export_in_woo', store=True)


    @api.depends('ks_woo_id')
    def _compute_export_in_woo(self):
        for rec in self:
            rec.ks_export_in_woo = bool(rec.ks_woo_id)
    #Added to queue
    def ks_update_coupon_to_woo(self):
        for each_record in self:
            json_data = self._ks_prepare_odoo_coupon_data(each_record)
            if each_record.ks_woo_instance_id and each_record.ks_woo_instance_id.ks_instance_state == 'active':
                try:
                    wcapi = each_record.ks_woo_instance_id.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        if each_record.ks_woo_id:
                            record_exist = wcapi.get("coupons/%s" % each_record.ks_woo_id)
                            if record_exist.status_code == 404:
                                self.ks_create_coupon_on_woo(wcapi, json_data, each_record)
                            else:
                                self.ks_update_coupon_on_woo(wcapi, json_data, each_record)
                        else:
                            self.ks_create_coupon_on_woo(wcapi, json_data, each_record)
                    else:
                        self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                     ks_status='success' if wcapi.get("").status_code in [200,
                                                                                                                          201] else 'failed',
                                                                     ks_type='system_status',
                                                                     ks_woo_instance_id=each_record.ks_woo_instance_id,
                                                                     ks_operation='odoo_to_woo',
                                                                     ks_operation_type='connection',
                                                                     response='Connection successful' if wcapi.get("").status_code in [200, 201] else wcapi.get("").text)
                except ConnectionError:
                    self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=each_record.ks_woo_instance_id,
                                                                        type='coupon',
                                                                        operation='odoo_to_woo',
                                                                        ks_woo_id=each_record.ks_woo_id)
                except Exception as e:
                    self.env['ks.woo.sync.log'].ks_exception_log(record=each_record, type="coupon",
                                                                 operation_type="create" if each_record.ks_woo_id else "update",
                                                                 instance_id=each_record.ks_woo_instance_id,
                                                                 operation="odoo_to_woo", exception=e)
            else:
                self.env['ks.woo.sync.log'].ks_no_instance_log(each_record, 'coupon')

    def ks_update_coupon_on_woo(self, wcapi, json_data, each_record):
        try:
            woo_coupon_response = wcapi.put("coupons/%s" % each_record.ks_woo_id, json_data)
            if woo_coupon_response.status_code in [200, 201]:
                status = 'success'
            else:
                status = 'failed'
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=each_record.ks_woo_id,
                                                         ks_status=status,
                                                         ks_type='coupon',
                                                         ks_woo_instance_id=each_record.ks_woo_instance_id,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='update',
                                                         response='Coupon [' + each_record.ks_coupon_code + '] has been succesfully updated' if status == 'success' else 'The update operation failed for Coupon [' + each_record.ks_coupon_code + '] due to ' + eval(woo_coupon_response.text).get('message'))
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=each_record.ks_woo_instance_id,
                                                                type='coupon',
                                                                operation='odoo_to_woo',
                                                                ks_woo_id=each_record.ks_woo_id)

    def ks_create_coupon_on_woo(self, wcapi, json_data, each_record):
        try:
            woo_coupon_response = wcapi.post("coupons", json_data)
            ks_woo_id = False
            if woo_coupon_response.status_code in [200, 201]:
                woo_coupon_data = woo_coupon_response.json()
                self.env['ks.woocommerce.instances'].ks_store_record_after_export(each_record, woo_coupon_data)
                ks_woo_id = woo_coupon_data.get('id')
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=ks_woo_id,
                                                         ks_status='success' if woo_coupon_response.status_code in [200,
                                                                                                              201] else 'failed',
                                                         ks_type='coupon',
                                                         ks_woo_instance_id=each_record.ks_woo_instance_id,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='create',
                                                         response='Coupon [' + each_record.ks_coupon_code + '] has been succesfully exported ' if woo_coupon_response.status_code in [200,
                                                                                                              201] else 'The export operation failed for Coupon [' + each_record.ks_coupon_code + '] due to ' + eval(woo_coupon_response.text).get('message'))
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=each_record.ks_woo_instance_id,
                                                                type='coupon',
                                                                operation='odoo_to_woo')

    @api.model
    def ks_update_coupon_to_odoo(self):
        instance_id = self.env['ks.woocommerce.instances'].search([('id', '=', self.ks_woo_instance_id.id)], limit=1)
        if instance_id.ks_instance_state == 'active':
            try:
                wcapi = self.ks_woo_instance_id.ks_api_authentication()
                if wcapi.get("").status_code in [200, 201]:
                    woo_coupon_response = wcapi.get("coupons/%s" % self.ks_woo_id)
                    if woo_coupon_response.status_code in [200, 201]:
                        self.ks_manage_coupon_woo_data(instance_id, woo_coupon_response.json())
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
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='product',
                                                                    operation='woo_to_odoo')
        else:
            return self.env['ks.message.wizard'].ks_pop_up_message(names='Error', message='The instance must be in '
                                                                                          'active state to perform '
                                                                                          'the operations')

    @api.model
    def ks_sync_coupon_from_woo(self, wcapi, instance_id):
        multi_api_call = True
        per_page = 100
        page = 1
        while (multi_api_call):
            try:
                woo_coupon_response = wcapi.get("coupons", params={"per_page": per_page, "page": page})
                if woo_coupon_response.status_code in [200, 201]:
                    all_woo_coupon_records = woo_coupon_response.json()
                    for each_record in all_woo_coupon_records:
                        self.ks_manage_coupon_woo_data(instance_id, each_record)
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
                                                                    type='product',
                                                                    operation='woo_to_odoo')

    def ks_manage_coupon_woo_data(self, instance_id, json_data):
        coupon_exist_in_odoo = self.search([('ks_woo_id', '=', json_data.get('id')),
                                            ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
        woo_formated_data = self._ks_prepare_woo_coupon_data(json_data, instance_id)
        if coupon_exist_in_odoo:
            coupon_exist_in_odoo.write(woo_formated_data)
            ks_operation_type = 'update'
        else:
            coupon_exist_in_odoo = self.create(woo_formated_data)
            ks_operation_type = 'create'
        self.env['ks.woo.sync.log'].create_log_param(
            ks_woo_id=json_data.get('id'),
            ks_status='success',
            ks_type='coupon',
            ks_woo_instance_id=instance_id,
            ks_operation='woo_to_odoo',
            ks_operation_type=ks_operation_type,
            response='Coupon [' + coupon_exist_in_odoo.ks_coupon_code + '] has been succesfully created' if ks_operation_type == 'create' else 'Coupon [' + coupon_exist_in_odoo.ks_coupon_code + '] has been succesfully updated',
        )

    def _ks_prepare_woo_coupon_data(self, json_data, instance_id):
        data = {
                  "ks_woo_id": json_data.get('id') or '',
                  "ks_coupon_code": json_data.get('code') or '',
                  "ks_amount": float(json_data.get('amount') or 0),
                  "ks_discount_type": json_data.get('discount_type') or '',
                  "ks_description": json_data.get('description') or '',
                  "ks_expiry_date": json_data.get('date_expires') or json_data.get('expiry_date') or False,
                  "ks_individual_use": json_data.get('individual_use'),
                  "ks_include_product_ids": self.ks_find_woo_product(json_data.get('product_ids') or '', instance_id),
                  "ks_exclude_product_ids": self.ks_find_woo_product(json_data.get('excluded_product_ids') or json_data.get('exclude_product_ids') or '',
                                                                     instance_id),
                  "ks_usage_limit": json_data.get('usage_limit') or '',
                  "ks_usage_limit_per_user": json_data.get('usage_limit_per_user') or '',
                  "ks_limit_usage_to_x_items": json_data.get('limit_usage_to_x_items') or '',
                  "ks_free_shipping": json_data.get('free_shipping'),
                  "ks_include_categories": self.ks_find_woo_category(json_data.get('product_categories') or [],
                                                                     instance_id),
                  "ks_exclude_categories": self.ks_find_woo_category(json_data.get('excluded_product_categories') or [],
                                                                     instance_id),
                  "ks_exclude_sale_items": json_data.get('exclude_sale_items') or '',
                  "ks_minimum_amount": float(json_data.get('minimum_amount') or 0),
                  "ks_maximum_amount": float(json_data.get('maximum_amount') or 0),
                  "ks_allowed_email": ",".join(json_data.get('email_restrictions')),
                  "ks_woo_instance_id": instance_id.id,
                  "ks_date_updated": datetime.strptime((json_data.get('date_modified')).replace('T',' '),
                                                                                 DEFAULT_SERVER_DATETIME_FORMAT) if json_data.get('date_modified') else False,
                  "ks_date_created": datetime.strptime((json_data.get('date_created')).replace('T',' '),
                                                                                              DEFAULT_SERVER_DATETIME_FORMAT) if json_data.get('date_created') else False
        }
        return data

    def ks_find_woo_category(self, list_of_w_ids, instance_id):
        if list_of_w_ids:
            list_of_ids = []
            for w_id in list_of_w_ids:
                category_exist = self.env['product.category'].search([('ks_woo_id', '=', w_id),
                                                                      ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
                if category_exist:
                    list_of_ids.append(category_exist.id)
                else:
                    try:
                        wcapi = instance_id.ks_api_authentication()
                        if wcapi.get("").status_code in [200, 201]:
                            woo_category_response = wcapi.get("products/categories/%s" % w_id)
                            if woo_category_response.status_code in [200, 201]:
                                woo_category_records = woo_category_response.json()
                                category = self.env['product.category'].ks_update_category_woocommerce(wcapi, instance_id, woo_category_records)
                                list_of_ids.append(category.id)
                            else:
                                self.env['ks.woo.sync.log'].create_log_param(
                                    ks_woo_id=w_id,
                                    ks_status='failed',
                                    ks_type='category',
                                    ks_woo_instance_id=instance_id,
                                    ks_operation='woo_to_odoo',
                                    ks_operation_type='fetch',
                                    response=str(woo_category_response.status_code) + eval(
                                        woo_category_response.text).get('message'),
                                )
                        else:
                            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                         ks_status='success' if wcapi.get(
                                                                             "").status_code in [200,
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
                                                                            type='category',
                                                                            ks_operation_type='import',
                                                                            operation='woo_to_odoo')
            return [(6, 0, list_of_ids)]

    def ks_find_woo_product(self, list_of_w_ids, instance_id):
        if list_of_w_ids:
            list_of_ids = []
            for w_id in list_of_w_ids:
                product_exist = self.ks_search_product(w_id, instance_id)
                if product_exist:
                    list_of_ids.append(product_exist.id)
                else:
                    try:
                        wcapi = instance_id.ks_api_authentication()
                        if wcapi.get("").status_code in [200, 201]:
                            woo_product_response = wcapi.get("products/%s" % w_id)
                            if woo_product_response.status_code in [200, 201]:
                                woo_product_records = woo_product_response.json()
                                if woo_product_records.get('parent_id') != 0:
                                    woo_prnt_product_response = wcapi.get("products/%s" % woo_product_records.get('parent_id'))
                                    if woo_prnt_product_response.status_code in [200, 201]:
                                        woo_product_records = woo_prnt_product_response.json()
                                    else:
                                        self.env['ks.woo.sync.log'].create_log_param(
                                            ks_woo_id=w_id,
                                            ks_status='failed',
                                            ks_type='product',
                                            ks_woo_instance_id=instance_id,
                                            ks_operation='woo_to_odoo',
                                            ks_operation_type='fetch',
                                            response=str(woo_product_response.status_code) + eval(
                                                woo_product_response.text).get('message'),
                                        )
                                self.env['product.template'].ks_mangae_woo_product(woo_product_records, wcapi, instance_id)
                                product_exist = self.ks_search_product(w_id, instance_id)
                                if product_exist:
                                    list_of_ids.append(product_exist.id)
                            else:
                                self.env['ks.woo.sync.log'].create_log_param(
                                    ks_woo_id=w_id,
                                    ks_status='failed',
                                    ks_type='product',
                                    ks_woo_instance_id=instance_id,
                                    ks_operation='woo_to_odoo',
                                    ks_operation_type='fetch',
                                    response=str(woo_product_response.status_code) + eval(
                                        woo_product_response.text).get('message'),
                                )
                        else:
                            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                         ks_status='success' if wcapi.get(
                                                                             "").status_code in [200,
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
                                                                            type='product',
                                                                            operation='woo_to_odoo',
                                                                            ks_woo_id=w_id)
            return [(6, 0, list_of_ids)]

    def ks_search_product(self, w_id, instance_id):
        product_exist = self.env['product.template'].search([('ks_woo_id', '=', w_id),
                                                             ('ks_woo_instance_id', '=', instance_id.id)],
                                                            limit=1).product_variant_id
        if not product_exist:
            product_exist = self.env['product.product'].search([('ks_woo_variant_id', '=', w_id),
                                                                ('ks_woo_instance_id', '=', instance_id.id)],
                                                               limit=1)
        return product_exist

    def _ks_prepare_odoo_coupon_data(self, record):
        data = {
                  "code": record.ks_coupon_code,
                  "amount": str(record.ks_amount),
                  "discount_type": record.ks_discount_type,
                  "description": record.ks_description or '',
                  "date_expires": record.ks_expiry_date.strftime("%Y-%m-%dT%H:%M:%S") if record.ks_expiry_date else '',
                  "individual_use": record.ks_individual_use,
                  "product_ids": self.ks_find_woo_product_ids(record.ks_include_product_ids),
                  "excluded_product_ids": self.ks_find_woo_product_ids(record.ks_exclude_product_ids),
                  "usage_limit": record.ks_usage_limit,
                  "usage_limit_per_user": record.ks_usage_limit_per_user,
                  "limit_usage_to_x_items": record.ks_limit_usage_to_x_items,
                  "free_shipping": record.ks_free_shipping,
                  "product_categories": record.ks_include_categories.mapped('ks_woo_id'),
                  "excluded_product_categories": record.ks_exclude_categories.mapped('ks_woo_id'),
                  "exclude_sale_items": record.ks_exclude_sale_items,
                  "minimum_amount": str(record.ks_minimum_amount),
                  "maximum_amount": str(record.ks_maximum_amount),
                  "email_restrictions": list(record.ks_allowed_email.split(",")) if record.ks_allowed_email else ''
        }
        return data

    def ks_find_woo_product_ids(self, product_records):
        product_ids = []
        for rec in product_records:
            if rec.ks_woo_variant_id:
                product_ids.append(rec.ks_woo_variant_id)
            else:
                product_ids.append(rec.ks_woo_id)
        return product_ids






