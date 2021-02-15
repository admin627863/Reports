# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from woocommerce import API
from frappe.model.document import Document

class WordpressIntegration(Document):
	pass
@frappe.whitelist()
def create_product():
	wcapi = API(
	url="http://139.59.16.219/",
	consumer_key="ck_14851e3cda5ca726da3b009d3daaa88aeb077a36",
	consumer_secret="cs_18f579a7164a006fe777e4c4d3ad2dcfba46abe9",
	wp_api=True,
	version="wc/v3"
	)
	l1=[]
	list_all_woo=wcapi.get("products").json()
	items=frappe.db.sql('''select * from `tabItem` where default_warehouse="WooCommerce - ET" ''',as_dict=1)
	frappe.msgprint(str(items))
	for prods in list_all_woo:
		l1.append(prods['name'])
	data={}
	#frappe.msgprint(str(l1))
	for item in items:
		if not item.woocommerce_id:
			#frappe.msgprint(str(item.woocommerce_id))
			if not item['item_name'] in l1:
				data['name']=item.name
				data['type']="simple"
				data['regular_price']=str(item.standard_rate)
				data['description']=item.description
			#data['images']=[{"src":str(item.image)}]
				data['manage_stock']=True
			#frappe.msgprint(str(data))
				response=wcapi.post("products", data).json()
				doc=frappe.get_doc("Item",item.name)
			#frappe.msgprint(str(doc))
				stock_item=frappe.db.set_value("Item",item.name,"woocommerce_id",response["id"])
				frappe.db.set_value("Item",item.name,"item_code",f"woocommerce - {response['id']}")
			#frappe.msgprint(str(stock_item))
	#update_products()
@frappe.whitelist()
def update_products():
	wcapi = API(
	url="http://139.59.16.219/",
	consumer_key="ck_14851e3cda5ca726da3b009d3daaa88aeb077a36",
	consumer_secret="cs_18f579a7164a006fe777e4c4d3ad2dcfba46abe9",
	wp_api=True,
	version="wc/v3"
	)
	woo_prod={}
	list_all_woo=wcapi.get("products").json()
	#frappe.msgprint(str(list_all_woo))
	data={}
	for item_name in list_all_woo:
		item=frappe.db.sql('''select * from `tabItem` where item_name=%(item)s and default_warehouse="WooCommerce - ET" ''',
				{"item":item_name['name']},as_dict=1)
		#frappe.msgprint(str(item))
		actual_qty=frappe.db.sql_list('''select actual_qty from `tabBin` where item_code=%(item)s and warehouse="WooCommerce - ET"''',
				{"item":item[0]['item_name']})
		if actual_qty:
			data['stock_quantity']=actual_qty[0]
			if data['stock_quantity']<=0:
				data['stock_status']="outofstock"
			else:
				data['stock_status']="instock"
		#frappe.msgprint(str(data))
		wcapi.put(f"products/{item[0]['woocommerce_id']}",data).json()
	#for woo_pro in list_all_woo:
		#name=woo_pro['name']
		#if woo_pro['id']:
			#frappe.msgprint(str(woo_pro['id']))
			#woo_prod[name]=woo_pro['id']
		#else:
			#create_product()
	#frappe.msgprint(str(woo_prod))
	#data={}
	#products=frappe.db.sql('''select * from `tabItem` where default_warehouse="WooCommerce - ET"  ''',as_dict=1)
	#frappe.msgprint(str(products))
	#for item_code in products:
		#actual_qty=frappe.db.sql_list('''select actual_qty from `tabBin` where item_code=%(item)s and warehouse="WooCommerce - ET"''',{"item":item_code.item_name})
		#data['name']=item_code.item_name
		#if actual_qty:
		#	data['stock_quantity']=actual_qty[0]
		#frappe.msgprint(str(data))
		#	if data['stock_quantity']<=0:
		#		data['stock_status']="outofstock"
		#wcapi.put(f"products/{item_code.woocommerce_id}", data).json()
