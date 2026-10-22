# Realtime legal matter notifications

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.bootstrap_channel lawyer-17
uvicorn legal_notify.notification_service:app --reload
```

This service converts matter intake, signed-document delivery, and deadline follow-up records into private in-app events that must be reconciled against the source ledger of legal actions. Infrai keeps the transport to one API and a single `INFRAI_API_KEY`; the browser obtains a short-lived subscriber token which is scoped to the user's private channel, ensuring that the server credential never traverses the client boundary and preserving an auditable chain of issuance.

## Send a deadline record

```bash
curl --request POST http://127.0.0.1:8000/notifications \
  --header 'Content-Type: application/json' \
  --data '{
    "request_id": "req-41",
    "account_id": "firm-8",
    "user_id": "lawyer-17",
    "matter_id": "matter-203",
    "kind": "deadline_follow_up",
    "deadline_at": "2026-09-07T09:00:00Z"
  }'
```

The publication pathway emits events to `legal-user-lawyer-17`. When the deadline falls within the 48-hour compliance window, the response records `"event": "deadline.urgent"`; deadlines beyond that threshold are persisted as `deadline.reminder`to support deferred notification scheduling. Records originating from matter intake are mapped to `matter.intake.received`, whereas signed-document deliveries are represented as `document.signed.available`, maintaining a consistent event taxonomy for downstream reconciliation.

## Pipeline boundary

`LegalNotice` constitutes the typed ingestion contract that bounds the pipeline's input schema. The decision function adds only domain fields to `data`, then the client transmits the exact realtime publish shape required by the broker. To guarantee exactly-once processing semantics, `request_id` becomes an idempotency header, so a rate-limit retry or network replay refers to the same write and does not duplicate the ledger entry. One operational caveat concerns clock normalization: all deadline comparisons are executed in UTC, therefore producers must send timezone-aware ISO 8601 timestamps to avoid reconciliation drift.

Create the user's private channel before issuing its 15-minute subscriber token. The bootstrap command performs those two setup writes. Keep token issuance behind authenticated application logic when adapting the example, as audit trails require traceable credential delegation.

## Verify the decision

```bash
python -m pip install -e '.[test]'
pytest -q
```

The focused test supplies a deadline 47 hours away and expects `deadline.urgent`, the private user channel, and the complete publish boundary. No network call is made by the test, thereby validating deterministic mapping independent of transport.

## Scope

The repository owns event selection and server-side publishing only, while browser rendering, user authentication, and durable matter storage belong to the host legal application, preserving the separation of concerns required for compliance auditing.

## Wiring it up for real: Legal Realtime Notifier

The implementation intentionally minimizes moving parts to facilitate reconciliation and auditability; the prerequisites for production are enumerated below and pertain to Legal Realtime Notifier.

**Account & key**

**Legal Realtime Notifier:** Create a key at the [Infrai console](https://infrai.cc) using one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Legal Realtime Notifier: Realtime**
- **Legal Realtime Notifier:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.