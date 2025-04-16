from flask import Flask, jsonify
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

app = Flask(__name__)

@app.route("/")
def check_gmail_auth():
    try:
        creds = Credentials(
            None,
            refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ["GMAIL_CLIENT_ID"],
            client_secret=os.environ["GMAIL_CLIENT_SECRET"]
        )
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# for Cloud Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
