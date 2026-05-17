import os
import re
import base64
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL       = "ellesonntseare@gmail.com"
FROM_NAME        = "Serame"

EMAIL_BODY = """Good day,

Please find the attached.

Regards,
Serame"""

# Files stored directly in the repo
ATTACHMENTS = [
    "ID.jpg",
    "Matric results.pdf",
    "Serame Ntseare CV.pdf",
    "Transcript.pdf",
    "University diploma.pdf",
]

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def parse_message(text):
    """
    Expects format: email subject
    Example: john@gmail.com Job Application – Serame
    Returns (email, subject) or (None, None) if invalid.
    """
    match = re.match(r"([\w\.-]+@[\w\.-]+\.\w+)\s+(.+)", text.strip())
    if not match:
        return None, None
    return match.group(1).strip(), match.group(2).strip()

def send_email(recipient, subject):
    attachments = []
    for filename in ATTACHMENTS:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(filepath):
            print(f"⚠️  File not found, skipping: {filename}")
            continue
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        attachments.append({
            "content":     encoded,
            "filename":    filename,
            "type":        "application/octet-stream",
            "disposition": "attachment"
        })

    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from":    {"email": FROM_EMAIL, "name": FROM_NAME},
        "subject": subject,
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
    files_found = [f for f in ATTACHMENTS if os.path.exists(os.path.join(os.path.dirname(__file__), f))]
    files_missing = [f for f in ATTACHMENTS if not os.path.exists(os.path.join(os.path.dirname(__file__), f))]
    return (
        f"Key set: {'✅' if key else '❌'}\n"
        f"Files found: {files_found}\n"
        f"Files missing: {files_missing}"
    )

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming = request.form.get("Body", "").strip()
    resp     = MessagingResponse()

    email, subject = parse_message(incoming)

    if not email or not subject:
        resp.message(
            "👋 To send your documents, use this format:\n\n"
            "*email subject*\n\n"
            "Example:\n"
            "john@gmail.com Job Application – Serame"
        )
        return str(resp)

    try:
        status, response_text = send_email(email, subject)
        if status in (200, 202):
            resp.message(f"✅ Done! Email sent to *{email}* with subject *{subject}*.")
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
