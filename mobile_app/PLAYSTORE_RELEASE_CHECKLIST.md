# Play Store Release Checklist

1. Increment app version values in android/gradle.properties:
- APP_VERSION_CODE=2 (must increase every release)
- APP_VERSION_NAME=1.0.1

2. Configure signing:
- Create keystore (release-key.jks)
- Copy android/key.properties.example to android/key.properties
- Fill real passwords/alias
- Keep key.properties and keystore out of git

3. Generate launcher icon and splash assets:
- Put source files in resources/
- Run: npm run assets:generate
- Run: npm run cap:sync

4. Build release in Android Studio:
- Build > Generate Signed Bundle / APK
- Choose Android App Bundle (AAB)
- Use release signing config

5. Validate before upload:
- App opens and loads https://cym-sender.vercel.app
- Login, quick announcement, messaging flows work
- No cleartext traffic warnings
- No crash on startup

6. Upload to Google Play Console:
- Create release
- Upload AAB
- Complete content rating, privacy policy, and data safety
- Roll out internal testing first
