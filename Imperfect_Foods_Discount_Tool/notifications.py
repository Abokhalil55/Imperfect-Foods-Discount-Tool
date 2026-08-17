import smtplib
import os 
from dotenv import load_dotenv
load_dotenv(override=True)

def send_notification_email(email, store_location, interested_in, store_name):
    sender_email = os.getenv("sender_email")          
    app_password = os.getenv("Google_app_pass")       
    
    receiver_email = email
    subject = "New Matching Product Alert!"
    message = f"Hello!\nA new item matching your interest in '{interested_in}' located at '{store_location}' in'{store_name}' is now available!"
    
    headers = [
        f"From: {sender_email}",
        f"To: {receiver_email}",
        f"Subject: {subject}",
        "MIME-Version: 1.0",
        "Content-Type: text/plain; charset=utf-8"
    ]
    
    text = "\r\n".join(headers) + "\r\n\r\n" + message
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.sendmail(sender_email, [receiver_email], text.encode("utf-8"))
    server.quit()
    
    return
