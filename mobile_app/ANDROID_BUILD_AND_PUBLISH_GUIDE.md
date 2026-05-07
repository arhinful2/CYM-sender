# Android App Build & Play Store Publishing Guide

This guide walks you through building a signed AAB (Android App Bundle) and publishing to Google Play Console.

## Pre-requisites
✓ Android Studio installed and configured
✓ Java SDK 11+ (installed with Android Studio)
✓ Android SDK (installed with Android Studio)
✓ Google Play Developer Account ($25 one-time registration)

## Step 1: Set Up Signing Keystore

Generate a release keystore (run once, keep it safe):

```bash
cd mobile_app/android
keytool -genkey -v -keystore release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release
```

Fill in when prompted:
- Keystore password: (remember this)
- Key password: (same as keystore password recommended)
- Name: Your full name
- Organizational unit: (e.g., "CYM")
- Organization: Church Youth Management
- City: (your city)
- State: (your state)
- Country: GH (or your country code)

Then configure signing:

```bash
# Copy template
copy key.properties.example key.properties

# Edit key.properties with real values:
storeFile=../keystore/release-key.jks
storePassword=YOUR_KEYSTORE_PASSWORD
keyAlias=release
keyPassword=YOUR_KEY_PASSWORD
```

⚠️ **CRITICAL**: Never commit key.properties or release-key.jks to git.

## Step 2: Increment App Version (For Each Release)

Edit `android/gradle.properties`:

```gradle
APP_VERSION_CODE=1        # Must increment by 1 each release
APP_VERSION_NAME=1.0.0    # User-visible version
```

Example progression:
- v1.0.0: CODE=1
- v1.0.1: CODE=2 (patch)
- v1.1.0: CODE=3 (minor)

## Step 3: Open in Android Studio

```bash
cd mobile_app
npx cap open android
```

Or manually:
```
File > Open > mobile_app/android
```

Wait for Gradle sync to complete (may take 5+ minutes first time).

## Step 4: Build Signed AAB

In Android Studio:

1. Menu: **Build > Generate Signed Bundle / APK**
2. Choose: **Android App Bundle (AAB)** (recommended for Play Store)
3. Next
4. Key store path: `android/keystore/release-key.jks`
5. Key store password: (enter your password)
6. Key alias: `release`
7. Key password: (enter your password)
8. Destination folder: `mobile_app/android/app/release/` (default)
9. Build variant: **release**
10. Signature versions: Check both **V1** and **V2** (modern signing)
11. **Create**

Wait for build (5-15 minutes). Output: `app-release.aab`

## Step 5: Validate Signed Bundle

```bash
# Inspect AAB contents
cd mobile_app/android/app/release
# Open app-release.aab in Android Studio or use bundletool

bundletool validate --bundle=app-release.aab
```

## Step 6: Test on Device (Optional)

Convert AAB to APK for local testing:

```bash
# Using bundletool (download from Google)
bundletool build-apks --bundle=app-release.aab --output=app.apks --mode=universal

# Install on connected device
bundletool install-apks --apks=app.apks
```

## Step 7: Upload to Google Play Console

1. Go to [play.google.com/console](https://play.google.com/console)
2. Select **CYM Sender** app (create if needed)
3. Left menu: **Release > Production**
4. **Create new release**
5. Upload AAB file (`app-release.aab`)
6. Add **Release notes**:
   - What's new in this version
   - Bug fixes
   - Feature improvements
7. **Review release**
8. Verify app metadata:
   - App title: CYM Sender
   - Short description: Church Youth Management System
   - Full description: (include key features: SMS, events, attendance, messaging)
   - Screenshots: (2-5 minimum; 1280x720 or 1440x810)
   - Feature graphic: 1024x500
   - Icon: 512x512
9. Content rating questionnaire: Complete if not done
10. Privacy policy: Provide link (required)
11. Data safety section: Declare data handling
12. **Rollout**:
    - First release: Start with **Internal Testing** (5%)
    - Monitor for crashes (24-48 hours)
    - Increase to **Staged Rollout** (10%, 25%, 50%, 100%)
    - Or direct to **Production** if confident

## Step 8: Monitor Releases

In Play Console:

1. **Analytics > Overview**: Check install trends
2. **Crashes & ANRs**: Monitor app stability
3. **Reviews > Ratings**: Read user feedback
4. **Version distribution**: Ensure rollout progressing

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Keystore not found** | Verify path in key.properties; ensure release-key.jks exists |
| **Signing failed** | Check key alias and passwords match keytool output |
| **Gradle sync hangs** | Restart Android Studio; invalidate caches (File > Invalidate) |
| **APK validation error** | Ensure minSdkVersion 23+; check manifest for errors |
| **Play Console upload fails** | Ensure AAB signed with same keystore as previous version; increment versionCode |
| **App crashes after install** | Check logcat in Android Studio; test on emulator first |

## Version Control

Never commit to git:
```
android/keystore/
android/key.properties
android/app/release/
```

These are already in .gitignore.

## Security Notes

1. **Keep keystore backed up**: Store release-key.jks in a secure location (encrypted USB, password manager)
2. **Password security**: Use strong passwords; don't share
3. **One keystore per app**: Never reuse across different apps
4. **Signature immutable**: Once released, can never change signing key

## Next Release Workflow (Fast Path)

```bash
# 1. Increment version in android/gradle.properties
# 2. Build signed AAB
Build > Generate Signed Bundle / APK > Android App Bundle
# 3. Upload to Play Console
# 4. Add release notes and roll out
```

Estimated time: 15-30 minutes per release.

## References

- [Android Studio Documentation](https://developer.android.com/studio/publish)
- [Play Console Help](https://support.google.com/googleplay/android-developer)
- [Bundle Tool](https://developer.android.com/studio/command-line/bundletool)
- [Android App Signing](https://developer.android.com/studio/publish/app-signing)
