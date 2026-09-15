# DAKSH WhatsApp privacy policy — draft for owner review

This draft is not published and must be checked against the actual deployment before use. Add the operator's contact address and effective date before publication.

DAKSH is a private assistant operated by SNNS Smartact Solutions Pvt Ltd. Its WhatsApp Business connection receives messages sent to its connected business number. It does not read an existing personal WhatsApp inbox.

The assistant processes sender identifiers, message text, timestamps, and message identifiers to recognize the authorized user, receive instructions, and create approval requests. Authorized message data is stored in a local database on the operator's Mac. Messages from senders outside the configured allowlist are ignored by the application.

Model inference runs locally through Ollama. WhatsApp messages are transported through Meta's WhatsApp Business services; the configured HTTPS tunnel provider carries webhook traffic to the Mac. These services have their own privacy terms. The deployed tunnel provider and configuration must be identified in the final policy.

DAKSH does not sell message data or use it for advertising. Credentials are stored separately from source code. Message records remain on the Mac until the operator removes them; there is currently no automatic retention expiry.

Users should not send passwords, verification codes, payment-card details, or other secrets. External actions remain subject to the assistant's configured approval workflow. This policy must be revised if cloud inference, broader access, attachments, or additional recipients are enabled.

For access or deletion requests, contact: **[operator to supply contact email]**.

Effective date: **[operator to supply]**.
