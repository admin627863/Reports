# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.model.document import Document
import json, re
import requests
import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from frappe.utils import add_months, formatdate, getdate, today
from frappe.utils import nowdate,datetime,now_datetime
from datetime import date,timedelta


class BankIntegrations(Document):
	pass
def get_headers(ss):
    doc = frappe.get_doc('Bank Integrations', ss)

    headers={"accept": "*/*",
              "content-length": "684",
              "content-type": "text/plain"
    }
    for d in doc.get("static_parameters"):
        if d.header == 1:
            headers.update({d.parameter: d.value})

    return headers

@frappe.whitelist()
def register(self):
    ss = frappe.get_doc('Bank Integrations', self)
    headers = get_headers(self)

    payload = {}
    for d in ss.get("static_parameters"):
        if (not d.header and (d.parameter == "CORPID" or d.parameter == "USERID" or d.parameter == "URN" or d.parameter == "AGGRNAME" or d.parameter == "AGGRID" or d.parameter == "url")):
            payload[d.parameter] = d.value
            if d.parameter == "url":
                url_address = d.value
    f = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/uatcertifiacte.pem', 'r')
    public_key = RSA.import_key(f.read())
    url = url_address + "RegistrationStatus"
#    url = 'https://apigwuat.icicibank.com:8443/api/Corporate/CIB/v1/RegistrationStatus'
    json_data = json.dumps(payload)
    json_data = json_data.encode('utf-8')
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(json_data)
    data = base64.b64encode(encrypted)
    response = requests.post(url, data=data, headers=headers)
    res=response.text.encode('utf-8')
    fb = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/privkey.pem', 'r')
    priv_key = RSA.import_key(fb.read())
    cipher = PKCS1_v1_5.new(priv_key)
    decrypt_text = cipher.decrypt(base64.b64decode(res),sentinel="Not")
    text = json.loads(decrypt_text.decode('utf-8'))
    frappe.msgprint(str(text['Status']))
#    ss.status = text['Status']
 #   ss.save()
    return text['Status']

__unpad__ = lambda s: s[0:-ord(s[-1])]

@frappe.whitelist()
def icici_api(self=None):
    if not self:
        bank_integration = frappe.db.sql_list("""select name from `tabBank Integrations` where is_active = '1' """)
        for self in bank_integration:
            frappe.msgprint(str(self))
            bank_statement(str(self))
            balance_enquiry(str(self))
    else:
        bank_statement(str(self))
        balance_enquiry(str(self))

@frappe.whitelist()
def bank_statement(self):
    ss = frappe.get_doc('Bank Integrations', self)
    headers = get_headers(self)
#    date = datetime.datetime.now()
    fromdate = getdate(nowdate()) - timedelta(2)
    fromdatee = fromdate.strftime('%d-%m-%Y')
    todate =  getdate(nowdate()).strftime('%d-%m-%Y')
    payload = {}
    for d in ss.get("static_parameters"):
        if (not d.header and (d.parameter == "CORPID" or d.parameter == "USERID" or d.parameter == "URN" or d.parameter == "AGGRID" or d.parameter == "url" or d.parameter == "ACCOUNTNO" or d.parameter == "FROMDATE" or d.parameter == "TODATE")):
            if d.parameter == "url":
                url_address = d.value
            elif d.parameter == "FROMDATE":
                if d.value == "0":
                   payload[d.parameter] = fromdatee
                else:
                   payload[d.parameter]  = d.value
            elif d.parameter == "TODATE":
                if d.value == "0":
                   payload[d.parameter] = todate
                else:
                   payload[d.parameter]=d.value
            else:
               payload[d.parameter] = d.value
    f = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/uatcertifiacte.pem', 'r')
    public_key = RSA.import_key(f.read())
    url = url_address + 'AccountStatement'
    json_data = json.dumps(payload)
    json_data = json_data.encode('utf-8')
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(json_data)
    data = base64.b64encode(encrypted)
    response = requests.post(url, data=data, headers=headers)
    res=json.loads(response.text.encode('utf-8'))
    data=base64.b64decode(res['encryptedData'])
    iv = data[0:16]
    fb = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/privkey.pem', 'r')
    priv_key = RSA.import_key(fb.read())
    cipher = PKCS1_v1_5.new(priv_key)
    decrypt_text=cipher.decrypt(base64.b64decode(res['encryptedKey']),sentinel="Not Decrypted")
    c = AES.new(decrypt_text, AES.MODE_CBC, iv)
    data=c.decrypt(data)
    response1=data[16:]
    response1=response1.decode()
    response1=__unpad__(response1)
    #response2=response1[:-7]
    #frappe.msgprint(str(response2))
#    frappe.msgprint(response1)
    response2=json.loads(response1)
#    frappe.throw(str(len(response2)))
    if len(response2) == 2:
        return response2
    l1=[]
    if not isinstance(response2['Record'],list):
        l1.append(response2['Record'])
        response2['Record']=l1
