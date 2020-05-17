# -*- coding: utf-8 -*-

from odoo import models

from . import ks_json_data

ADDRESS_DATA = ks_json_data.ADDRESS_DATA
PARTNER_DATA = ks_json_data.PARTNER_DATA


class PartnerConnectorSyncing(models.Model):
    _inherit = 'res.partner'

    def create_json_data(self):
        for rec in self:
            addresses = rec.address_get(['delivery', 'invoice'])
            json_data = {
                'language': rec._get_language_from_code(rec.lang) or '',
                'invoice_address': rec._get_json_address_format(addresses.get('invoice')),
                'delivery_address': rec._get_json_address_format(addresses.get('delivery')),
                'address': rec._get_json_address_format(rec.id)
            }
            partner = rec.read()[0]
            json_data.update({
                value: partner.get(key) or "" for key, value in PARTNER_DATA.items()
            })
            return json_data

    def _get_json_address_format(self, partner_id):
        partner = self.search_read([('id', '=', partner_id)])[0]
        return {
            value: partner.get(key)[0]
            if isinstance(partner.get(key), tuple) and len(partner.get(key)) == 2 else partner.get(key)
            for key, value in ADDRESS_DATA.items() if partner.get(key)
        }

    def _prepare_partner_data(self, json_data):
        partner_data = {key: json_data.get(PARTNER_DATA.get(key)) for key in PARTNER_DATA if json_data.get(key)}
        if json_data.get('language'):
            partner_data.update({
                'lang': self._get_language_code(json_data.get('language')) or False,
            })
        if json_data.get('address'):
            partner_address = self._make_address_data(json_data.get('address'))
            if partner_address:
                partner_data.update(partner_address)
        return partner_data

    def _prepare_create_data(self, json_data):
        partner_data = self._prepare_partner_data(json_data)
        other_addresses = self._add_address(json_data)
        if other_addresses:
            partner_data.update({'child_ids': other_addresses})
        return partner_data

    def _update_partner_details(self, json_data):
        address_id = False
        partner_data = self._prepare_partner_data(json_data)
        for i in ['invoice_address', 'delivery_address']:
            if json_data.get(i):
                main_add_data = json_data.get('address') or {"name": self.name if self.name else '',
                                                             "street": self.street if self.street else '',
                                                             "street2": self.street2 if self.street2 else '',
                                                             "city": self.city if self.city else '',
                                                             "state": self.state_id.code if self.state_id.code else False,
                                                             "zip": self.zip if self.zip else '',
                                                             "country": self.country_id.code if self.country_id.code else False,
                                                             "email": self.email if self.email else '',
                                                             "phone": self.phone if self.phone else ''
                                                             }
                address_data = self._match_address(main_add_data, json_data.get(i))
                if not address_data:
                    addresses = self.child_ids.filtered(lambda x: x.type == i.split('_')[0])
                    new_address = False
                    for each_add in addresses:
                        if not new_address:
                            address = {
                                "name": each_add.name if each_add.name else '',
                                "street": each_add.street if each_add.street else '',
                                "street2": each_add.street2 if each_add.street2 else '',
                                "city": each_add.city if each_add.city else '',
                                "state": each_add.state_id.code if each_add.state_id.code else False,
                                "zip": each_add.zip if each_add.zip else '',
                                "country": each_add.country_id.code if each_add.country_id.code else False,
                                "email": each_add.email if each_add.email else '',
                                "phone": each_add.phone if each_add.phone else ''
                            }
                            new_address = self._match_address(address, json_data.get(i))
                            if new_address:
                                address_id = each_add.id
                    updated_address = self._make_address_data(json_data.get(i))
                    if not new_address:
                        if updated_address:
                            updated_address['type'] = i.split('_')[0]
                            updated_address['parent_id'] = self.id
                            address_id = self.env['res.partner'].create(updated_address).id
        self.write(partner_data)
        return address_id

    # make invoice and delivery address
    def _add_address(self, json_data):
        child_addresses = []
        for i in ['invoice_address', 'delivery_address']:
            if json_data.get('address') and json_data.get(i):
                address_data = self._match_address(json_data.get('address'), json_data.get(i))
                if not address_data:
                    address_data = self._make_address_data(json_data.get(i))
                    if address_data:
                        address_data['type'] = i.split('_')[0]
                        child_addresses.append((0, 0, address_data))
        return child_addresses

    def _make_address_data(self, address):
        data = {}
        for key, value in ADDRESS_DATA.items():
            if self._fields.get(key).type != 'many2one':
                if address.get(value):
                    data[key] = address.get(value)
            else:
                if key == 'country_id':
                    country_id = self.env[self._fields.get(key).comodel_name].search([
                        ('code', '=', address.get(value))], limit=1)
                    if not country_id and address.get(value):
                        country_id = self.env[self._fields.get(key).comodel_name].create(
                            {'code': address.get(value), 'name': address.get(value)})
                    if address.get(value):
                        data[key] = country_id.id
                if key == 'state_id':
                    country_id = self.env['res.country'].search([
                        ('code', '=', address.get('country'))], limit=1)
                    if not country_id and address.get('country'):
                        country_id = self.env[self._fields.get(key).comodel_name].create(
                            {'code': address.get(value), 'name': address.get(value)})
                    state_id = self.env[self._fields.get(key).comodel_name].search([
                        ('code', '=', address.get(value)), ('country_id', '=', country_id.id)], limit=1)
                    if not state_id and address.get('state') and country_id:
                        state_id = self.env[self._fields.get(key).comodel_name].create(
                            {'code': address.get(value), 'name': address.get(value), 'country_id': country_id.id})
                    if state_id:
                        data[key] = state_id.id
        if len(data) == 1 and len(data.get('name')) == 1 and not data.get('name').strip():
            data.pop('name')
        return data

    def _match_address(self, address1, address2):
        if address1 and address2:
            if {c: address1[c] for c in address1 if c in address2 and address1[c] != address2[c]}:
                return False
        return True

    def _get_language_code(self, json_language):
        language = [language for language in self.env['res.lang'].get_installed()
                    if language[1].upper() == json_language.upper()]
        return language[0][0] if language else False

    def _get_language_from_code(self, code):
        language = [i[1] for i in self.env['res.lang'].get_installed() if i[0] == code]
        if language:
            return language[0]
