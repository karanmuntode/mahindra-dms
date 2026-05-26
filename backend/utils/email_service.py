# from dotenv import load_dotenv
# load_dotenv()

# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import os

# SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
# SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
# SMTP_USER = os.getenv("SMTP_USER", "")
# SMTP_PASS = os.getenv("SMTP_PASS", "")

# def send_otp_email(to_email: str, otp: str):
#     try:
#         msg = MIMEMultipart("alternative")
#         msg["Subject"] = "Mahindra DMS — Your OTP Code"
#         msg["From"] = SMTP_USER
#         msg["To"] = to_email

#         html = f"""
        # <html><body style="font-family:Arial;background:#f0f4f8;padding:30px">
        #   <div style="max-width:480px;margin:auto;background:white;border-radius:12px;padding:32px;box-shadow:0 4px 20px rgba(0,100,200,0.1)">
        #     <h2 style="color:#1565C0;margin-bottom:8px">Mahindra Document Management</h2>
        #     <p style="color:#555">Your One-Time Password (OTP) for email verification:</p>
        #     <div style="background:#E3F2FD;border-radius:8px;padding:20px;text-align:center;margin:20px 0">
        #       <span style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#1565C0">{otp}</span>
        #     </div>
        #     <p style="color:#888;font-size:13px">This OTP is valid for 10 minutes. Do not share it with anyone.</p>
        #   </div>
        # </body></html>
#         """

#         msg.attach(MIMEText(html, "html"))

#         server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)

#         server.ehlo()

#         server.starttls()

#         server.ehlo()

#         server.login(SMTP_USER, SMTP_PASS)

#         server.sendmail(
#             SMTP_USER,
#             to_email,
#              msg.as_string()
#         )

#         server.quit()

#         print(f"OTP sent to {to_email}")
#     except Exception as e:
#         print("EMAIL ERROR:", str(e))
#         # Don't raise — allow signup to proceed even if email fails


# def send_otp(email: str) -> str:
#     import random
#     otp = str(random.randint(100000, 999999))
#     send_otp_email(email, otp)
#     return otp

from dotenv import load_dotenv
load_dotenv()

import os
import random
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY")




def send_otp_email(to_email: str, otp: str):
    try:
        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "api-key": str(BREVO_API_KEY),
            "accept": "application/json",
            "content-type": "application/json"
        }

        payload = {
            "sender": {
                "name": "Mahindra DMS",
                "email": "karanmuntode510@gmail.com"
            },
            "to": [
                {
                    "email": to_email
                }
            ],
            "subject": "Mahindra DMS OTP Verification",

            "htmlContent": f"""
            <html>
            <body style="font-family:Arial;background:#f0f4f8;padding:30px">
          <div style="max-width:480px;margin:auto;background:white;border-radius:12px;padding:32px;box-shadow:0 4px 20px rgba(0,100,200,0.1)">
            <h2 style="color:#1565C0;margin-bottom:8px">Mahindra Document Management</h2>
            <p style="color:#555">Your One-Time Password (OTP) for email verification:</p>
            <div style="background:#E3F2FD;border-radius:8px;padding:20px;text-align:center;margin:20px 0">
              <span style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#1565C0">{otp}</span>
            </div>
            <p style="color:#888;font-size:13px">This OTP is valid for 10 minutes. Do not share it with anyone.</p>
          </div>
        </body>
            </html>
            """
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=20
        )

        print("STATUS CODE =", response.status_code)
        print("BREVO RESPONSE =", response.text)

    except Exception as e:
        print("EMAIL ERROR:", str(e))


def send_otp(email: str):
    otp = str(random.randint(100000, 999999))

    send_otp_email(email, otp)

    return otp