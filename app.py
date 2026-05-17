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
GITHUB_PAT        = os.environ.get("GITHUB_PAT", "")       # Your GitHub Personal Access Token
GITHUB_USER       = "Ellesonntseare"
GITHUB_REPO       = "whatsapp-email-sender"
GITHUB_BRANCH     = "main"                                  # change to "master" if needed

GITHUB_API_BASE   = (
    f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}"
    f"/contents/{{filepath}}?ref={GITHUB_BRANCH}"
)

# ── PROFILES ──────────────────────────────────
# Each profile has its own sender info, documents, and email body.
# Filenames must match exactly what is uploaded to the GitHub repo.

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
        "from_email": "ellesonntseare@gmail.com",   # change if Mathapelo has her own sender email
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

# In-memory session store { whatsapp_number: { "profile": "serame" | "mathapelo" } }
# NOTE: resets every time the server restarts.
SESSIONS = {}

# ─────────────────────────────────────────────
#  GITHUB FILE FETCHER
# ─────────────────────────────────────────────

def fetch_file_from_github(filename):
    """
    Fetches a file from the private GitHub repo using the PAT.
    Returns (base64_encoded_string, error_message).
    GitHub API already returns file content as base64.
    """
    url = GITHUB_API_BASE.format(filepath=requests.utils.quote(filename, safe="/"))
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept":        "application/vnd.github.v3+json",
    }
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        # Strip newlines GitHub adds to the base64 string
        return data.get("content", "").replace("\n", ""), None
    else:
        return None, f"{resp.status_code} - {resp.text}"

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def parse_send_command(text):
    """
    Expects: email subject
    Returns (email, subject) or (None, None).
    """
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
            print(f"⚠️  Could not fetch '{filename}' from GitHub: {error}")
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
    """
    Visit /debug to verify your environment variables and that
    all files can be fetched from GitHub.
    """
    sg_key = os.environ.get("SENDGRID_API_KEY", "")
    gh_pat = os.environ.get("GITHUB_PAT", "")
    lines  = [
        f"SendGrid key set : {'✅' if sg_key else '❌'}",
        f"GitHub PAT set   : {'✅' if gh_pat else '❌'}",
        f"Repo             : {GITHUB_USER}/{GITHUB_REPO} (branch: {GITHUB_BRANCH})",
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
    incoming   = request.form.get("Body", "").strip()
    sender     = request.form.get("From", "unknown")
    resp       = MessagingResponse()
    text_lower = incoming.lower()

    # ── LOGOUT / SWITCH ───────────────────────
    if text_lower in ("logout", "switch", "exit"):
        SESSIONS.pop(sender, None)
        resp.message(
            "👋 Logged out.\n\n"
            "Who would you like to log in as?\n\n"
            "Type *SERAME* or *MATHAPELO*"
        )
        return str(resp)

    # ── NOT logged in yet ─────────────────────
    if sender not in SESSIONS:
        if text_lower == "serame":
            SESSIONS[sender] = {"profile": "serame"}
            resp.message(
                "✅ Logged in as *SERAME*.\n\n"
                "To send your documents, use this format:\n\n"
                "*email subject*\n\n"
                "Example:\njohn@gmail.com Job Application – Serame\n\n"
                "Type *logout* to switch profiles."
            )
        elif text_lower == "mathapelo":
            SESSIONS[sender] = {"profile": "mathapelo"}
            resp.message(
                "✅ Logged in as *MATHAPELO*.\n\n"
                "To send your documents, use this format:\n\n"
                "*email subject*\n\n"
                "Example:\njohn@gmail.com Job Application – Mathapelo\n\n"
                "Type *logout* to switch profiles."
            )
        else:
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
            note = f"\n⚠️ Skipped (not found on GitHub): {', '.join(missing)}" if missing else ""
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
