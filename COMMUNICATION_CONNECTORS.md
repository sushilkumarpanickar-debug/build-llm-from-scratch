# DAKSH communications setup

DAKSH has one local Communications screen for Telegram instructions, Gmail inbox review, Google Calendar events, WhatsApp intake, and human approval. Imported items are stored in the existing scoped SQLite database. No connector sends mail, changes calendar events, or performs an external action in Phase 1.

Copy the required entries from `.env.example` into a local `.env` or export them before starting DAKSH. Real credentials and OAuth tokens belong only in `local_workspace/data/connectors/`, which Git ignores.

## Telegram bot instructions and approvals

1. Create a bot using Telegram's BotFather and copy its bot token.
2. Find the numeric chat ID for the private Telegram chat that may control DAKSH.
3. Set `DAKSH_TELEGRAM_BOT_TOKEN` and the comma-separated `DAKSH_TELEGRAM_ALLOWED_CHATS` allowlist.
4. Set `DAKSH_CONNECTOR_POLL_SECONDS=60` for background checks, or leave it at `0` and use **Check Now** in the DAKSH Communications screen.

Any normal message from an allowed chat becomes a pending instruction. DAKSH replies with its approval number. Reply `/approve 12` to approve and stage that instruction as a mission, or `/reject 12` to reject it. Approval stages a local mission; it does not itself send messages or make external changes.

## Gmail and Google Calendar

1. In Google Cloud, create a project, enable the Gmail API and Google Calendar API, configure the OAuth consent screen, and create an OAuth client for a **Desktop app**.
2. Save the downloaded file as `local_workspace/data/connectors/google_oauth_client.json`.
3. Install the local dependencies with `./setup_mac.sh`.
4. Run `.venv/bin/python scripts/setup_google_connectors.py` and complete the Google sign-in in your browser.
5. Restart DAKSH and select **Check Now** under Communications.

DAKSH requests only `gmail.readonly` and `calendar.readonly`. It imports recent inbox metadata/snippets and upcoming events. A Gmail subject beginning `[DAKSH]`, or a body beginning `/daksh`, `/task`, or `/mission`, creates a pending instruction. The default Gmail search is `newer_than:7d` and can be narrowed with `DAKSH_GMAIL_QUERY`.

## WhatsApp Cloud API

WhatsApp requires a Meta Business app, a Cloud API phone number, and a public HTTPS webhook. It cannot reach an application that is available only at `127.0.0.1`.

Set all of these before enabling the webhook:

- `DAKSH_WHATSAPP_VERIFY_TOKEN`: a private verification value you choose.
- `DAKSH_WHATSAPP_APP_SECRET`: the Meta app secret used to verify every webhook signature.
- `DAKSH_WHATSAPP_ALLOWED_NUMBERS`: comma-separated sender numbers in international digits-only format.
- `DAKSH_ALLOW_EXTERNAL_WEBHOOKS=true`: explicit permission for only the WhatsApp webhook path to accept an external host.

Configure Meta's callback URL as `https://YOUR-SECURE-ENDPOINT/api/webhooks/whatsapp`. Use a trusted HTTPS reverse proxy or tunnel and protect access to the Mac. DAKSH validates `X-Hub-Signature-256` with the app secret before accepting a payload. This Phase 1 connector receives approved senders' messages but does not send WhatsApp replies.

## Control model

- Each connector has an allowlist or authenticated account boundary.
- External instructions enter a pending approval queue.
- Approval creates a local planned mission and an audit entry.
- Execution, sending, filing, payments, and calendar changes remain separate actions requiring their own review.
- Connector polling is off by default. Set a polling interval only after credentials are configured.
