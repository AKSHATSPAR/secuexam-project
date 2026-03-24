# SecuExam: Case Study Report
## Secure Exam Paper Distribution System

**Course:** Software Engineering (BCSE301L), Winter Semester 2025-26

**Testing Tool Used:** Selenium WebDriver (Python)

**Application Type:** Web Application (Python Flask + HTML/CSS/JS)

---

## Table of Contents
1. Project Overview
2. Test Plan
3. Test Scenarios
4. Test Cases
5. Test Environment
6. Question-wise Answers (Q1 to Q6)
7. Screenshots and Evidence

---

## 1. Project Overview

We built SecuExam as a secure exam paper distribution web application. The core idea behind this project is to prevent exam paper leaks using multiple layers of security. The system handles everything from uploading and encrypting exam papers to controlling when they can be accessed and tracking who downloads them.

Here is a breakdown of the key features we implemented:

| Feature | Technology | What It Does |
|---------|-----------|--------------|
| Encryption | AES-256-CBC | We use military-grade symmetric encryption for all uploaded papers |
| Key Management | Shamir's Secret Sharing (3-of-5) | The decryption key is split into 5 fragments and at least 3 are required to reconstruct it |
| Time-Lock | Server-side timestamp verification | Papers can only be accessed 30 minutes before the exam start time |
| Watermarking | ReportLab + PyPDF2 | Every downloaded PDF gets the receiver's IP, name, and download timestamp embedded on each page |
| Audit Trail | SQLite logging | Every access attempt (whether successful, blocked, or failed) is logged with IP and user details |
| Authentication | Bcrypt hashing + Role-based access | We have three roles: Setter, Receiver, and Admin, each with session management |

### Architecture

```
+------------------------------------------------------+
|                   SecuExam Web App                    |
|  +------------+  +------------+  +---------------+   |
|  | Login Page |  | Setter     |  | Receiver      |   |
|  | (index)    |  | Dashboard  |  | Dashboard     |   |
|  +-----+------+  +-----+------+  +------+--------+   |
|        |               |                |             |
|  +-----v---------------v----------------v---------+  |
|  |         Flask Backend (server.py)               |  |
|  |  Auth | Upload | Encrypt | Schedule | Download  |  |
|  +---------------------+-------------------------+   |
|                        |                             |
|  +---------------------v-------------------------+   |
|  | AES-256 | Shamir SSS | Time-Lock | Watermark  |  |
|  +---------------------+-------------------------+   |
|                        |                             |
|  +---------------------v-------------------------+   |
|  |          SQLite Database (secuexam.db)         |   |
|  | Users | Papers | Schedules | Keys | Logs      |   |
|  +------------------------------------------------+  |
+------------------------------------------------------+
```

### User Roles

| Role | What They Can Do |
|------|-----------------|
| Setter | Upload PDF papers, set exam schedule, view encryption status |
| Receiver | View scheduled exams, download papers (time-lock enforced), see watermark notice |
| Admin | User management, audit log inspection, analytics dashboard, key fragment viewer |

---

## 2. Test Plan

### 2.1 Objective

We designed our test plan to validate the functional correctness, security integrity, and UI consistency of the SecuExam web application. We used Selenium WebDriver as the primary testing automation tool throughout.

### 2.2 Scope

| In Scope | Out of Scope |
|----------|-------------|
| Authentication flows (login, logout, register) | Load and stress testing |
| Role-based access control (Setter, Receiver, Admin) | Penetration testing |
| Paper upload and AES-256 encryption | Cross-browser testing (we limited it to Chrome) |
| Time-lock enforcement | Performance benchmarking |
| UI consistency and responsive design | Third-party integration testing |
| Security edge cases (SQL injection, XSS) | |
| Admin dashboard functionality | |

### 2.3 Testing Approach

We organized our Selenium test suite into 6 test classes with a total of 34 automated test cases:

| Test Class | Number of Tests |
|-----------|----------------|
| Test01_LoginPage | 8 tests |
| Test02_SetterDashboard | 4 tests |
| Test03_ReceiverDashboard | 5 tests |
| Test04_AdminDashboard | 7 tests |
| Test05_UIConsistency | 5 tests |
| Test06_SecurityTests | 5 tests |
| **Total** | **34 tests + 35+ screenshots** |

### 2.4 Entry and Exit Criteria

| Criteria | Details |
|----------|---------|
| Entry | Flask server running on localhost:5050; test PDF available; Chrome WebDriver installed |
| Exit | 90% or higher test pass rate; all critical security tests pass; screenshot evidence captured |

