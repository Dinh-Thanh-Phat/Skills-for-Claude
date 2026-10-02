---
name: maestro-network-mocking
description: >-
  Control API responses during Maestro mobile E2E flows to test UI behavior in isolation — error
  states, edge cases, slow networks — without a live backend. Use when Maestro flows depend on
  real API responses that are hard to control (loading skeletons, empty states, 5xx errors, slow
  responses), when you want deterministic Maestro tests on CI, or when the backend isn't available
  yet. Triggers on: "mock API in Maestro", "WireMock Maestro", "Maestro network stub",
  "Maestro offline test", "Mockoon mobile", "Requestly Maestro", "mock server mobile test",
  "test without real API Maestro".
---

# Maestro Network Mocking

Maestro tests the UI layer. But if the app talks to a real API, tests can fail because of backend
flakiness, data mutations, or unavailability. Network mocking isolates the UI from the backend:
the app calls the mock server, gets predictable JSON, and Maestro asserts the UI result.

> **Maestro has NO built-in network mocking/interception** (no mocking page in docs.maestro.dev,
> nothing in the CHANGELOG through 2.11.0). Everything below happens *outside* Maestro: a mock
> server or proxy, plus a way to point the **app** at it. Maestro only drives the UI.

## Decision table — pick an approach

| Approach | App code change needed | Best for | Tool |
|---|---|---|---|
| **WireMock** | Change base URL via env/build flag | CI pipelines, Java/Spring backends, record-replay | WireMock standalone / Docker |
| **Mockoon** | Change base URL | Quick setup, visual editing, small teams | Mockoon CLI |
| **json-server** | Change base URL | Simple REST; zero-config | json-server |
| **Requestly proxy** | None (device/sim proxy setting) | Real devices, no source access, HTTPS intercept | Requestly Desktop |
| **App mock mode** | Already built-in | Teams that control the app codebase | Internal flag |

---

## Approach 1: WireMock (recommended for CI)

WireMock runs as an HTTP server. The app is pointed to WireMock instead of the real API via a
base URL environment variable. WireMock responds with pre-defined JSON stubs.

### Start WireMock

```bash
# Docker (recommended — no Java install needed)
docker run --rm -d \
  --name wiremock \
  -p 8080:8080 \
  -v $(pwd)/wiremock/__files:/home/wiremock/__files \
  -v $(pwd)/wiremock/mappings:/home/wiremock/mappings \
  wiremock/wiremock:latest

# Or standalone JAR
java -jar wiremock-standalone-3.x.x.jar --port 8080
```

### JSON stub mapping structure

```
project/
└── wiremock/
    ├── mappings/           # request→response rules (one JSON per endpoint/scenario)
    │   ├── products-list.json
    │   ├── products-empty.json   # test empty state
    │   └── server-error.json
    └── __files/            # response body files (large responses live here)
        └── products-response.json
```

```json
// wiremock/mappings/products-list.json — happy path
{
  "request": {
    "method": "GET",
    "urlPattern": "/api/v1/products.*"
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "bodyFileName": "products-response.json"
  }
}
```

```json
// wiremock/mappings/server-error.json — error state test
{
  "request": {
    "method": "GET",
    "urlPattern": "/api/v1/products/99999"
  },
  "response": {
    "status": 500,
    "body": "{\"error\": \"Internal Server Error\"}"
  }
}
```

```json
// wiremock/mappings/slow-response.json — slow network simulation
{
  "request": {
    "method": "GET",
    "urlPattern": "/api/v1/search.*"
  },
  "response": {
    "status": 200,
    "bodyFileName": "search-response.json",
    "fixedDelayMilliseconds": 2000
  }
}
```

### Configure the app to use WireMock

```bash
# Android emulator: 10.0.2.2 → host machine localhost
# iOS simulator: 127.0.0.1 works (shares host network)

# Pass base URL via environment variable (most common pattern)
export API_BASE_URL=http://10.0.2.2:8080   # Android emulator
export API_BASE_URL=http://127.0.0.1:8080  # iOS simulator

# OR: use a debug/test build flavor that reads BASE_URL from BuildConfig
# OR: use ADB to set a system property the app reads
adb shell setprop debug.app.api_url http://10.0.2.2:8080
```

### Maestro flow using mocked API

> ⚠️ A flow-level `env:` block only defines **Maestro variables** (`${API_BASE_URL}` inside the YAML).
> The app never sees it. To hand the URL to the app, pass it as a **launch argument** — documented
> `launchApp.arguments` (string/boolean/double/integer), read by the app via `intent.extras` (Android)
> / launch arguments (iOS). The app must be coded to honour it (debug builds only).

```yaml
# flows/product-list-empty-state.yaml
appId: com.example.app
env:
  MOCK_URL: http://10.0.2.2:8080       # Maestro variable (Android emulator → host)
---
- launchApp:
    clearState: true
    arguments:
      apiBaseUrl: ${MOCK_URL}          # app reads intent.extras?.getString("apiBaseUrl")
- assertVisible:
    text: "No products found"    # rendered from the empty-state JSON stub
```

Variable interpolation inside `arguments` values is UNVERIFIED — if it doesn't resolve, hard-code the
URL or use a mock-pointed build flavor.

