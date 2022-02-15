
#Read here to create a paypal sandbox account:
# https://developer.paypal.com/docs/api/overview/#create-sandbox-accounts
import os
paymentpaypal.client_id = os.environ['PAYPAL_CLIENT_ID']
paymentpaypal.client_secret = os.environ['PAYPAL_CLIENT_SECRET']
paymentpaypal.sandboxed = True