#        frappe.msgprint(str(response2['Record']))
    for transaction in response2['Record']:
 #       frappe.msgprint(str(transaction['VALUEDATE']) + formatdate(transaction['TXNDATE']))
        from datetime import datetime as dt
        datetimeobject = dt.strptime(transaction['VALUEDATE'], '%d-%m-%Y')
#        date_new_format = datetimeobject.strftime('%d-%m-%Y')
#        frappe.msgprint(str(datetimeobject)  + "valuedate" + transaction['VALUEDATE'] + "getdate" + str(datetimeobject.date()))
        if not frappe.db.exists("Bank Transaction", dict(transaction_id=transaction["TRANSACTIONID"])):
   #         transaction_date = getdate(transaction['TXNDATE'])
  #          trans_date = transaction_date.strftime('%d-%m-%Y')
  #          frappe.throw(str(trans_date))
            if transaction['TYPE'] == "CR":
                credit = transaction["AMOUNT"]
                debit = 0
            if transaction['TYPE'] == "DR":
                debit = transaction["AMOUNT"]
                credit = 0
            #datetimeobject = datetime.strptime(transaction['VALUEDATE'], '%d-%m-%Y')
            #new_format = datetimeobject.strftime('%d-%m-%Y')
            new_transaction = frappe.get_doc({
				"doctype": "Bank Transaction",
				"date": datetimeobject.date(),
				"balance": transaction['AMOUNT'],
				"bank_account": ss.bank_account,
				"debit": debit,
				"credit": credit,
				"currency": "INR",
				"transaction_id": transaction["TRANSACTIONID"],
				"reference_number": transaction["TRANSACTIONID"],
				"description": transaction["REMARKS"]
			})
            new_transaction.insert()
            new_transaction.submit()
    frappe.msgprint("Account Statements Synced Successfully")
    print("Account Statements Synced Successfully")

@frappe.whitelist()
def registeration(self):
    ss = frappe.get_doc('Bank Integrations', self)
    headers = get_headers(self)

    payload = {}
    for d in ss.get("static_parameters"):
        if (not d.header and (d.parameter == "CORPID" or d.parameter == "USERID" or d.parameter == "URN" or d.parameter == "AGGRNAME" or d.parameter == "AGGRID" or d.parameter == "url" or d.parameter == "ALIASID")):
#            payload[d.parameter] = d.value
            if d.parameter == "url":
                url_address = d.value
            else:
               payload[d.parameter] = d.value

    f = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/uatcertifiacte.pem', 'r')
    public_key = RSA.import_key(f.read())
    url = url_address + 'Registration'
    frappe.msgprint(str(payload))
    frappe.msgprint(str(headers))
    json_data = json.dumps(payload)
    json_data = json_data.encode('utf-8')
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(json_data)
    data = base64.b64encode(encrypted)
    response = requests.post(url, data=data, headers=headers)
    res = response.text.encode('utf-8')
    #frappe.msgprint(res)
    fb = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/privkey.pem', 'r')
    priv_key = RSA.import_key(fb.read())
    cipher = PKCS1_v1_5.new(priv_key)
    try:
    	decrypt_text = cipher.decrypt(base64.b64decode(res),sentinel="Not")
    except:
    	raise Exception(res)
    text = json.loads(decrypt_text.decode('utf-8'))
    frappe.msgprint(str(text))

@frappe.whitelist()
def balance_enquiry(self):
    ss = frappe.get_doc('Bank Integrations', self)
    headers = get_headers(self)

    payload = {}
    for d in ss.get("static_parameters"):
        if (not d.header and (d.parameter == "CORPID" or d.parameter == "USERID" or d.parameter == "URN" or d.parameter == "AGGRID" or d.parameter == "url" or d.parameter == "ACCOUNTNO")):
#            payload[d.parameter] = d.value
            if d.parameter == "url":
                url_address = d.value
            else:
               payload[d.parameter] = d.value
    f = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/uatcertifiacte.pem', 'r')
    public_key = RSA.import_key(f.read())
    url = url_address + 'BalanceInquiry'
    json_data = json.dumps(payload)
    json_data = json_data.encode('utf-8')
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(json_data)
    # encrypted=rsa.encrypt(json_data,cipher)
    data = base64.b64encode(encrypted)
    response = requests.post(url, data=data, headers=headers)
    res = response.text.encode('utf-8')
    fb = open(r'/home/frappe/frappe-bench/apps/erpnext/erpnext/public/privkey.pem', 'r')
    priv_key = RSA.import_key(fb.read())
    cipher = PKCS1_v1_5.new(priv_key)
    decrypt_text = cipher.decrypt(base64.b64decode(res), sentinel="Not")
    text = json.loads(decrypt_text.decode('utf-8'))
   # frappe.msgprint(text['EFFECTIVEBAL'])
    frappe.db.set_value("Bank Integrations",self,"balance",text['EFFECTIVEBAL'])
    frappe.msgprint( "Effective Balance is "+text['EFFECTIVEBAL'])
