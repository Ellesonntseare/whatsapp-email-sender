import os
import re
import base64
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

SENDGRID_API_KEY  = os.environ.get("SENDGRID_API_KEY", "")

GITHUB_USER      = "Ellesonntseare"
GITHUB_REPO      = "whatsapp-email-sender"
GITHUB_BRANCH    = "main"
GITHUB_RAW_BASE  = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/"
)

# ── PROFILES ──────────────────────────────────

PROFILES = {
    "1": {
        "name":       "Serame",
        "from_email": "ellesonntseare@gmail.com",
        "from_name":  "Serame",
        "email_body": (
            "Good day,\n\n"
            "Please find the attached.\n\n"
            "Regards,\n"
            "Serame"
        ),
        "attachments": [
            "ID.jpg",
            "Matric results.pdf",
            "Serame Ntseare CV.pdf",
            "Transcript.pdf",
            "University diploma.pdf",
        ],
    },
    "2": {
        "name":       "Mathapelo",
        "from_email": "ellesonntseare@gmail.com",
        "from_name":  "Mathapelo",
        "email_body": (
            "Good day,\n\n"
            "Please find the attached.\n\n"
            "Regards,\n"
            "Mathapelo"
        ),
        "attachments": [
            "Identity document.pdf",
            "Mathapelo_Majoro_CV_Updated.pdf",
            "Matric.pdf",
        ],
    },
}

SESSIONS = {}

LOGIN_PROMPT = (
    "👋 Welcome! Who would you like to log in as?\n\n"
    "1️⃣  Serame\n"
    "2️⃣  Mathapelo\n\n"
    "Reply with *1* or *2*"
)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def fetch_file_from_github(filename):
    url  = GITHUB_RAW_BASE + requests.utils.quote(filename, safe="/")
    resp = requests.get(url)
    if resp.status_code == 200:
        return base64.b64encode(resp.content).decode(), None
    return None, f"{resp.status_code} - {resp.text[:200]}"


def parse_send_command(text):
    match = re.match(r"([\w\.-]+@[\w\.-]+\.\w+)\s+(.+)", text.strip())
    if not match:
        return None, None
    return match.group(1).strip(), match.group(2).strip()


def send_email(profile_key, recipient, subject):
    profile     = PROFILES[profile_key]
    attachments = []
    errors      = []

    for filename in profile["attachments"]:
        encoded, error = fetch_file_from_github(filename)
        if error:
            print(f"⚠️  Could not fetch '{filename}': {error}")
            errors.append(filename)
            continue
        attachments.append({
            "content":     encoded,
            "filename":    filename,
            "type":        "application/octet-stream",
            "disposition": "attachment",
        })

    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from":    {"email": profile["from_email"], "name": profile["from_name"]},
        "subject": subject,
        "content": [{"type": "text/plain", "value": profile["email_body"]}],
        "attachments": attachments,
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type":  "application/json",
        },
        json=payload,
    )
    return response.status_code, response.text, errors

# ─────────────────────────────────────────────
#  FLASK APP
# ─────────────────────────────────────────────

app = Flask(__name__)


@app.route("/")
def index():
    return "✅ WhatsApp Email Sender is running."


@app.route("/debug")
def debug():
    sg_key = os.environ.get("SENDGRID_API_KEY", "")
    lines  = [
        f"SendGrid key set : {'✅' if sg_key else '❌'}",
        f"Repo             : {GITHUB_USER}/{GITHUB_REPO} (branch: {GITHUB_BRANCH})",
        "",
    ]
    for key, profile in PROFILES.items():
        lines.append(f"[{profile['name'].upper()}] files:")
        for filename in profile["attachments"]:
            encoded, error = fetch_file_from_github(filename)
            status = "✅ found" if encoded else f"❌ {error}"
            lines.append(f"  {filename}: {status}")
        lines.append("")
    return "\n".join(lines)


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming   = request.form.get("Body", "").strip()
    sender     = request.form.get("From", "unknown")
    resp       = MessagingResponse()
    text_lower = incoming.lower().strip()

    # ── LOGOUT / SWITCH ───────────────────────
    if text_lower in ("logout", "switch", "exit", "0"):
        SESSIONS.pop(sender, None)
        resp.message(LOGIN_PROMPT)
        return str(resp)

    # ── NOT logged in yet ─────────────────────
    if sender not in SESSIONS:
        if text_lower in ("1", "2"):
            profile     = PROFILES[text_lower]
            SESSIONS[sender] = {"profile": text_lower}
            resp.message(
                f"✅ Logged in as *{profile['name'].upper()}*.\n\n"
                "To send your documents, use this format:\n\n"
                "*email subject*\n\n"
                f"Example:\njohn@gmail.com Job Application – {profile['name']}\n\n"
                "Type *0* to switch profiles."
            )
        else:
            resp.message(LOGIN_PROMPT)
        return str(resp)

    # ── Already logged in ─────────────────────
    profile_key  = SESSIONS[sender]["profile"]
    profile_name = PROFILES[profile_key]["name"]
    email, subject = parse_send_command(incoming)

    if not email or not subject:
        resp.message(
            f"👤 Logged in as *{profile_name.upper()}*\n\n"
            "To send your documents, use this format:\n\n"
            "*email subject*\n\n"
            "Example:\njohn@gmail.com Job Application\n\n"
            "Type *0* to switch profiles."
        )
        return str(resp)

    try:
        status, response_text, missing = send_email(profile_key, email, subject)
        if status in (200, 202):
            note = f"\n⚠️ Skipped (not found): {', '.join(missing)}" if missing else ""
            resp.message(
                f"✅ Email sent to *{email}*\n"
                f"Subject: *{subject}*\n"
                f"Profile: *{profile_name.upper()}*"
                f"{note}"
            )
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
