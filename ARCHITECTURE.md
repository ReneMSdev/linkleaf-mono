# Architecture

How LinkLeaf's pieces fit together, drawn from the code in this repo. The backend API
passes its test suite in CI but has never been deployed. The Flutter app is a UI prototype
on mock data, and its API client isn't connected yet (dotted lines below).

## System overview

```mermaid
flowchart LR
  app["Flutter app<br/>(UI prototype, mock data)"]:::client
  visitor["Visitor's phone<br/>(scans QR code)"]:::client

  subgraph api["FastAPI backend (modular monolith)"]
    routers["api/<br/>(routers: /v1 + public<br/>/p, /q, vCard, theme preview)"]
    domain["domain/<br/>(user, profile, link, contact,<br/>media, theme, subscription)"]
    core["core/<br/>(db session, storage, image processing)"]
    authdep["auth/<br/>(token check, UID allowlist)"]
    routers --> domain --> core
    routers --> authdep
  end

  firebase["Firebase Auth"]:::external
  revenuecat["RevenueCat"]:::external
  pg[("PostgreSQL 16")]:::storage
  gcspub[("GCS public bucket<br/>(avatars, images)")]:::storage
  gcspriv[("GCS private bucket<br/>(résumés)")]:::storage

  app -. "Bearer ID token (not wired yet)" .-> routers
  app -. "sign in (not wired yet)" .-> firebase
  visitor -- "/q/{token}, /p/{slug}, vCard" --> routers
  authdep -- "verify ID token" --> firebase
  revenuecat -- "subscription webhook" --> routers
  core --> pg
  core --> gcspub
  core -- "signed URLs" --> gcspriv

  classDef external fill:#2a1f14,stroke:#e8a659,color:#f2f2f0
  classDef storage fill:#16202a,stroke:#7ea6c9,color:#f2f2f0
  classDef client fill:#1f1a2a,stroke:#a78bfa,color:#f2f2f0
```

The intended layering is `api/` → `domain/` → `core/`, with domains calling each other
through service functions. The code mostly follows it, with exceptions: some services
query other domains' models directly (for example, the subscription service touches
profiles and media during the expiration cleanup), and a few routers run small queries
themselves.

## Authentication and first login

There's no sign-up endpoint. Firebase handles credentials, and the backend creates a user
the first time it sees an allowlisted UID. The first two steps are the planned app flow;
the app doesn't call Firebase or the API yet.

```mermaid
sequenceDiagram
  participant App as Flutter app
  participant API as FastAPI (auth/dependencies.py)
  participant DB as PostgreSQL
  rect rgb(42, 31, 20)
    Note over App,Firebase: planned, not wired in the app yet
    App->>Firebase: sign in
    Firebase-->>App: ID token
  end
  App->>API: request with Authorization: Bearer <token>
  rect rgb(42, 31, 20)
    API->>Firebase: verify_id_token (Admin SDK)
    Firebase-->>API: uid, email
  end
  alt UID not in ALLOWED_FIREBASE_UIDS
    API-->>App: 403 (or anonymous on optional-auth routes)
  else allowed
    API->>DB: find user by firebase_uid
    opt first login
      API->>DB: create user + free subscription
    end
    API-->>App: response
    API--)DB: background task: update last_login_at
  end
```

## QR scan, public profile and "Save contact"

Printed QR codes point at an immutable token, never at the slug, so renaming a profile
can't break a card that's already been handed out.

```mermaid
sequenceDiagram
  participant V as Visitor's phone
  participant API as FastAPI (public routes)
  participant DB as PostgreSQL
  V->>API: GET /q/{qr_token}
  API->>DB: active profile with this token?
  API-->>V: 302 → /p/{current slug}
  V->>API: GET /p/{slug}
  API->>DB: active profile with this slug?
  alt found
    API->>DB: load links, contact, public media, theme
    API-->>V: ProfilePublic JSON (is_premium, has_sensitive_data)
    API--)DB: background task: view_count + 1 (skipped for the owner)
  else not found, but slug is in slug_history
    API-->>V: 301 → /p/{new slug}
  end
  V->>API: GET /contacts/{profile_id}/vcard
  API-->>V: {slug}.vcf (vCard 3.0, branding note on free tier)
```

`/p/{slug}` returns JSON. The web page meant to render it (planned in Next.js) was never
built.

## Subscription lifecycle

RevenueCat reports purchases and expirations by webhook. A bad secret gets a 401; unknown
events, malformed payloads and unknown users get `200 ignored`, so RevenueCat doesn't keep
retrying events the backend chose to skip.

```mermaid
flowchart TD
  hook["POST /v1/subscriptions/webhook"] --> secret{"secret valid?"}
  secret -- no --> r401["401"]
  secret -- yes --> parse{"known event,<br/>known user?"}
  parse -- no --> ignored["200 ignored"]
  parse -- "INITIAL_PURCHASE / RENEWAL /<br/>RESTORE / PRODUCT_CHANGE" --> active["premium, active"]
  parse -- "CANCELLATION / BILLING_ISSUE" --> cancelled["premium, cancelled<br/>(access kept until expiry)"]
  parse -- EXPIRATION --> expired["free, expired"]
  expired --> c1["soft-delete portfolio images<br/>and résumés on non-default profiles"]
  c1 --> c2["soft-delete non-default profiles"]
  c2 --> c3["soft-delete portfolio images<br/>and résumé on the default profile"]
  c3 --> grace[("30-day grace period:<br/>owner can restore")]:::storage
  active --> ok["200"]
  cancelled --> ok
  grace --> ok

  classDef storage fill:#16202a,stroke:#7ea6c9,color:#f2f2f0
```
