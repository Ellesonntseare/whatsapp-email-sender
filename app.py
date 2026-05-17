import os
import re
import base64
import requests
from io import BytesIO
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL       = "ellesonntseare@gmail.com"
FROM_NAME        = "Serame"
DEFAULT_SUBJECT  = "Application"

EMAIL_BODY = """Good day,

Please find the attached.

Regards,
Serame"""

DRIVE_FILES = [
    ("Serame_Documents.pdf", "1V7G_t7QvK3W_Sd7UqkNtcPhOuoQOf_Vm"),
]

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def extract_email(text):
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else None

def download_drive_file(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    response = session.get(url, stream=True)

    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    if token:
        response = session.get(url, params={"confirm": token}, stream=True)

    return BytesIO(response.content)

def send_email(recipient):
    attachments = []
    for filename, file_id in DRIVE_FILES:
        try:
            file_data = download_drive_file(file_id)
            encoded   = base64.b64encode(file_data.read()).decode()
            attachments.append({
                "content":     encoded,
                "filename":    filename,
                "type":        "application/octet-stream",
                "disposition": "attachment"
            })
        except Exception as e:
            print(f"⚠️  Could not attach {filename}: {e}")

    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from":    {"email": FROM_EMAIL, "name": FROM_NAME},
        "subject": DEFAULT_SUBJECT,
        "content": [{"type": "text/plain", "value": EMAIL_BODY}],
        "attachments": attachments
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type":  "application/json"
        },
        json=payload
    )

    return response.status_code, response.text

# ─────────────────────────────────────────────
#  FLASK APP
# ─────────────────────────────────────────────

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ WhatsApp Email Sender is running."

@app.route("/debug")
def debug():
    key = os.environ.get("SENDGRID_API_KEY", "")
    if not key:
        return "❌ SENDGRID_API_KEY is NOT set in environment."
    return f"✅ SENDGRID_API_KEY is set. Starts with: {key[:10]}... Length: {len(key)}"

@app.route("/test-email")
def test_email():
    status, response_text = send_email(FROM_EMAIL)
    return f"SendGrid Status: {status}\nResponse: {response_text}"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming = request.form.get("Body", "").strip()
    resp     = MessagingResponse()
    email    = extract_email(incoming)

    if not email:
        resp.message(
            "👋 Hi! To send your documents, just reply with the recipient's email address.\n\n"
            "Example: send to john@gmail.com"
        )
        return str(resp)

    try:
        status, response_text = send_email(email)
        if status in (200, 202):
            resp.message(f"✅ Done! Your documents have been sent to *{email}* successfully.")
        else:
            resp.message(f"❌ SendGrid error {status}: {response_text}")
    except Exception as e:
        resp.message(f"❌ Something went wrong: {str(e)}")

    return str(resp)

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