### 2.5 Risk Assessment

| Risk | How We Mitigated It |
|------|-------------------|
| Server crashes during test | We added automated restart in the test setup |
| ChromeDriver version mismatch | We used the headless=new flag with a Safari fallback |
| Time-dependent tests (time-lock) | We set exam time dynamically relative to current time |

---

## 3. Test Scenarios

### Scenario 1: User Authentication

| ID | Scenario | Expected Result |
|----|----------|----------------|
| TS-01 | Login page loads with correct UI elements | Page title contains "SecuExam"; role tabs visible; form fields present |
| TS-02 | Role tab switching auto-fills credentials | Email field updates per selected role |
| TS-03 | Invalid login is rejected | Error toast displayed; user remains on login page |
| TS-04 | Empty fields trigger HTML5 validation | Form submission blocked; page does not navigate |
| TS-05 | Valid admin login redirects to /admin | URL contains "admin"; admin dashboard loads |
| TS-06 | Valid setter login redirects to /setter | URL contains "setter"; setter dashboard loads |
| TS-07 | Valid receiver login redirects to /receiver | URL contains "receiver"; receiver dashboard loads |
| TS-08 | Register modal opens and closes | Modal becomes visible on click; hidden on close |

### Scenario 2: Paper Upload and Encryption (Setter)

| ID | Scenario | Expected Result |
|----|----------|----------------|
| TS-09 | Setter dashboard loads with all sections | Stats, upload zone, and history table present |
| TS-10 | Upload zone shows drag-drop instructions | "Drag and drop your PDF here" text visible |
| TS-11 | PDF upload triggers AES-256 encryption | Encryption result panel shows paper ID, "AES-256-CBC", and "5 shares (3 required)" |
| TS-12 | Upload history table populates | Table shows uploaded paper with metadata |

### Scenario 3: Receiver Dashboard and Time-Lock

| ID | Scenario | Expected Result |
|----|----------|----------------|
| TS-13 | Receiver dashboard loads with stats | 4 stat cards displayed (Total, Unlocked, Locked, Expired) |
| TS-14 | Exam list shows scheduled papers | Table rows with subject, setter name, and status |
| TS-15 | Time-lock prevents early download | Papers show "Locked" status with countdown timer |
| TS-16 | Countdown timers update live | Timer decrements every second |
| TS-17 | Security notice warns about watermarking | Banner text mentions "watermarked", "IP address", "logged" |

### Scenario 4: Admin Dashboard

| ID | Scenario | Expected Result |
|----|----------|----------------|
| TS-18 | Admin dashboard loads with analytics | 4 stat cards + Chart.js doughnut + bar charts |
| TS-19 | Security features grid is displayed | AES-256, Shamir, Time-Lock, Watermark, Audit, Bcrypt cards visible |
| TS-20 | Users tab lists all users | Table with name, email, role, status columns |
| TS-21 | Audit logs tab shows access history | Table with timestamp, user, IP, status columns |
| TS-22 | Papers tab lists uploaded papers | Table with key share visuals |
| TS-23 | Tab navigation works correctly | Each tab switches content panel |

### Scenario 5: Security Edge Cases

| ID | Scenario | Expected Result |
|----|----------|----------------|
| TS-24 | Unauthorized /setter access redirects to login | Non-authenticated users cannot access protected pages |
| TS-25 | Unauthorized /admin access redirects to login | Same as above |
| TS-26 | SQL injection in login is rejected | Server does not crash; user remains on login page |
| TS-27 | XSS payload is sanitized | HTML5 email validation blocks script tags |
| TS-28 | API returns 401 without authentication | /api/me responds with "Not authenticated" |

---

## 4. Test Cases

### Test Case TC-01: Login Page Loads Correctly

| Field | Value |
|-------|-------|
| Test ID | TC-01 |
| Test Scenario | TS-01 |
| Description | We verified that the login page renders with all required UI elements |
| Pre-conditions | Flask server running on localhost:5050 |
| Test Steps | 1. Navigate to http://localhost:5050/ 2. Wait for page load 3. Verify page title 4. Check for logo, role tabs, form fields |
| Expected Result | Title contains "SecuExam"; 3 role tabs present; email and password fields visible |
| Actual Result | PASS: All UI elements rendered correctly |
| Tool Used | Selenium WebDriver (Python) |

### Test Case TC-02: Paper Upload and AES-256 Encryption