### Partial mocking — proxy pass-through

Mock only specific endpoints; let everything else hit the real API:

```json
// mappings/passthrough.json — catch-all proxy to real API
{
  "priority": 10,
  "request": {
    "urlPattern": ".*"
  },
  "response": {
    "proxyBaseUrl": "https://api.example.com"
  }
}
```

WireMock does **not** match in file order. Give the catch-all a low priority (higher number, e.g.
`"priority": 10`) and leave targeted stubs at the default/higher priority (lower number wins); without
priorities, the most recently added matching stub wins. (From WireMock docs knowledge — re-check
https://wiremock.org/docs/stubbing/ ; UNVERIFIED this session.)

### WireMock scenario-based stateful mocking

Test flows that require different responses to the same endpoint:

```json
// First call → loading state
{
  "scenarioName": "Cart",
  "requiredScenarioState": "Started",
  "newScenarioState": "ItemAdded",
  "request": { "method": "GET", "url": "/api/v1/cart" },
  "response": { "status": 200, "body": "{\"items\":[]}" }
}
```

```json
// After add-to-cart → shows item
{
  "scenarioName": "Cart",
  "requiredScenarioState": "ItemAdded",
  "request": { "method": "GET", "url": "/api/v1/cart" },
  "response": { "status": 200, "body": "{\"items\":[{\"id\":1,\"name\":\"Widget\"}]}" }
}
```

---

## Approach 2: Mockoon CLI (zero-config for small teams)

```bash
# Install
npm install -g @mockoon/cli

# Create a mock environment from Mockoon GUI, export mockoon-data.json
# Then start headlessly
mockoon-cli start --data mockoon-data.json --port 3001

# In Maestro flow
env:
  API_BASE_URL: http://10.0.2.2:3001
```

Mockoon GUI (desktop app) lets you visually define routes and responses, then export the JSON for
CLI use in CI.

---

## Approach 3: Requestly — no app code change

Requestly runs a proxy on the desktop that the device routes through. No source code change needed.

```bash
# 1. Install Requestly Desktop (requestly.io)
# 2. Create HTTP rules (modify API responses, redirect URLs, inject delays)
# 3. Configure device proxy:
#    Android emulator: Settings → WiFi → Proxy → 10.0.2.2:8010
#    iOS simulator:    System Preferences → Network → Proxies → HTTP: 127.0.0.1:8010
# 4. Trust Requestly's SSL certificate on device (for HTTPS)
# 5. Run Maestro flows — requests intercepted transparently
```

Requestly also supports **Replay Mode**: record all network traffic from a real session, then replay
it deterministically in future Maestro runs.

---

## CI integration — Docker Compose

```yaml
# docker-compose.test.yml
services:
  wiremock:
    image: wiremock/wiremock:latest
    ports: ["8080:8080"]
    volumes:
      - ./wiremock/__files:/home/wiremock/__files
      - ./wiremock/mappings:/home/wiremock/mappings
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/__admin/health"]
      interval: 5s
      timeout: 3s
      retries: 5
```

```yaml
# .github/workflows/maestro-tests.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start WireMock
        run: docker compose -f docker-compose.test.yml up -d && sleep 3

      - name: Enable KVM
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules && sudo udevadm trigger --name-match=kvm

      - name: Run Maestro tests (with mock API)
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          arch: x86_64
          script: |
            adb install -r build/app-debug.apk
            maestro test --format junit --output results.xml flows/

      - name: Stop WireMock
        if: always()
        run: docker compose -f docker-compose.test.yml down

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: maestro-results
          path: results.xml
```

---

## Scenarios to always test with mocking

| Scenario | Stub recipe |
|---|---|
| Empty list | `status: 200`, body `{ "items": [] }` |
| Server error | `status: 500` |
| Auth expired | `status: 401` |
| Rate limited | `status: 429` |
| Slow network | `fixedDelayMilliseconds: 3000` |
| Large payload | body with 100+ items |
| Partial failure | Mix of successful and failed items in one response |

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| App can't reach WireMock on emulator | Using `localhost` instead of `10.0.2.2` | Change base URL to `http://10.0.2.2:8080` in emulator |
| HTTPS requests not intercepted | App uses cert pinning or HTTPS without trust override | Use Requestly with cert installed, or configure app to allow test certs |
| WireMock returns 404 for all requests | Mapping files not loaded | Check `mappings/` volume mount; visit `localhost:8080/__admin/mappings` |
| Stub matched wrong request | Overlapping `urlPattern` | Make patterns more specific; check WireMock logs at `/__admin/requests` |
| iOS simulator can't reach `10.0.2.2` | iOS uses `127.0.0.1` not `10.0.2.2` | Use `127.0.0.1` for iOS simulator; `10.0.2.2` for Android emulator |

## Sources
- https://maestro.dev/blog/guide-to-maestro-ui-testing-with-api-mocking-using-wiremock
- https://github.com/edgarmiro/maestro-tests-with-mocks
- https://medium.com/trendyol-tech/building-scalable-android-tests-with-maestro-structure-mocking-and-authentication-4920b498c832
- https://yrkan.com/blog/mock-servers-mobile-dev/
- https://wiremock.org/docs/
- https://mockoon.com/cli/
- https://requestly.io/docs/
