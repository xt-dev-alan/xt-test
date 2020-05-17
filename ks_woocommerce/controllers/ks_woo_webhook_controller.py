import json
import logging

from odoo import http, SUPERUSER_ID
from odoo.http import Root, HttpRequest
from odoo.http import request

_logger = logging.getLogger(__name__)


class KsWooWebhookHandler(http.Controller):
    @http.route(['/woo_hook/<int:woo_instance_id>/customer/create'], auth='public', csrf=False, methods=['POST'])
    def create_customer_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    request.env['res.partner'].sudo().ks_manage_customer_woo_data(woo_instance, data)
        return 'ok'

    @http.route(['/woo_hook/<int:woo_instance_id>/customer/update'], auth='public', csrf=False, methods=['POST'])
    def update_customer_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    request.env['res.partner'].sudo().ks_manage_customer_woo_data(woo_instance, data)
        return 'ok'

    @http.route(['/woo_hook/<int:woo_instance_id>/coupon/create'], auth='public', csrf=False, methods=['POST'])
    def create_coupon_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    wcapi = woo_instance.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        request.env['ks.woo.coupon'].sudo().ks_manage_coupon_woo_data(woo_instance, data)
                    else:
                        request.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                        ks_status='success' if wcapi.get(
                                                                            "").status_code in [200,
                                                                                                201] else 'failed',
                                                                        ks_type='system_status',
                                                                        ks_woo_instance_id=woo_instance,
                                                                        ks_operation='woo_to_odoo',
                                                                        ks_operation_type='connection',
                                                                        response=str(wcapi.get("").status_code) + ': '
                                                                                 + eval(wcapi.get("").text).get(
                                                                            'message') + '[Coupon WooHook]')
        return 'ok'

    @http.route(['/woo_hook/<int:woo_instance_id>/coupon/update'], auth='public', csrf=False, methods=['POST'])
    def update_coupon_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    wcapi = woo_instance.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        request.env['ks.woo.coupon'].sudo().ks_manage_coupon_woo_data(woo_instance, data)
                    else:
                        request.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                        ks_status='success' if wcapi.get(
                                                                            "").status_code in [200,
                                                                                                201] else 'failed',
                                                                        ks_type='system_status',
                                                                        ks_woo_instance_id=woo_instance,
                                                                        ks_operation='woo_to_odoo',
                                                                        ks_operation_type='connection',
                                                                        response=str(wcapi.get("").status_code) + ': '
                                                                                 + eval(wcapi.get("").text).get(
                                                                            'message') + '[Coupon WooHook]')
        return 'ok'

    @http.route(['/woo_hook/<int:woo_instance_id>/product/create'], auth='public', csrf=False, methods=['POST'])
    def create_product_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    wcapi = woo_instance.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        request.env['product.template'].sudo().ks_mangae_woo_product(data, wcapi, woo_instance)
                    else:
                        request.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                        ks_status='success' if wcapi.get(
                                                                            "").status_code in [200,
                                                                                                201] else 'failed',
                                                                        ks_type='system_status',
                                                                        ks_woo_instance_id=woo_instance,
                                                                        ks_operation='woo_to_odoo',
                                                                        ks_operation_type='connection',
                                                                        response=str(wcapi.get("").status_code) + ': '
                                                                                 + eval(wcapi.get("").text).get(
                                                                            'message') + '[Product WooHook]')
        return 'ok'

    @http.route(['/woo_hook/<int:woo_instance_id>/product/update'], auth='public', csrf=False, methods=['POST'])
    def update_product_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    wcapi = woo_instance.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        request.env['product.template'].sudo().ks_mangae_woo_product(data, wcapi, woo_instance)
                    else:
                        request.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                        ks_status='success' if wcapi.get(
                                                                            "").status_code in [200,
                                                                                                201] else 'failed',
                                                                        ks_type='system_status',
                                                                        ks_woo_instance_id=woo_instance,
                                                                        ks_operation='woo_to_odoo',
                                                                        ks_operation_type='connection',
                                                                        response=str(wcapi.get("").status_code) + ': '
                                                                                 + eval(wcapi.get("").text).get(
                                                                            'message') + '[Product WooHook]')
        return 'ok'

    @http.route(['/woo_hook/<int:woo_instance_id>/order/create'], auth='public', csrf=False, methods=['POST'])
    def create_order_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    wcapi = woo_instance.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        request.env['sale.order'].sudo().with_context({'uid': SUPERUSER_ID}).ks_manage_sale_order_data(data, wcapi, woo_instance)
                    else:
                        request.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                        ks_status='success' if wcapi.get(
                                                                            "").status_code in [200,
                                                                                                201] else 'failed',
                                                                        ks_type='system_status',
                                                                        ks_woo_instance_id=woo_instance,
                                                                        ks_operation='woo_to_odoo',
                                                                        ks_operation_type='connection',
                                                                        response=str(wcapi.get("").status_code) + ': '
                                                                                 + eval(wcapi.get("").text).get(
                                                                            'message') + '[Sale Order WooHook]')
        return 'ok'

    @http.route(['/woo_hook/<int:woo_instance_id>/order/update'], auth='public', csrf=False, methods=['POST'])
    def update_order_webhook(self, woo_instance_id, **post):
        if request.httprequest.data:
            self._ks_check_user()
            if woo_instance_id:
                woo_instance = request.env['ks.woocommerce.instances'].sudo().search([('id', '=', woo_instance_id)],
                                                                                     limit=1)
                data = request.httprequest.data
                if woo_instance and data:
                    wcapi = woo_instance.ks_api_authentication()
                    if wcapi.get('').status_code in [200, 201]:
                        request.env['sale.order'].sudo().with_context({'uid': SUPERUSER_ID}).ks_manage_sale_order_data(data, wcapi, woo_instance)
                    else:
                        request.env['ks.woo.sync.log'].create_log_param(ks_woo_id=False,
                                                                        ks_status='success' if wcapi.get(
                                                                            "").status_code in [200,
                                                                                                201] else 'failed',
                                                                        ks_type='system_status',
                                                                        ks_woo_instance_id=woo_instance,
                                                                        ks_operation='woo_to_odoo',
                                                                        ks_operation_type='connection',
                                                                        response=str(wcapi.get("").status_code) + ': '
                                                                                 + eval(wcapi.get("").text).get(
                                                                            'message') + '[Sale Order WooHook]')
        return 'ok'

    def _ks_check_user(self):
        if request.env.user.has_group('base.group_public'):
            request.env.user = request.env['res.users'].browse(SUPERUSER_ID)
            request.env.uid = SUPERUSER_ID
        return request.env.user


old_get_request = Root.get_request


def get_request(self, httprequest):
    is_json = httprequest.args.get('jsonp') or httprequest.mimetype in ("application/json", "application/json-rpc")
    httprequest.data = {}
    woo_hook_path = ks_match_the_url_path(httprequest.path)
    if woo_hook_path and is_json:
        request = httprequest.get_data().decode(httprequest.charset)
        httprequest.data = json.loads(request)
        return HttpRequest(httprequest)
    return old_get_request(self, httprequest)


Root.get_request = get_request


def ks_match_the_url_path(path):
    if path:
        path_list = path.split('/')
        if path_list[1] == 'woo_hook' and int(path_list[2]) and path_list[3] in ['customer', 'coupon', 'product',
                                                                                 'order'] and path_list[4] in ['create',
                                                                                                               'update']:
            return True
        else:
            return False