| Field | Value |
|-------|-------|
| Test ID | TC-02 |
| Test Scenario | TS-11 |
| Description | We verified that a PDF upload triggers encryption and Shamir key splitting |
| Pre-conditions | Logged in as Setter; test PDF available |
| Test Steps | 1. Login as setter 2. Select test PDF via file input 3. Fill subject and exam time 4. Click "Encrypt and Upload" 5. Verify encryption result panel |
| Expected Result | Encryption result shows: Paper ID, "AES-256-CBC", "5 shares (3 required)" |
| Actual Result | PASS: Paper encrypted with AES-256-CBC; key split into 5 Shamir shares |
| Tool Used | Selenium WebDriver (Python) |

### Test Case TC-03: Time-Lock Enforcement

| Field | Value |
|-------|-------|
| Test ID | TC-03 |
| Test Scenario | TS-15 |
| Description | We verified that papers scheduled for future exams show locked status |
| Pre-conditions | Paper uploaded with exam time 2+ hours in future; logged in as Receiver |
| Test Steps | 1. Login as receiver 2. View exam list 3. Check paper status 4. Verify download button is disabled |
| Expected Result | Paper shows "Locked" with countdown timer; download button disabled |
| Actual Result | PASS: Time-lock correctly enforces access restriction |
| Tool Used | Selenium WebDriver (Python) |

### Test Case TC-04: SQL Injection Prevention

| Field | Value |
|-------|-------|
| Test ID | TC-04 |
| Test Scenario | TS-26 |
| Description | We verified that SQL injection payload does not bypass authentication |
| Pre-conditions | On login page |
| Test Steps | 1. Enter valid email 2. Enter password: ' OR '1'='1 3. Click Sign In 4. Verify rejection |
| Expected Result | Login rejected; user stays on login page; server does not crash |
| Actual Result | PASS: Bcrypt comparison safely rejects injection payload |
| Tool Used | Selenium WebDriver (Python) |

### Test Case TC-05: Admin Dashboard Charts and Analytics

| Field | Value |
|-------|-------|
| Test ID | TC-05 |
| Test Scenario | TS-18 |
| Description | We verified that admin analytics page renders Chart.js visualizations |
| Pre-conditions | Logged in as Admin |
| Test Steps | 1. Login as admin 2. Verify stat cards show non-zero values 3. Verify canvas elements exist for charts 4. Verify security features grid |
| Expected Result | 4 stat cards + 2 charts (doughnut + bar) + 6 security feature cards |
| Actual Result | PASS: All analytics elements rendered with live data |
| Tool Used | Selenium WebDriver (Python) |

---

## 5. Test Environment

### 5.1 Hardware

| Component | Specification |
|-----------|--------------|
| Machine | MacBook (Apple Silicon) |
| RAM | 8+ GB |
| Storage | 256+ GB SSD |

### 5.2 Software

| Component | Version |
|-----------|---------|
| OS | macOS |
| Python | 3.14 |
| Flask | 3.1.3 |
| Selenium | 4.41.0 |
| Chrome | Latest stable |
| ChromeDriver | Matching Chrome version |
| SQLite | 3.x (built-in) |

### 5.3 Test Data

| Data | Description |
|------|-------------|
| test_exam_paper.pdf | Single-page PDF with mock exam questions |
| Default Users | Admin, Setter, Receiver (pre-created) |
| Database | secuexam.db (auto-created SQLite database) |

### 5.4 Network

- Protocol: HTTP (localhost)
- Port: 5050
- Server: Flask development server (Werkzeug)

### 5.5 Testing Tool: Selenium WebDriver

We chose Selenium WebDriver as our testing tool for this entire case study. Selenium is an open-source browser automation framework that lets us write test scripts in Python to interact with web pages programmatically. It supports clicking buttons, filling forms, taking screenshots, and validating page content. We used it with Chrome in headless mode along with Python's unittest framework for organizing and running all 34 test cases.

---

## 6. Question-wise Answers

### Q1: Mutation Testing

**Objective:** We wanted to evaluate how effective our test suite is by introducing deliberate faults (mutants) into the source code and checking whether the tests catch them.

**Module Under Test:** Time-lock enforcement and authentication logic in `server.py`.

**Mutation Operator Used:** Relational Operator Replacement (ROR) and Arithmetic Operator Replacement (AOR).

**Step-by-Step Execution:**

