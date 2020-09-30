# -*- coding: utf-8 -*-

import logging

from datetime import date

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

STATES = [
    ('draft', 'draft'), 
    ('accept', 'Accepted'), 
    ('progress', 'Progress'),
    ('close', 'Close')
]

class PawnPawn(models.Model):
    _name = 'pawn.pawn'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Pawn'

    name = fields.Char(string='Name', required=True, default=_('New') )
    date = fields.Date(string='Date', default=date.today())
    approved_date = fields.Date(string='Approved')
    order_id = fields.Many2one('sale.order', string='Order')
    user_id = fields.Many2one('res.users', string='User', default=lambda s: s.env.user)
    state = fields.Selection(STATES, default='draft')
    type = fields.Selection([('pawn', 'Pawn'), ('sale', 'Sale')], string='Type', default='pawn', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda s: s.env.company.currency_id )
    amount = fields.Monetary(string='Amount')


    partner_name = fields.Char(string='Partner Name', required=True)
    partner_vat = fields.Char(string='Partner Vat', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    street = fields.Char()
    city = fields.Char()
    phone = fields.Char()

    product_name = fields.Char(string='Product Name', required=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_description = fields.Text(string="Product Description")
    product_search_ids = fields.One2many('pawn.product.search', 'pawn_id', string='Product search')


    def _get_partner(self):
        partner = self.env['res.partner']
        partner_id = partner.search( [('vat', '=', self.partner_vat)], limit=1)
        if not partner_id:
            partner_id = partner.create(  {
                                            'name': self.partner_name, 
                                            'vat': self.partner_vat,
                                            'type': 'contact'} )
        return partner_id

    def _create_product(self):
        product = self.env['product.product']
        categ_id = self.env.ref('pawnshop.categ_empeño')
        product_id = product.create( {  'name': self.product_name, 
                                        'default_code': self.name,
                                        'barcode': self.name,
                                        'list_price': self.amount,
                                        'type': 'product',
                                        'categ_id': categ_id.id
                                    } )
        return product_id

    def action_accept(self):
        for record in self:
            partner_id = record._get_partner()
            product_id = record._create_product()
            record.write( {
                            'state': 'accept',
                            'partner_id': partner_id.id,
                            'product_id': product_id.id,
                            'approved_date': date.today(),
                            'street': partner_id.street,
                            'city': partner_id.city,
                            'phone': partner_id.phone,
                        } )
        

    def create_order(self):
        sale_order = self.env['sale.order']
        storage = self.env.ref('pawnshop.product_costo_almacenamiento')
        admin = self.env.ref('pawnshop.product_costo_administracion')
        loan = self.env.ref('pawnshop.product_interes_prestamo')
        for record in self:
            lines = [
                (0, 0, {'name': storage.name, 'product_id': storage.id,}),
                (0, 0, {'name': admin.name, 'product_id': admin.id,}),
                (0, 0, {'name': loan.name, 'product_id': loan.id,}),
                (0, 0, {'name': record.product_id.name, 'product_id': record.product_id.id})                
                ]
            order_id = sale_order.create( {'partner_id': record.partner_id.id, 'order_line': lines} )
            record.write(  {'order_id': order_id.id, 'state': 'progress'} )



    @api.onchange('street', 'city', 'phone')
    def _onchange_partner(self):
        if not self.partner_id:
            return
        self.partner_id.street = self.street
        self.partner_id.city = self.city
        self.partner_id.phone = self.phone


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pawn.pawn') or _('New')
        result = super(PawnPawn, self).create(vals)
        return result


class PawnProductSearch(models.Model):
    _name = 'pawn.product.search'
    _description = 'Pawn Product Search'

    name = fields.Char(string='Name', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda s: s.env.company.currency_id )
    attachment = fields.Binary(string='Attachment')
    amount = fields.Monetary(string='Amount', required=True)
    pawn_id = fields.Many2one('pawn.pawn', string='Pawn')




    

    