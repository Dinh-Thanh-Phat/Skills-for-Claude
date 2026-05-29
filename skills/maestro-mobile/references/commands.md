# Maestro Command Reference

Complete list of Maestro YAML commands with syntax.

## App Control
```yaml
- launchApp                              # launch fresh (clears state)
- launchApp:
    appId: com.example.app              # override appId
    clearState: true                    # clear state before launch (default with launchApp)
    clearKeychain: true                 # also clear keychain (iOS)
    stopApp: false                      # don't stop before launching

- stopApp                               # terminate the app
- stopApp:
    appId: com.example.app

- clearState                            # clear app data without relaunching
- clearKeychain                         # clear keychain (iOS)

- openLink: "myapp://deeplink/path"     # open URL/deep link
- openLink:
    link: "myapp://path"
    autoVerify: true                    # Android Auto Verify deep links
```

## Tapping
```yaml
- tapOn: "Button Text"                  # tap on text
- tapOn:
    id: "button-id"                     # accessibility ID
- tapOn:
    text: "Submit"
- tapOn:
    label: "Submit form"                # accessibility label / content desc
- tapOn:
    below: "Email"                      # relative position
- tapOn:
    below: "Email"
    above: "Password"                   # combine relative selectors
- tapOn:
    point: { x: 50%, y: 30% }          # coordinates (% or px)

- doubleTapOn: "Image"
- longPressOn: "Item"
- longPressOn:
    id: "item-id"
    duration: 2000                      # ms
```

## Text Input
```yaml
- inputText: "hello world"
- clearText                             # clear focused input
- hideKeyboard                          # dismiss soft keyboard
- pressKey: Enter                       # Home, Back, VolumeUp, VolumeDown, Lock, Enter
- copyTextFrom:
    id: "input-field"                   # copies to clipboard
- pasteText                             # paste from clipboard
```

## Scrolling & Swiping
```yaml
- scroll                                # scroll down
- scroll:
    direction: UP                       # UP / DOWN / LEFT / RIGHT
    duration: 400                       # ms

- scrollUntilVisible:
    element:
      id: "target-item"
    direction: DOWN
    timeout: 10000                      # ms

- swipe:
    direction: LEFT                     # swipe gesture
    duration: 300
- swipe:
    start: { x: 80%, y: 50% }
    end: { x: 20%, y: 50% }
    duration: 300

- drag:
    start: { x: 100, y: 400 }
    end: { x: 100, y: 200 }
```

## Assertions
```yaml
- assertVisible: "Text"                 # fails immediately if not found
- assertVisible:
    id: "button-id"
- assertVisible:
    text: "Order #"
    contains: true                      # partial match
- assertVisible:
    text: "Submit"
    enabled: true                       # check enabled state
- assertVisible:
    id: "badge"
    timeout: 8000                       # custom wait timeout (ms)

- assertNotVisible: "Error Message"
- assertNotVisible:
    id: "loading-spinner"

- assertTrue: ${MY_VAR} == "expected"  # boolean assertion on variable
```

## Waiting
```yaml
- waitForAnimationToEnd                 # wait for screen to become static
- waitForAnimationToEnd:
    timeout: 5000                       # max wait in ms (continues if timeout)

- wait: 1000                           # ⚠️ avoid — use assertions instead

# Better than wait: assert what you're waiting for
- assertVisible:
    id: "content"
    timeout: 10000
```

## Flow Composition
```yaml
- runFlow: ./shared/login.yaml          # run another flow file

- runFlow:
    file: ./flows/login.yaml
    env:
      USER_EMAIL: test@example.com
      USER_PASSWORD: secret
```

## Conditionals
```yaml
- condition:
    visible: "Allow"
  if:
    - tapOn: "Allow"
  else:
    - tapOn: "Deny"

- condition:
    platform: iOS                       # iOS / Android
  if:
    - tapOn: "Allow Notifications"

- condition:
    notVisible: "Skip"
  if:
    - runFlow: onboarding.yaml
```

## Loops
```yaml
- repeat:
    times: 3
    commands:
      - tapOn: "Next"
      - waitForAnimationToEnd

- repeat:
    while:
      notVisible: "End"
    maxRepeat: 20                       # prevent infinite loops
    commands:
      - scroll:
          direction: DOWN
```

## Screenshots & Recording
```yaml
- takeScreenshot: filename-prefix       # saves to test-artifacts/
- startRecording                        # start video recording
- stopRecording                         # stop and save video
```

## JavaScript (runScript)
```yaml
- runScript:
    file: scripts/my-script.js
    env:
      INPUT_VAR: "value"
    outputVars:
      RESULT: result.myOutput           # map JS output → flow variable

# Access flow vars in JS: params.INPUT_VAR
# Write output: output.myOutput = "value"
```

## System / Device
```yaml
- setLocation:
    lat: 37.7749
    long: -122.4194

- startLocation                         # start fake GPS
- stopLocation

- addMedia:
    files:
      - path/to/photo.jpg               # add to Photos/Gallery
```

## Variables & Environment
```yaml
# In flow header
env:
  USER_EMAIL: test@example.com
  API_URL: https://staging.api.com

# In commands
- inputText: ${USER_EMAIL}
- tapOn: ${BUTTON_ID}

# Pass at CLI
# maestro test --env USER_EMAIL=a@b.com flow.yaml

# From runScript outputVars
- inputText: ${GENERATED_EMAIL}
```

## appId Override
```yaml
# Top of flow file
appId: com.example.app        # default
# OR
appId: ${APP_ID}              # from env

# Per-command (rarely needed)
- tapOn:
    id: "button"
    # appId overriding not needed per-command
```
