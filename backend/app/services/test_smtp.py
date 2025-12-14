import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

msg = EmailMessage()
msg.set_content("SMTP test successful!")
msg['Subject'] = "SMTP Test"
msg['From'] = os.getenv("SMTP_EMAIL")
msg['To'] = os.getenv("SMTP_EMAIL")

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(os.getenv("SMTP_EMAIL"), os.getenv("SMTP_PASSWORD"))
    smtp.send_message(msg)

print("Email sent!")
