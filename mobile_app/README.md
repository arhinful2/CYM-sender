# CYM Mobile App Wrapper (Android)

This folder adds an Android app shell around the existing Django web system.
It does **not** remove or change your backend logic.

## What This Gives You

- Installable Android app package (APK/AAB)
- Same live system from `https://cym-sender.vercel.app`
- Zero rewrite of current Django features

## Prerequisites

1. Install Node.js LTS (includes npm): [nodejs.org](https://nodejs.org/)
2. Install Android Studio: [developer.android.com/studio](https://developer.android.com/studio)
3. Ensure Java SDK and Android SDK are configured by Android Studio

## First-Time Setup

From this `mobile_app` folder:

```powershell
npm install
npx cap add android
npx cap sync android
npx cap open android
```

Or run the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-android.ps1
```

## Build For Release (Play Store)

1. Open project in Android Studio (`npx cap open android`)
2. Set signing config
3. Build signed AAB from Android Studio
4. Upload AAB to Google Play Console

## Notes

- If you change domain later, update `server.url` in `capacitor.config.ts`.
- Keep HTTPS enabled in production.
- Push notifications can be added later using Capacitor plugins without touching core Django logic.

## Production Prep Added

1. Versioning is now controlled in android/gradle.properties:

- APP_VERSION_CODE
- APP_VERSION_NAME

1. Optional signing is pre-wired in android/app/build.gradle:

- Copy android/key.properties.example to android/key.properties
- Fill your real keystore values

1. Security hardening is enabled in AndroidManifest.xml:

- allowBackup=false
- fullBackupContent=false
- usesCleartextTraffic=false

1. Asset pipeline command:

- npm run assets:generate

1. Full release checklist:

- See PLAYSTORE_RELEASE_CHECKLIST.md
