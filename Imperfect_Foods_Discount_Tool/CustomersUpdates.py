import smtplib
from database import intrest_customers



def Customer_updates(item):
    if item['category'] == intrest_customers['category']:
        message = f"Hi {intrest_customers['email']}, we would like to inform you that there are some {intrest_customers['category']} available near to your location with a good discount."
        email_sender = ''
        email_receiver = ''