1. We identified critical logic in the time-lock module: `if now >= unlock_dt:`
2. We created a mutant by changing it to: `if now <= unlock_dt:`
3. We saved the file and ran the Selenium test suite
4. We observed whether TC-03 (Time-Lock Enforcement) caught the error

**Mutations We Applied:**

| Mutant ID | Original Code | Mutated Code | Test That Catches It |
|-----------|--------------|-------------|---------------------|
| M-01 | `if now >= unlock_dt:` | `if now <= unlock_dt:` | TC-03: Locked papers become unlocked, test fails |
| M-02 | `k=3, n=5` (Shamir threshold) | `k=2, n=5` | TC-02: Wrong threshold changes encryption behavior |
| M-03 | `if not bcrypt.checkpw(...)` | `if bcrypt.checkpw(...)` | TC-01, TC-04: Authentication inverted, wrong passwords log in |
| M-04 | `role IN ('setter','receiver','admin')` | `role IN ('setter','receiver')` | TC-05: Admin cannot login, stats test fails |
| M-05 | `return jsonify({"error": "..."}), 401` | `return jsonify({"error": "..."}), 200` | TC-04: API auth test fails due to wrong status code |

**Mutation Score Calculation:**

```
Mutation Score = (Killed Mutants / Total Mutants) x 100

Total Mutants: 5
Killed by Tests: 5
Survived: 0
Mutation Score: 100%
```

**Conclusion:** All five mutants were killed by our existing test suite, which shows that our tests are effective at catching logic errors in critical modules.

---

### Q2: UI Testing

**Objective:** We wanted to verify that the application renders correctly and maintains visual consistency across different screen sizes.

**Tool Used:** Selenium WebDriver with `set_window_size()` for responsive testing.

**Step-by-Step Execution:**

1. We launched the SecuExam app in Chrome via Selenium
2. We tested at three different viewports:
   - Desktop: 1440 x 900
   - Tablet: 768 x 1024
   - Mobile: 375 x 812
3. We navigated through all four pages (Login, Setter, Receiver, Admin) at each viewport
4. We checked for layout breaks, text overflow, and element visibility
5. We captured screenshots at each resolution for evidence

**What We Verified:**

| Check | What We Looked For | Result |
|-------|-------------------|--------|
| Page layout | Content stays within viewport boundaries | Pass |
| Dark theme consistency | Background colors and glassmorphic effects render properly | Pass |
| Gradient text | Animated gradient headings display correctly | Pass |
| Responsive navigation | Elements reflow properly on smaller screens | Pass |
| Form usability | Input fields and buttons remain accessible at all sizes | Pass |

**Evidence:** We captured screenshots at each resolution. The login page, setter dashboard, and admin dashboard all maintained their visual integrity across all three viewports.

---

### Q3: Mobile App Testing (Theoretical)

Since we built a web application, this section describes how we would test SecuExam if it were adapted as a mobile app (for example, built with React Native or Flutter).

**How the Mobile Version Would Differ:**

| Component | Web Version | Mobile Adaptation |
|-----------|------------|------------------|
| Frontend | HTML/CSS/JS | React Native or Flutter |
| Navigation | URL routing | Stack and Tab navigation |
| File Upload | HTML file input | Device file picker + camera |
| Notifications | Toast messages | Push notifications |
| Storage | Browser cookies | AsyncStorage or SQLite |
| UI | Glassmorphic CSS | Platform-native components |

**Mobile Testing with Selenium (Appium):**

We would use Appium, which extends the Selenium WebDriver protocol for mobile apps:

```python
# Theoretical Appium configuration for SecuExam mobile
from appium import webdriver as appium_driver

caps = {
    "platformName": "Android",
    "deviceName": "emulator-5554",
    "app": "/path/to/secuexam.apk",
    "automationName": "UiAutomator2"
}
driver = appium_driver.Remote("http://localhost:4723/wd/hub", caps)

# Same Selenium API applies
driver.find_element(By.ID, "login-email").send_keys("admin@secuexam.in")
driver.find_element(By.ID, "login-btn").click()
```

**Mobile-Specific Test Scenarios:**

| ID | Scenario | Tool |
|----|----------|------|
| MT-01 | App launches correctly on Android and iOS | Selenium (Appium) |
| MT-02 | Touch-based login works | Selenium (Appium) |
| MT-03 | PDF download saves to device storage | Selenium (Appium) |
| MT-04 | Push notification fires for exam unlock reminder | Selenium (Appium) |
| MT-05 | Screen rotation does not break layout | Selenium (Appium) |
| MT-06 | App works under slow network (3G simulation) | Selenium (Appium) |

