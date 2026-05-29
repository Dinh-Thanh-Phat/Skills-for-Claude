# Requirements — [Feature Name]
<!-- Scenario A input template. Fill this out before invoking qa-test-generation. -->

## Feature
**Name:** [e.g., "User Login", "Exchange Market Table", "Crypto Buy Flow"]
**URL / Page:** [e.g., https://app.example.com/login]
**Date:** [YYYY-MM-DD]

---

## User Story
As a **[user type: guest / logged-in user / admin]**,
I want to **[primary action]**,
so that **[business benefit]**.

---

## Acceptance Criteria
- [ ] [Condition 1 — what must be true for the feature to work]
- [ ] [Condition 2]
- [ ] [Condition 3]

---

## Key Flows to Cover

### Happy Path
1. [Start state]
2. [User action]
3. [Expected result]

### Error Cases
| Input / Condition | Expected Error |
|-------------------|----------------|
| [e.g., empty email field] | [e.g., "Email is required" shown] |
| [e.g., wrong password] | [e.g., "Invalid credentials" toast] |

### Edge Cases
- [e.g., session timeout during flow]
- [e.g., network error mid-submit]
- [e.g., duplicate submission]

---

## Test Data Needed
| Field | Valid Value | Invalid Value |
|-------|-------------|---------------|
| [e.g., Email] | [e.g., user@test.com] | [e.g., notanemail] |
| [e.g., Password] | [e.g., Test@1234] | [e.g., empty string] |

---

## Constraints
- **Auth required:** Yes / No
- **Test environment URL:** [URL]
- **Special setup:** [e.g., "Need account with KYC verified status"]

---

## Out of Scope
- [What NOT to test in this session]
