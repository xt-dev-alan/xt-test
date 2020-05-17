# -*- coding: utf-8 -*-
{
    'name': "Odoo WooCommerce Connector",
    'summary': """WooCommerce Connector will help you to integrate and manage your WooCommerce 
                  store in Odoo and thus resolves the need to go in Woocommerce backend to
                   handle things which can be managed from Odoo.
    """,
    'description': """
            Webhook Connector Apps
            Odoo Webhook Apps
            Best Webhook Connector Apps
            Odoo Woocommerce Connectors
            Woocommerce Connectors
            Woo commerce Connectors
            Woocommerce Apps
            Woo commerce Apps
            Woo-commerce Apps
            Best Woocommerce Apps
            Best Woo commerce Apps
            Real Time Syncing
            Import Export Data Apps
            V13 Woocommerce
            Woocommerce V13
            One Click Data Sync
            Instance Apps
            API sync Apps
            API integration
            Bidirectional Sync
            Bidirectional Apps
            Multiple Woocommerce store
            Multiple Woo store
            Woo Odoo Bridge
            Inventory Management Apps
            Update Stock Apps
            Best Woo Apps
            Best Connector Apps
            Woocommerce Bridge
            Odoo Woocommerce bridge
            Woo commerce bridge
            Auto Task Apps
            Auto Job Apps
            Woocommerce Order Cancellation
            Order Status Apps
            Order Tracking Apps
            Order Workflow Apps
            Woocommerce Order status Apps
            Connector For Woocommerce
    """,

    'author': "Ksolves India Pvt. Ltd.",
    'website': "https://www.ksolves.com/",
    'category': 'Sales',
    'version': '13.0.2.3.0',
    'application': True,
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 319.0,
    'maintainer': 'Ksolves India Pvt. Ltd.',
    'support': 'sales@ksolves.com',
    'images': ['static/description/woo_latest_banner.gif'],
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'sale_stock', 'stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/ks_security.xml',
        'security/ks_woo_commerce_model_security.xml',
        'data/ks_woo_partner_data.xml',
        'data/ks_woo_product_data.xml',
        'data/ks_job_process_cron.xml',
        'views/ks_assets.xml',
        'views/ks_woocommerce.xml',
        # 'views/ks_woo_pricelist.xml',
        'views/ks_message_wizard.xml',
        'views/ks_instance_operations_view.xml',
        'views/ks_woo_log_view.xml',
        'views/ks_woo_dashnoard_view.xml',
        'views/ks_partner.xml',
        'views/ks_product.xml',
        'views/ks_product_attribute.xml',
        'views/ks_product_category.xml',
        'views/ks_woo_product_view.xml',
        'views/ks_woo_product_tag_view.xml',
        'views/ks_woo_coupon_view.xml',
        'views/ks_woo_payment_gateways_view.xml',
        'views/ks_product_variant_price_view.xml',
        'views/ks_woo_sales_order_view.xml',
        'views/ks_woo_delivery_details.xml',
        'views/ks_woo_invoices.xml',
        'views/ks_account_invoice_view.xml',
        'views/ks_account_tax_view.xml',
        'views/ks_woo_record_mapping_view.xml',
        'views/ks_public_price_list_view.xml',
        'views/ks_queue_jobs.xml'
    ],
    'post_init_hook': 'post_install_hook',

    'external_dependencies': {
        'python': ['woocommerce', 'python-wordpress-xmlrpc', 'python-magic'],
    },
}
