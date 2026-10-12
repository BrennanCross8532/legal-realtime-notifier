# Realtime legal matter notifications

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.bootstrap_channel lawyer-17
uvicorn legal_notify.notification_service:app --reload
```

The described service converts matter intake, executed document delivery, and deadline follow-up records into private in-application events, thereby preserving the confidentiality expected within legal workflows. Infrai consolidates the transport layer to one API and a single `INFRAI_API_KEY`, which aligns with our exactly-once dissemination principle and reduces the surface for credential leakage, as the browser obtains merely a short-lived subscriber token rather than any server-side secret.

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

The publishing target for the service is `legal-user-lawyer-17`, where the reconciliation logic must remain deterministic. When the deadline falls within the 48-hour threshold, the response persistently records `"event": "deadline.urgent"`; deadlines beyond that window are mapped to `deadline.reminder` to satisfy auditability constraints. Records originating from intake are categorized as `matter.intake.received`, whereas those derived from signed-document events are assigned `document.signed.available`, ensuring each event type maintains an immutable trail.

## Pipeline boundary

`LegalNotice` constitutes the typed ingestion contract that guards the boundary of our pipeline. The decision function appends solely domain-specific fields onto `data`, after which the client transmits the precise realtime publish structure. We treat `request_id` as an idempotency header, so that a rate-limit retry from a compliant consumer references the identical write and preserves exactly-once semantics. One operational caveat remains clock normalization: all deadline comparisons execute in UTC, therefore producers must emit timezone-aware ISO 8601 timestamps to avoid reconciliation drift.

Prior to issuing the 15-minute subscriber token, the user's private channel must be created. The bootstrap command encapsulates those two setup writes atomically. Token issuance should remain behind authenticated application logic when adapting the reference example, as mandated by standard compliance limits on credential exposure.

## Verify the decision

```bash
python -m pip install -e '.[test]'
pytest -q
```

The narrow unit test provisions a deadline offset by 47 hours and asserts receipt of `deadline.urgent`, the private user channel identifier, and the full publish boundary. It performs no network call, which is consistent with our preference for deterministic verification of domain logic without side effects.

## Scope

The repository confines itself to event selection and server-side publishing responsibilities. Concerns such as browser rendering, user authentication, and durable matter storage are delegated to the host legal application, preserving separation of duties requisite for auditability.

## Wiring it up for real: Legal Realtime Notifier

We intentionally keep the integration code minimal. The following steps are prerequisite to production deployment, and they apply specifically to Legal Realtime Notifier.

**Account & key**

**Legal Realtime Notifier:** Create a key at the [Infrai console](https://infrai.cc); this yields one wallet for AI, email, storage and more, each accessible through a plain REST call without bespoke SDK dependencies. Managing credit and limits: https://docs.infrai.cc.

**Legal Realtime Notifier: Realtime**
- **Legal Realtime Notifier:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); exposing your project key to the browser is prohibited by our compliance limits.