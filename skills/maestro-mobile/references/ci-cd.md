# Maestro CI/CD Integration

## GitHub Actions — Maestro Cloud

```yaml
# .github/workflows/maestro-cloud.yml
name: Maestro Cloud Tests
on: [push, pull_request]

jobs:
  test-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build APK
        run: ./gradlew assembleDebug

      - name: Run Maestro Tests on Cloud
        uses: mobile-dev-inc/maestro-github-action@v1
        with:
          api-key: ${{ secrets.MAESTRO_CLOUD_API_KEY }}
          app-file: app/build/outputs/apk/debug/app-debug.apk
          flows-dir: maestro/flows/
          async: false                    # wait for results

  test-ios:
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4

      - name: Build IPA
        run: |
          xcodebuild archive \
            -scheme MyApp \
            -destination 'generic/platform=iOS Simulator' \
            -archivePath MyApp.xcarchive
          xcodebuild -exportArchive \
            -archivePath MyApp.xcarchive \
            -exportPath ./build \
            -exportOptionsPlist ExportOptions.plist

      - name: Run Maestro Tests on Cloud
        uses: mobile-dev-inc/maestro-github-action@v1
        with:
          api-key: ${{ secrets.MAESTRO_CLOUD_API_KEY }}
          app-file: build/MyApp.ipa
          flows-dir: maestro/flows/
```

## GitHub Actions — Local (No Cloud, Android Emulator)

```yaml
# .github/workflows/maestro-local.yml
name: Maestro Local Tests
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Enable KVM
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules
          sudo udevadm trigger --name-match=kvm

      - name: Install Maestro
        run: curl -Ls "https://get.maestro.mobile.dev" | bash

      - name: Set up JDK
        uses: actions/setup-java@v4
        with:
          java-version: 17
          distribution: temurin

      - name: Build APK
        run: ./gradlew assembleDebug

      - name: Start Emulator & Run Tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          target: google_apis
          arch: x86_64
          profile: pixel_6
          disable-animations: true
          script: |
            ~/.maestro/bin/maestro test \
              --format junit \
              --output test-results.xml \
              maestro/flows/

      - name: Publish Test Results
        uses: mikepenz/action-junit-report@v4
        if: always()
        with:
          report_paths: test-results.xml

      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: maestro-artifacts
          path: test-artifacts/
```

## GitHub Actions — Local (macOS iOS Simulator)

```yaml
# .github/workflows/maestro-ios.yml
name: Maestro iOS Tests
on: [push]

jobs:
  test-ios:
    runs-on: macos-14

    steps:
      - uses: actions/checkout@v4

      - name: Select Xcode
        run: sudo xcode-select -s /Applications/Xcode_15.4.app

      - name: Install Maestro
        run: curl -Ls "https://get.maestro.mobile.dev" | bash

      - name: Create iOS Simulator
        run: |
          UDID=$(xcrun simctl create "CI-iPhone" "iPhone 15" "iOS-17-4")
          xcrun simctl boot $UDID
          xcrun simctl bootstatus $UDID -b
          echo "SIM_UDID=$UDID" >> $GITHUB_ENV

      - name: Build & Install App
        run: |
          xcodebuild \
            -scheme MyApp \
            -destination "id=$SIM_UDID" \
            -derivedDataPath DerivedData \
            build
          xcrun simctl install $SIM_UDID \
            DerivedData/Build/Products/Debug-iphonesimulator/MyApp.app

      - name: Run Maestro Tests
        run: |
          ~/.maestro/bin/maestro test \
            --format junit \
            --output test-results.xml \
            --env SIM_UDID=$SIM_UDID \
            maestro/flows/

      - name: Upload Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: maestro-results
          path: |
            test-results.xml
            test-artifacts/
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test

maestro-android:
  stage: test
  image: ubuntu:22.04
  services:
    - name: budtmo/docker-android:emulator_14.0
      alias: android-emulator
  variables:
    ANDROID_SERIAL: "emulator-5554"
  before_script:
    - apt-get update && apt-get install -y curl
    - curl -Ls "https://get.maestro.mobile.dev" | bash
    - export PATH="$HOME/.maestro/bin:$PATH"
  script:
    - adb wait-for-device
    - adb install app-debug.apk
    - maestro test --format junit --output results.xml maestro/flows/
  artifacts:
    reports:
      junit: results.xml
    paths:
      - test-artifacts/
    when: always
```

## Maestro Cloud CLI (Direct)

```bash
# Upload and run on Maestro Cloud
maestro cloud \
  --apiKey $MAESTRO_CLOUD_API_KEY \
  --app app.apk \
  maestro/flows/

# Run on specific devices
maestro cloud \
  --apiKey $MAESTRO_CLOUD_API_KEY \
  --device-locale en_US \
  --app app.apk \
  maestro/flows/

# Get results as JUnit XML
maestro cloud \
  --apiKey $MAESTRO_CLOUD_API_KEY \
  --format junit \
  --output results.xml \
  --app app.apk \
  maestro/flows/
```

## Retry Strategy for Flaky Tests

```yaml
# maestro test with retries
maestro test --retry-on-failure 2 flows/    # retry each failing test up to 2x

# Or in CI, retry the whole step:
# GitHub Actions
- name: Run Maestro
  uses: nick-fields/retry@v3
  with:
    timeout_minutes: 10
    max_attempts: 2
    command: maestro test maestro/flows/
```

## BrowserStack Integration

```bash
# Upload app
APP_URL=$(curl -u "$BS_USER:$BS_KEY" \
  -X POST "https://api-cloud.browserstack.com/app-automate/upload" \
  -F "file=@app.apk" | jq -r '.app_url')

# Run Maestro flows on BrowserStack
maestro cloud \
  --apiKey $MAESTRO_CLOUD_API_KEY \
  --app $APP_URL \
  maestro/flows/
```

## Environment Management

```bash
# .maestro/config.yaml — default environment
env:
  APP_ID: com.example.app
  API_URL: https://staging.api.example.com
  TEST_EMAIL: qa-${random}@test.com

# Override per environment
maestro test --env API_URL=https://prod.api.example.com flows/

# Multiple env files
maestro test --env-file .env.staging flows/
```