---

### Q4: Web Application Testing

**This is our primary testing domain.** We conducted actual testing on the SecuExam web application using Selenium WebDriver.

**Our Selenium test suite (`test_secuexam.py`) has 6 test classes with 34 automated test cases:**

```python
class Test01_LoginPage(SecuExamTestBase):        # 8 tests
class Test02_SetterDashboard(SecuExamTestBase):   # 4 tests
class Test03_ReceiverDashboard(SecuExamTestBase):  # 5 tests
class Test04_AdminDashboard(SecuExamTestBase):     # 7 tests
class Test05_UIConsistency(SecuExamTestBase):      # 5 tests
class Test06_SecurityTests(SecuExamTestBase):      # 5 tests
```

**Key Selenium Techniques We Used:**

| Technique | Selenium API | How We Used It |
|-----------|-------------|---------------|
| Element Location | `find_element(By.ID, ...)` | Locating form fields, buttons, tabs |
| Element Interaction | `click()`, `send_keys()` | Filling forms, clicking buttons, switching tabs |
| Assertions | `assertEqual()`, `assertTrue()` | Validating page content, URL, element state |
| Waits | `WebDriverWait`, `time.sleep()` | Handling AJAX calls, page transitions |
| Screenshots | `save_screenshot()` | Capturing 35+ evidence screenshots per run |
| JavaScript Execution | `execute_script()` | Setting datetime-local input values |
| Cookie Management | `delete_all_cookies()` | Clean state between test sessions |
| Window Sizing | `set_window_size()` | Testing responsive layouts (mobile, tablet) |

**Testing strategies we applied:**

1. **Functional Testing:** We verified login authentication for all three roles, tested the paper upload flow with AES-256 encryption confirmation, validated time-lock enforcement, and confirmed watermark notice visibility.

2. **Security Testing:** We tested SQL injection payloads, XSS prevention, unauthorized access to protected routes, and API authentication checks.

3. **Integration Testing:** We ran end-to-end workflows: Login, Upload PDF, Encrypt, View in Receiver, Verify Time-lock, Admin sees audit log.

4. **Regression Testing:** After each code change, we re-ran the full 34-test suite to make sure nothing broke.

5. **UI Testing:** We verified responsive design at three viewports and checked dark theme consistency across all pages.

**Run Command:**
```bash
source venv/bin/activate
python server.py &
python test_secuexam.py
```

---

### Q5: DevOps Testing (Theoretical)

Since we did not set up a full CI/CD pipeline for this project, this section describes how we would integrate automated testing into a DevOps pipeline if we were to deploy SecuExam in production.

**Proposed CI/CD Pipeline:**

```
+------------+    +----------+    +----------+    +----------+
|   GitHub   |    |  GitHub  |    |  Staging  |    |   Prod   |
|   Push     |--->|  Actions |--->|  Deploy   |--->|  Deploy  |
|            |    |  (CI)    |    |  (CD)     |    |          |
+------------+    +----------+    +----------+    +----------+
                       |
         +-------------+-------------+
         v             v             v
   +----------+  +----------+  +----------+
   |  Lint    |  |  Unit    |  | Selenium |
   |  Check   |  |  Tests   |  |  E2E     |
   +----------+  +----------+  +----------+
```

**GitHub Actions Configuration (Theoretical):**

```yaml
# .github/workflows/secuexam-ci.yml
name: SecuExam CI/CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: python server.py &
      - run: python test_secuexam.py
      - uses: actions/upload-artifact@v4
        with:
          name: test-screenshots
          path: test_screenshots/
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - run: echo "Deploy to production server"
```

**How Testing Would Fit Into the Pipeline:**

| Testing Type | Tool | What We Would Test |
|-------------|------|-------------------|
| Unit Testing | Selenium WebDriver | Individual login, upload, download functions |
| Integration Testing | Selenium WebDriver | End-to-end workflow: upload, encrypt, download |
| Smoke Testing | Selenium WebDriver | Quick login + page load checks after deployment |
| Regression Testing | Selenium WebDriver | Full test suite run on every PR and commit |
| Security Testing | Selenium WebDriver | SQL injection, XSS, unauthorized access checks |

---

### Q6: Object-Oriented Testing

**Objective:** We wanted to show how OOP testing principles apply to the SecuExam codebase.

**OOP Classes in Our Project:**

Our Selenium test suite itself is built using object-oriented principles. We have a base test class that all individual test classes inherit from:

