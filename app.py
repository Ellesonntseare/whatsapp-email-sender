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

SENDGRID_API_KEY = "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"
FROM_EMAIL       = "ellesonntseare@gmail.com"
FROM_NAME        = "Serame"

DEFAULT_SUBJECT  = "Application"

EMAIL_BODY = """Good day,

Please find the attached.

Regards,
Serame"""

# Google Drive files — add more as needed
# Format: ("Filename.pdf", "GOOGLE_DRIVE_FILE_ID")
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

    if response.status_code not in (200, 202):
        raise Exception(f"SendGrid error {response.status_code}: {response.text}")

# ─────────────────────────────────────────────
#  FLASK APP
# ─────────────────────────────────────────────

app = Flask(__name__)

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
