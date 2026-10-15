# Hidayah mobile app (Expo, Android + iPhone)

One codebase for both phones, built with Expo SDK 57 and Expo Router. It talks to the same backend as the website and shows the same content with the same credits. The admin dashboard is web-only.

## What was checked, and what was not

Checked in the build environment: TypeScript type check, 9 unit tests for the API client (token storage, refresh rotation, offline logout), and a real Metro bundle for both Android and iOS.

**Not checked: the app has never run on a phone or emulator.** Please test it yourself before relying on it.

## Run it on your phone (development)

1. Start the backend on your computer, listening on all addresses so the phone can reach it:
   `cd backend; .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Copy `mobile/.env.example` to `mobile/.env` and put your computer's LAN address in it (for example `http://192.168.1.20:8000/api/v1`). Phone and computer must be on the same Wi-Fi. `localhost` will not work from a phone.
3. In `mobile/`: `npm install` then `npx expo start`.
4. Install **Expo Go** on the phone, scan the QR code. Android and iPhone both work this way.

The phone app does not need CORS (that setting is only for browsers).

## Store builds (needs your approval and accounts)

Publishing to Google Play and the App Store needs developer accounts (Apple's is paid) and Expo's build service (EAS). The bundle identifiers in `app.json` (`com.example.hidayah`) are placeholders and must be replaced first. Nothing has been built or submitted.

## Notes

- `src/lib/types.ts` is a copy of the website's API types. Keep them in step.
- `.npmrc` sets `legacy-peer-deps=true` because one optional peer dependency of the Expo packages conflicts.
- Urdu fonts are not included yet (Urdu content is not launched).
