import base64
import logging
import magic
import mimetypes
import werkzeug.wrappers
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class KsWooImageHandler(http.Controller):
    @http.route(['/ks_woo_image/<int:product_template_id>/<int:product_image_id>/<string:image>'], auth='public',
                csrf=False, methods=['GET', 'POST'], type='http')
    def create_woo_public_image_url(self, product_template_id=False, product_image_id=False, image=False, **post):
        response = werkzeug.wrappers.Response()
        if product_image_id and product_template_id and image:
            product_template = request.env['product.template'].sudo().search([('id', '=', product_template_id)])
            if product_template.ks_product_image_ids:
                product_image_record = product_template.ks_product_image_ids.search([('id', '=', product_image_id)])
                if product_image_record.ks_image:
                    decode_image = base64.b64decode(product_image_record.ks_image)
                    response.data = decode_image
                    response.mimetype = self._ks_find_mimetype(product_image_record.ks_file_name, decode_image)
                else:
                    _logger.warning('[WooCommerce] Product image not found on this URL')
            else:
                _logger.warning('[WooCommerce] Product image not found on this URL')
        return response

    def _ks_find_mimetype(self, filename, decode_image):
        mime_type = mimetypes.guess_type(filename)
        image_mimetype = mime_type[0]
        if not image_mimetype:
            if decode_image:
                image_mimetype = magic.from_buffer(decode_image, mime=True)
            else:
                image_mimetype = 'image/png'
        return image_mimetype
