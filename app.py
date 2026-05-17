import os
import re
import base64
import json
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

SENDGRID_API_KEY  = os.environ.get("SENDGRID_API_KEY", "")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WA_NUMBER   = os.environ.get("TWILIO_WA_NUMBER", "")  # e.g. whatsapp:+14155238886

GITHUB_USER      = "Ellesonntseare"
GITHUB_REPO      = "whatsapp-email-sender"
GITHUB_BRANCH    = "main"
GITHUB_RAW_BASE  = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/"
)

# ── PROFILES ──────────────────────────────────

PROFILES = {
    "serame": {
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
    "mathapelo": {
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


def send_interactive_buttons(to):
    """
    Sends a WhatsApp interactive button message via Twilio API
    so the user can tap to choose a profile.
    """
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    interactive = {
        "type": "button",
        "body": {"text": "👋 Welcome! Who would you like to log in as?"},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": "serame",    "title": "Serame"}},
                {"type": "reply", "reply": {"id": "mathapelo", "title": "Mathapelo"}},
            ]
        }
    }

    client.messages.create(
        from_=TWILIO_WA_NUMBER,
        to=to,
        body="",
        persistent_action=[],
        content_sid=None,
        content_variables=None,
        **{"interactive": json.dumps(interactive)}
    )


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
        f"SendGrid key set  : {'✅' if sg_key else '❌'}",
        f"Twilio SID set    : {'✅' if TWILIO_ACCOUNT_SID else '❌'}",
        f"Twilio Token set  : {'✅' if TWILIO_AUTH_TOKEN else '❌'}",
        f"Twilio WA number  : {'✅' if TWILIO_WA_NUMBER else '❌'}",
        f"Repo              : {GITHUB_USER}/{GITHUB_REPO} (branch: {GITHUB_BRANCH})",
        "",
    ]
    for pname, profile in PROFILES.items():
        lines.append(f"[{pname.upper()}] files:")
        for filename in profile["attachments"]:
            encoded, error = fetch_file_from_github(filename)
            status = "✅ found" if encoded else f"❌ {error}"
            lines.append(f"  {filename}: {status}")
        lines.append("")
    return "\n".join(lines)


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming    = request.form.get("Body", "").strip()
    sender      = request.form.get("From", "unknown")
    button_id   = request.form.get("ButtonPayload", "").strip().lower()
    resp        = MessagingResponse()
    text_lower  = incoming.lower()

    # Button reply takes priority over typed text
    selection = button_id if button_id else text_lower

    # ── LOGOUT / SWITCH ───────────────────────
    if selection in ("logout", "switch", "exit"):
        SESSIONS.pop(sender, None)
        try:
            send_interactive_buttons(sender)
        except Exception:
            resp.message(
                "👋 Logged out.\n\n"
                "Who would you like to log in as?\n\n"
                "Type *SERAME* or *MATHAPELO*"
            )
        return str(resp)

    # ── NOT logged in yet ─────────────────────
    if sender not in SESSIONS:
        if selection in ("serame", "mathapelo"):
            SESSIONS[sender] = {"profile": selection}
            resp.message(
                f"✅ Logged in as *{selection.upper()}*.\n\n"
                "To send your documents, use this format:\n\n"
                "*email subject*\n\n"
                f"Example:\njohn@gmail.com Job Application – {selection.capitalize()}\n\n"
                "Type *logout* to switch profiles."
            )
        else:
            # Send interactive buttons; fall back to text if it fails
            try:
                send_interactive_buttons(sender)
            except Exception:
                resp.message(
                    "👋 Welcome! Who would you like to log in as?\n\n"
                    "Type *SERAME* or *MATHAPELO*"
                )
        return str(resp)

    # ── Already logged in ─────────────────────
    profile_key = SESSIONS[sender]["profile"]
    email, subject = parse_send_command(incoming)

    if not email or not subject:
        resp.message(
            f"👤 Logged in as *{profile_key.upper()}*\n\n"
            "To send your documents, use this format:\n\n"
            "*email subject*\n\n"
            "Example:\njohn@gmail.com Job Application\n\n"
            "Type *logout* to switch profiles."
        )
        return str(resp)

    try:
        status, response_text, missing = send_email(profile_key, email, subject)
        if status in (200, 202):
            note = f"\n⚠️ Skipped (not found): {', '.join(missing)}" if missing else ""
            resp.message(
                f"✅ Email sent to *{email}*\n"
                f"Subject: *{subject}*\n"
                f"Profile: *{profile_key.upper()}*"
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
