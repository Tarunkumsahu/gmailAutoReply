from flask import Flask
import base64
import os
import re
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

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
        userId="me", labelIds=["INBOX", "UNREAD"], maxResults=10
    ).execute()

    messages = results.get("messages", [])

    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"], format="full").execute()
        headers = msg["payload"]["headers"]

        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        to_email = next((h["value"] for h in headers if h["name"] == "To"), "")

        if "wwtarunsahu@gmail.com" not in to_email:
            continue  # Only respond if email was sent to this address

        # Extract all email addresses from body and headers
        body_data = ""
        if "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part.get("mimeType") == "text/plain":
                    body_data = base64.urlsafe_b64decode(part["body"]["data"]).decode()
        else:
            body_data = base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode()

        all_emails = set(re.findall(r'[\w\.-]+@[\w\.-]+', body_data))
        target_emails = [e for e in all_emails if not e.endswith("gmail.com") and not e.endswith("algebrait.com")]

        if not target_emails:
            continue

        target_email = target_emails[0]
        target_name = target_email.split("@")[0].split(".")[0].capitalize()

        reply_text = f"""Hello {target_name},
  
I hope you're doing well. I recently received a job requirement from my employer, and I wanted to express my strong interest in this position. I'm open to relocating if necessary and look forward to the possibility of joining your team.

Please feel free to reach out to me at your earliest convenience to discuss this opportunity further. If required, I can also provide passport details.

Looking forward to hearing from you soon.

My Employers details:
Sandy@algebrait.com, Rosy@algebrait.com
7372796091  7372796092

--

------------------------------------------
Tarun Sahu
P: 469-454-8473
E: tarun.kum.sahu@gmail.com
L: https://www.linkedin.com/in/tarun-sahu-716595243/
"""

        message_body = f"To: {target_email}\r\nSubject: Re: Interest in the opportunity\r\n\r\n{reply_text}"
        raw_message = base64.urlsafe_b64encode(message_body.encode("utf-8")).decode("utf-8")

        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        # Mark the message as read
        service.users().messages().modify(
            userId="me",
            id=message["id"],
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    return "Auto-replies sent."

# Bind to Cloud Run port
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
