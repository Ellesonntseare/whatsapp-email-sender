import os
import re
import requests
import smtplib
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

GMAIL_ADDRESS      = "ellesonntseare@gmail.com"
GMAIL_APP_PASSWORD = "qzhp yjri citw jult"

DEFAULT_SUBJECT = "Application"

EMAIL_BODY = """Good day,

Please find the attached.

Regards,
Serame"""

# Google Drive files — add as many as you need
# Format: ("Filename.pdf", "GOOGLE_DRIVE_FILE_ID")
DRIVE_FILES = [
    ("Serame_Documents.pdf", "1V7G_t7QvK3W_Sd7UqkNtcPhOuoQOf_Vm"),
]

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def extract_email(text):
    """Pull the first valid email address out of a WhatsApp message."""
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else None

def download_drive_file(file_id):
    """Download a file from Google Drive by its file ID."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    response = session.get(url, stream=True)

    # Handle the Google Drive large-file confirmation page
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    if token:
        response = session.get(url, params={"confirm": token}, stream=True)

    return BytesIO(response.content)

def send_email(recipient):
    """Send email with all Drive attachments to the given recipient."""
    msg = MIMEMultipart()
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = recipient
    msg["Subject"] = DEFAULT_SUBJECT
    msg.attach(MIMEText(EMAIL_BODY, "plain"))

    for filename, file_id in DRIVE_FILES:
        try:
            file_data = download_drive_file(file_id)
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_data.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
        except Exception as e:
            print(f"⚠️  Could not attach {filename}: {e}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, recipient, msg.as_string())

# ─────────────────────────────────────────────
#  FLASK APP
# ─────────────────────────────────────────────

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming = request.form.get("Body", "").strip()
    resp = MessagingResponse()

    email = extract_email(incoming)

    if not email:
        resp.message(
            "👋 Hi! To send your documents, just reply with the recipient's email address.\n\n"
            "Example: send to john@gmail.com"
        )
        return str(resp)

    try:
        send_email(email)
        resp.message(f"✅ Done! Your documents have been sent to *{email}* successfully.")
    except Exception as e:
        resp.message(f"❌ Something went wrong: {str(e)}\n\nPlease try again.")

    return str(resp)

@app.route("/")
def index():
    return "✅ WhatsApp Email Sender is running."

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
