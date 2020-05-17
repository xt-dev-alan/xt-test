# -*- coding: utf-8 -*-

from odoo import models, fields, api
from requests.exceptions import ConnectionError


class KsProductCategoryInherit(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin', 'product.category']
    _name = 'product.category'

    ks_woo_id = fields.Integer('Woo Id', track_visibility='onchange',
                               readonly=True, default=0,
                               help="""Woo Id: Unique WooCommerce resource id for the product category on the specified 
                                               WooCommerce Instance""")
    ks_slug = fields.Char('Slug')
    ks_woo_description = fields.Text('Woo Description')
    ks_export_in_woo = fields.Boolean('Exported in Woo',
                                      readonly=True,
                                      store=True,
                                      compute='_ks_compute_export_in_woo',
                                      help="""Exported in Woo: If enabled, the product is synced with the specified 
                                                    WooCommerce Instance""")
    ks_woo_instance_id = fields.Many2one('ks.woocommerce.instances', track_visibility='onchange',
                                         string='Woo Instance',
                                         help="""WooCommerce Instance: Ths instance of woocomerce to which this 
                                                         category belongs to.""")

    @api.depends('ks_woo_id')
    def _ks_compute_export_in_woo(self):
        """
        To show the product category are exported in woo
        :return: None
        """
        for rec in self:
            rec.ks_export_in_woo = bool(rec.ks_woo_id)

    def ks_sync_product_category_woocommerce(self, wcapi, instance_id):
        """
        Sync the product category and its values from woo to Odoo
        :param wcapi:
        :param instance_id:
        :return: None
        """
        try:
            multi_api_call = True
            per_page = 100
            page = 1
            while (multi_api_call):
                all_woo_category_response = wcapi.get("products/categories", params={"per_page": per_page, "page": page})
                if all_woo_category_response.status_code in [200, 201]:
                    all_woo_category_records = all_woo_category_response.json()
                    for each_record in all_woo_category_records:
                        self.ks_update_category_woocommerce(wcapi, instance_id, each_record)
                else:
                    self.env['ks.woo.sync.log'].create_log_param(
                        ks_woo_id=False,
                        ks_status='failed',
                        ks_type='category',
                        ks_woo_instance_id=instance_id,
                        ks_operation='woo_to_odoo',
                        ks_operation_type='fetch',
                        response=str(all_woo_category_response.status_code) + eval(all_woo_category_response.text).get('message'),
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

    def _get_parent_categ(self, wcapi, instance_id, category_record):
        try:
            parent_id = category_record.get('parent')
            if parent_id != 0:
                parent_categ_id = self.env['product.category'].search([('ks_woo_id', '=', parent_id)], limit=1)
                if not parent_categ_id:
                    parent_response = wcapi.get("products/categories/%s" % parent_id)
                    if parent_response.status_code in [200, 201]:
                        parent_record = parent_response.json()
                        if parent_id != 0:
                            self._get_parent_categ(wcapi, instance_id, parent_record)
                        return self.create(self._prepare_woo_product_category_data(parent_record, instance_id))
                    else:
                        self.env['ks.woo.sync.log'].create_log_param(
                            ks_woo_id=parent_id,
                            ks_status='failed',
                            ks_type='category',
                            ks_woo_instance_id=instance_id,
                            ks_operation='woo_to_odoo',
                            ks_operation_type='fetch',
                            response=str(parent_response.status_code) + eval(parent_response.text).get('message') + '[Parent Category]',
                        )
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                type='category',
                                                                operation='woo_to_odoo',
                                                                ks_woo_id=category_record.get('parent'))

    def ks_get_parent_path(self):
        parent_id_get = self.parent_id
        parent_id_list = []
        while parent_id_get.id:
            # if each_record._fields.get('parent_id'):
            parent_id_list.append(str(parent_id_get.id))
            parent_id_get = parent_id_get.parent_id
        parent_id_list.reverse()
        parent_id_list.append(str(self.id))

        return parent_id_list

    @api.model
    def ks_update_product_category_to_odoo(self):
        """
        Sync the product category and its values from woo to Odoo
        :param wcapi:
        :param instance_id:
        :return: None
        """
        instance_id = self.env['ks.woocommerce.instances'].search([('id', '=', self.ks_woo_instance_id.id)], limit=1)
        if instance_id.ks_instance_state == 'active':
            try:
                wcapi = self.ks_woo_instance_id.ks_api_authentication()
                if wcapi.get("").status_code in [200, 201]:
                    all_woo_category_response = wcapi.get("products/categories/%s" % self.ks_woo_id)
                    if all_woo_category_response.status_code in [200, 201]:
                        self.ks_update_category_woocommerce(wcapi, instance_id, all_woo_category_response.json())
                    else:
                        self.env['ks.woo.sync.log'].create_log_param(
                            ks_woo_id=False,
                            ks_status='failed',
                            ks_type='category',
                            ks_woo_instance_id=instance_id,
                            ks_operation='woo_to_odoo',
                            ks_operation_type='fetch',
                            response=str(all_woo_category_response.status_code) + eval(all_woo_category_response.text).get('message'),
                        )
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=instance_id,
                                                                    type='product',
                                                                    operation='woo_to_odoo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=False, type="product",
                                                             operation_type="import",
                                                             instance_id=instance_id,
                                                             operation="woo_to_odoo", exception=e)
        else:
            return self.env['ks.message.wizard'].ks_pop_up_message(names='Error', message='The instance must be in '
                                                                                          'active state to perform '
                                                                                          'the operations')

    @api.model
    def ks_update_product_category_to_woo(self):
        """
        This will update the record in Odoo to Woo.
        :return: None
        """
        for each_record in self:
            try:
                parent_path_ids = each_record.parent_path.split('/')
                if each_record.ks_woo_instance_id and each_record.ks_woo_instance_id.ks_instance_state == 'active':
                    for parent_id in parent_path_ids:
                        if parent_id:
                            current_record = each_record.search([('id', '=', parent_id)], limit=1)
                            wcapi = each_record.ks_woo_instance_id.ks_api_authentication()
                            if wcapi.get('').status_code in [200, 201]:
                                category_data = each_record._prepare_odoo_product_category_data(current_record)
                                if current_record.ks_woo_id:
                                    record_exist_status = wcapi.get("products/categories/%s" % current_record.ks_woo_id)
                                    if record_exist_status.status_code == 404:
                                        each_record.create_category_on_woo(wcapi, current_record, category_data)
                                    else:
                                        each_record.update_category_on_woo(wcapi, current_record, category_data)
                                else:
                                    each_record.create_category_on_woo(wcapi, current_record, category_data)
                            else:
                                self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                             ks_status='success' if wcapi.get(
                                                                                 "").status_code in [200,
                                                                                                     201] else 'failed',
                                                                             ks_type='system_status',
                                                                             ks_woo_instance_id=each_record.ks_woo_instance_id,
                                                                             ks_operation='odoo_to_woo',
                                                                             ks_operation_type='connection',
                                                                             response='Connection successful' if wcapi.get("").status_code in [200, 201] else wcapi.get("").text)
                else:
                    self.env['ks.woo.sync.log'].ks_no_instance_log(each_record, 'category')
            except ConnectionError:
                self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=each_record.ks_woo_instance_id,
                                                                    type='category',
                                                                    operation='odoo_to_woo')
            except Exception as e:
                self.env['ks.woo.sync.log'].ks_exception_log(record=each_record, type="category",
                                                             operation_type="create" if each_record.ks_woo_id else "update",
                                                             instance_id=each_record.ks_woo_instance_id,
                                                             operation="odoo_to_woo", exception=e)

    def update_category_on_woo(self, wcapi, current_record, category_data):
        try:
            woo_categ_response = wcapi.put("products/categories/%s" % current_record.ks_woo_id, category_data)
            if woo_categ_response.status_code in [200, 201]:
                status = 'success'
            else:
                status = 'failed'
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=current_record.ks_woo_id,
                                                         ks_status=status,
                                                         ks_type='category',
                                                         ks_woo_instance_id=current_record.ks_woo_instance_id,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='update',
                                                         response='Category [' + current_record.name + '] has been succesfully updated' if status == 'success' else 'The update operation failed for Category [' + current_record.name + '] due to ' + eval(
                                                             woo_categ_response.text).get('message'))
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=current_record.ks_woo_instance_id,
                                                                type='category',
                                                                operation='odoo_to_woo',
                                                                ks_woo_id=current_record.ks_woo_id)

    def create_category_on_woo(self, wcapi, current_record, category_data):
        """
        Will create Category in WooCommerce.

        :param current_record: Odoo product.category record
        :param category_data: Category json data
        :return: THe category record
        """
        try:
            woo_category_response = wcapi.post("products/categories", category_data)
            ks_woo_id = False
            if woo_category_response.status_code in [200, 201]:
                woo_category_data = woo_category_response.json()
                current_record.ks_woo_id = ks_woo_id = woo_category_data.get('id')
                current_record.ks_slug = woo_category_data.get('slug')
            self.env['ks.woo.sync.log'].create_log_param(ks_woo_id=ks_woo_id,
                                                         ks_status='success' if woo_category_response.status_code in [200,
                                                                                                              201] else 'failed',
                                                         ks_type='category',
                                                         ks_woo_instance_id=current_record.ks_woo_instance_id,
                                                         ks_operation='odoo_to_woo',
                                                         ks_operation_type='create',
                                                         response='Category [' + current_record.name + '] has been succesfully exported ' if woo_category_response.status_code in [
                                                             200,
                                                             201] else 'The export operation failed for Category [' + current_record.name + '] due to ' + eval(
                                                             woo_category_response.text).get('message'))
            if woo_category_response.status_code in [200, 201]:
                return current_record
        except ConnectionError:
            self.env['ks.woo.sync.log'].ks_connection_error_log(instance_id=current_record.ks_woo_instance_id,
                                                                type='category',
                                                                operation='odoo_to_woo')

    def ks_update_category_woocommerce(self, wcapi, instance_id, category_record):
        category_exist_in_odoo = self.search([('ks_woo_id', '=', category_record.get('id')),
                                              ('ks_woo_instance_id', '=', instance_id.id)], limit=1)
        if category_record.get('parent') != 0:
            self._get_parent_categ(wcapi, instance_id, category_record)
        woo_formated_data = self._prepare_woo_product_category_data(category_record, instance_id)
        if category_exist_in_odoo:
            category_exist_in_odoo.write(woo_formated_data)
            ks_operation_type = 'update'
        else:
            category_exist_in_odoo = self.create(woo_formated_data)
            ks_operation_type = 'create'
        self.env['ks.woo.sync.log'].create_log_param(
            ks_woo_id=category_exist_in_odoo.ks_woo_id,
            ks_status='success',
            ks_type='category',
            ks_woo_instance_id=instance_id,
            ks_operation='woo_to_odoo',
            ks_operation_type=ks_operation_type,
            response='Category [' + category_exist_in_odoo.name + '] has been succesfully created' if ks_operation_type == 'create' else 'Category [' + category_exist_in_odoo.name + '] has been succesfully updated',
        )
        return category_exist_in_odoo

    def update_category_on_odoo(self, json_data, instance_id, wcapi):
        if json_data:
            odoo_categ_ids = []
            for each_record in json_data:
                odoo_categ_ids.append(self.ks_update_category_woocommerce(wcapi, instance_id, each_record).id)
            return odoo_categ_ids

    def _prepare_woo_product_category_data(self, json_data, instance_id):
        data = {
            "name": json_data.get('name'),
            "ks_slug": json_data.get('slug') or '',
            "ks_woo_id": json_data.get('id'),
            "ks_woo_instance_id": instance_id.id,
            "ks_woo_description": json_data.get("description") or ''
        }
        if json_data.get('parent'):
            data.update({"parent_id": self.search([('ks_woo_id', '=', json_data.get('parent')),
                                                   ('ks_woo_instance_id', '=', instance_id.id)], limit=1).id})
        return data

    def _prepare_odoo_product_category_data(self, each_record):
        data = {
            "name": each_record.name if each_record.name else '',
            "slug": each_record.ks_slug if each_record.ks_slug else '',
            "parent": each_record.parent_id.ks_woo_id if each_record.parent_id.ks_woo_id else 0,
            "description": each_record.ks_woo_description if each_record.ks_woo_description else ''
        }
        return data
