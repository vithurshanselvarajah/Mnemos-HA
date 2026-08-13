# API Key Permissions

Mnemos has two permission levels for API keys, and which one you give the Home Assistant integration determines what works.

| Permission | What you can do | What works in Mnemos-HA |
| --- | --- | --- |
| **Identify-Only** | `POST /api/v1/identify` (read-only) | All sensors, `mnemos.identify`, `mnemos.refresh` — everything currently in the integration |
| **Full-Admin** | Everything, including `assign`, `mark-non-face`, `ignore`, `models/switch`, `keys/*` | Same as above, plus future `mnemos.assign` and `mnemos.switch_model` services |

The config flow accepts either. Identify-Only is the recommended default because it follows least-privilege: if a HA user with access to the integration is compromised, they can't reassign faces or rotate keys.

## Where to find the key

1. In Mnemos, **Settings → API Keys**.
2. Click **+ Create API Key**.
3. Name it `home-assistant`, leave permission at **Identify-Only**.
4. Copy the token — it is shown only once.
5. Paste it into the HA config flow.

## Rotation

If you rotate the key in Mnemos:

1. Open **Settings → Devices & Services → Mnemos → Configure**.
2. Replace the API key.
3. The integration will hot-reload with the new key on the next coordinator cycle (≤ 30 s, default).

## Verifying permissions

`GET /healthz` is the integration's handshake. It works for any key. A 401 here means the key was revoked or mistyped; a 200 doesn't tell you what *level* you have, but the actions that need a higher level will fail with 403 the first time you call them.
