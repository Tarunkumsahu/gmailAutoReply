from flask import Flask, request
import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)

@app.route("/", methods=["GET"])
def gmail_auto_reply():
    creds = Credentials(
        None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"]
    )

    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me", labelIds=["INBOX", "UNREAD"], maxResults=5, q="from:wwtarunsahu@gmail.com"
    ).execute()

    messages = results.get("messages", [])

    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"], format="full").execute()
        headers = msg["payload"]["headers"]
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

        body = ""
        if "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
        else:
            data = msg["payload"]["body"].get("data")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8")

        import re
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', body)
        filtered = [e for e in emails if not (e.endswith("@gmail.com") or e.endswith("@algebrait.com"))]

        if not filtered:
            continue

        target_emails = filtered
        name = sender.split("<")[0].strip()
        reply_text = f"""Hello {name},

I hope you're doing well. I recently received a job requirement from my employer, and I wanted to express my strong interest in this position. I'm open to relocating if necessary and look forward to the possibility of joining your team.

Please feel free to reach out to me at your earliest convenience to discuss this opportunity further. If required, I can also provide passport details as well.

Looking forward to hearing from you soon.
My Employer's details: 
Sandy@algebrait.com , Rosy@algebrait.com
7372796091  7372796092

--
Tarun Sahu
P: 469-454-8473
E: tarun.kum.sahu@gmail.com
L: https://www.linkedin.com/in/tarun-sahu-716595243/
"""

        msg_mime = MIMEMultipart()
        msg_mime["To"] = ", ".join(target_emails)
        msg_mime["Cc"] = "tarun.kum.sahu@gmail.com"
        msg_mime["Subject"] = f"Re: {subject}"
        msg_mime.attach(MIMEText(reply_text, "plain"))

        with open("Tarun_Sahu_Resume.pdf", "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename="Tarun_Sahu_Resume.pdf")
            msg_mime.attach(attachment)

        raw_message = base64.urlsafe_b64encode(msg_mime.as_bytes()).decode("utf-8")

        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        service.users().messages().modify(
            userId="me",
            id=message["id"],
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    return "Auto-replies sent."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