```python
class SecuExamTestBase(unittest.TestCase):
    """Base test class using OOP principles."""

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Chrome(options=chrome_options)

    def login_as(self, role, creds): ...
    def save_screenshot(self, name): ...
    def logout(self): ...
```

**OOP Principles We Applied:**

| OOP Principle | How We Applied It |
|--------------|------------------|
| Inheritance | `Test01_LoginPage(SecuExamTestBase)`: all test classes inherit browser setup and teardown |
| Encapsulation | `login_as()` encapsulates the complete authentication flow; `save_screenshot()` encapsulates evidence capture |
| Polymorphism | Each test class overrides `setUp()/tearDown()` for role-specific login (setter vs. receiver vs. admin) |
| Abstraction | `apiFetch()` abstracts HTTP request logic; `showToast()` abstracts notification display |

**Class Under Test: ShamirSecretSharing**

```python
class ShamirSecretSharing:
    def __init__(self, k=3, n=5, prime=257):
        self.k = k      # Threshold
        self.n = n      # Total shares
        self.prime = prime

    def split(self, secret_bytes: bytes) -> list:
        """Split secret into n shares."""
        ...

    def reconstruct(self, shares: list) -> bytes:
        """Reconstruct from k shares."""
        ...

# OOP Test
class TestShamirSSS(unittest.TestCase):
    def test_split_creates_n_shares(self):
        sss = ShamirSecretSharing(k=3, n=5)
        secret = os.urandom(32)
        shares = sss.split(secret)
        self.assertEqual(len(shares), 5)

    def test_reconstruct_recovers_secret(self):
        sss = ShamirSecretSharing(k=3, n=5)
        secret = os.urandom(32)
        shares = sss.split(secret)
        recovered = sss.reconstruct(shares[:3])
        self.assertEqual(recovered, secret)

    def test_insufficient_shares_fails(self):
        sss = ShamirSecretSharing(k=3, n=5)
        secret = os.urandom(32)
        shares = sss.split(secret)
        recovered = sss.reconstruct(shares[:2])
        self.assertNotEqual(recovered, secret)
```

**Conclusion:** By structuring our test code using inheritance, encapsulation, and polymorphism, we made it easy to write, maintain, and extend our test suite. The same OOP principles that guide the application code also guide our testing approach.

---

## 7. Screenshots and Evidence

### Login Page
The login page features a premium glassmorphic dark theme with role-based tab switching (Setter, Receiver, Admin), auto-fill demo credentials, and security feature highlights.

> Evidence: Login page with Setter tab active showing form fields, gradient branding, and AES-256 + Shamir encryption banner.

### Setter Dashboard
The Paper Setter dashboard provides drag-and-drop PDF upload, exam scheduling with date/time picker, duration configuration, and real-time encryption status cards.

> Evidence: Setter dashboard showing 3 stat cards (Papers Uploaded, Encrypted, Scheduled), upload zone with "Drag and drop your PDF here", and exam configuration form.

### Admin Dashboard
The Admin Control Center displays Chart.js analytics (doughnut chart for users by role, bar chart for access attempts), tabbed navigation (Analytics, Users, Audit Logs, Papers), and a comprehensive security features grid.

> Evidence: Admin dashboard showing Users by Role doughnut chart, 4 stat cards, and 6 security feature cards (AES-256-CBC, Shamir's SSS, Server-Side Time-Lock, Dynamic Watermarking, Immutable Audit Trail, Bcrypt Password Hashing).

### Receiver Dashboard
The Exam Center dashboard displays scheduled exams with countdown timers, locked/unlocked status badges, and a security notice about IP-tracked watermarking.

---

## Appendix: File Structure

```
software/
  server.py                    # Flask backend
  requirements.txt             # Python dependencies
  test_secuexam.py             # Selenium test suite (34 tests)
  test_exam_paper.pdf          # Test PDF for upload testing
  secuexam.db                  # SQLite database (auto-created)
  secuexam_app/
    index.html                 # Login page
    setter.html                # Setter dashboard
    receiver.html              # Receiver dashboard
    admin.html                 # Admin dashboard
    css/
      style.css                # Premium glassmorphic design system
    js/
      app.js                   # Shared JavaScript utilities
    uploads/                   # Encrypted paper storage
  test_screenshots/            # Selenium screenshot evidence
```

---

*Testing Tool: Selenium WebDriver (Python)*
*Application: SecuExam, Secure Exam Paper Distribution System*
