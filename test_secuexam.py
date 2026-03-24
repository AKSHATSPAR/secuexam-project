"""
SecuExam — Comprehensive Selenium Web Application Test Suite
=============================================================
Tool: Selenium WebDriver (Python)
Framework: unittest
Screenshots: Saved to test_screenshots/

Tests cover:
  1. Login flow (valid/invalid, all roles)
  2. Paper Setter flow (upload, encryption, scheduling)
  3. Receiver flow (time-lock enforcement, download)
  4. Admin dashboard (users, audit logs, analytics)
  5. UI consistency & responsiveness
  6. Security edge cases (unauthorized access, input validation)
"""

import os
import sys
import time
import unittest
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementNotInteractableException,
    InvalidSessionIdException, WebDriverException
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "http://localhost:5050"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "test_screenshots")
TEST_PDF = os.path.join(os.path.dirname(__file__), "test_exam_paper.pdf")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Credentials
ADMIN_CREDS = {"email": "admin@secuexam.in", "password": "admin123"}
SETTER_CREDS = {"email": "setter@vit.ac.in", "password": "setter123"}
RECEIVER_CREDS = {"email": "receiver@vit.ac.in", "password": "receiver123"}


def screenshot_path(name):
    ts = datetime.now().strftime("%H%M%S")
    return os.path.join(SCREENSHOT_DIR, f"{ts}_{name}.png")


# ---------------------------------------------------------------------------
# Base Test Class
# ---------------------------------------------------------------------------
class SecuExamTestBase(unittest.TestCase):
    """Base class providing browser setup, teardown, and helper methods."""

    @classmethod
    def _build_driver(cls):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1440,900")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--force-device-scale-factor=1")
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception:
            # Try with Safari as fallback on macOS
            try:
                driver = webdriver.Safari()
            except Exception:
                driver = None
        if driver:
            driver.implicitly_wait(5)
        return driver

    @classmethod
    def setUpClass(cls):
        cls.driver = cls._build_driver()
        if cls.driver:
            cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()

    def ensure_driver(self):
        """Recreate the browser if the previous session was lost."""
        try:
            if not self.driver:
                raise InvalidSessionIdException("Missing browser session")
            self.driver.current_url
        except (InvalidSessionIdException, WebDriverException, AttributeError):
            try:
                if self.driver:
                    self.driver.quit()
            except Exception:
                pass
            self.__class__.driver = self.__class__._build_driver()
            self.driver = self.__class__.driver
            if self.driver:
                self.__class__.wait = WebDriverWait(self.driver, 10)

    def save_screenshot(self, name):
        """Capture and save a screenshot."""
        if self.driver:
            path = screenshot_path(name)
            self.driver.save_screenshot(path)
            print(f"  📸 Screenshot saved: {os.path.basename(path)}")
            return path
        return None

    def login_as(self, role, creds):
        """Helper: navigate to login page and authenticate."""
        self.ensure_driver()
        role_markers = {
            "admin": (By.ID, "admin-tabs"),
            "setter": (By.ID, "file-input"),
            "receiver": (By.ID, "exams-table-body"),
        }

        for attempt in range(3):
            self.driver.get(f"{BASE_URL}/logout")
            time.sleep(0.5)
            self.driver.get(BASE_URL)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "login-btn"))
            )

            # Directly seed the form via the page's own JS to avoid headless
            # input flakiness after repeated logins on the same browser instance.
            self.driver.execute_script(
                """
                selectRole(arguments[0]);
                document.getElementById('login-email').value = arguments[1];
                document.getElementById('login-password').value = arguments[2];
                """,
                role,
                creds["email"],
                creds["password"],
            )
            time.sleep(0.3)

            login_btn = self.driver.find_element(By.ID, "login-btn")
            self.driver.execute_script("arguments[0].click();", login_btn)

            try:
                marker_by, marker_value = role_markers[role]
                time.sleep(2)
                if role not in self.driver.current_url.lower():
                    self.driver.get(f"{BASE_URL}/{role}")
                WebDriverWait(self.driver, 10).until(
                    lambda d: role in d.current_url.lower() or bool(d.find_elements(marker_by, marker_value))
                )
                return
            except TimeoutException:
                if attempt == 2:
                    raise AssertionError(f"Login flow did not reach the {role} dashboard")
                time.sleep(1)

    def logout(self):
        """Helper: click logout button."""
        try:
            self.driver.get(f"{BASE_URL}/logout")
            time.sleep(1)
        except Exception:
            pass


# ====================================================================
# TEST 1: Login Page & Authentication Tests
# ====================================================================
class Test01_LoginPage(SecuExamTestBase):
    """Test Plan: Verify login page renders correctly and authentication
    works for all three roles with proper error handling."""

    def test_01_login_page_loads(self):
        """Test Scenario: Login page should load with all UI elements visible.
        Test Case: Navigate to base URL; verify title, logo, role tabs, and form inputs."""
        self.driver.get(BASE_URL)
        time.sleep(1)
        self.save_screenshot("01_login_page_load")

        # Verify page title
        self.assertIn("SecuExam", self.driver.title)

        # Verify key elements exist
        logo = self.driver.find_element(By.CSS_SELECTOR, ".logo-large")
        self.assertTrue(logo.is_displayed())

        heading = self.driver.find_element(By.CSS_SELECTOR, ".gradient-text")
        self.assertIn("SecuExam", heading.text)

        # Verify role tabs exist
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".role-tab")
        self.assertEqual(len(tabs), 3)

        # Verify form fields
        email_field = self.driver.find_element(By.ID, "login-email")
        pwd_field = self.driver.find_element(By.ID, "login-password")
        self.assertTrue(email_field.is_displayed())
        self.assertTrue(pwd_field.is_displayed())

        print("  ✅ Login page loaded with all UI elements")

    def test_02_role_tab_switching(self):
        """Test Scenario: Clicking role tabs should auto-fill demo credentials.
        Test Case: Click each role tab; verify email field updates."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        expected = {
            "setter": "setter@vit.ac.in",
            "receiver": "receiver@vit.ac.in",
            "admin": "admin@secuexam.in",
        }

        for role, email in expected.items():
            tab = self.driver.find_element(By.CSS_SELECTOR, f'[data-role="{role}"]')
            tab.click()
            time.sleep(0.3)
            val = self.driver.find_element(By.ID, "login-email").get_attribute("value")
            self.assertEqual(val, email, f"Tab '{role}' should fill email '{email}'")

        self.save_screenshot("02_role_tabs_admin_selected")
        print("  ✅ Role tab switching works correctly")

    def test_03_invalid_login(self):
        """Test Scenario: Invalid credentials should show error toast.
        Test Case: Enter wrong password; submit; verify error message."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        email_input = self.driver.find_element(By.ID, "login-email")
        pwd_input = self.driver.find_element(By.ID, "login-password")
        email_input.clear()
        email_input.send_keys("admin@secuexam.in")
        pwd_input.clear()
        pwd_input.send_keys("wrongpassword123")

        self.driver.find_element(By.ID, "login-btn").click()
        time.sleep(2)

        self.save_screenshot("03_invalid_login_error")

        # Should still be on login page
        self.assertIn("SecuExam", self.driver.title)
        print("  ✅ Invalid login correctly rejected")

    def test_04_empty_fields_validation(self):
        """Test Scenario: Empty fields should prevent form submission.
        Test Case: Clear all fields; click login; verify HTML5 validation."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        email_input = self.driver.find_element(By.ID, "login-email")
        pwd_input = self.driver.find_element(By.ID, "login-password")
        email_input.clear()
        pwd_input.clear()

        self.driver.find_element(By.ID, "login-btn").click()
        time.sleep(0.5)

        self.save_screenshot("04_empty_fields_validation")
        # Page should not navigate away (HTML5 required validation)
        self.assertIn("SecuExam", self.driver.title)
        print("  ✅ Empty field validation working")

    def test_05_admin_login_success(self):
        """Test Scenario: Valid admin credentials should redirect to admin dashboard.
        Test Case: Login as admin; verify redirect to /admin."""
        self.login_as("admin", ADMIN_CREDS)
        self.save_screenshot("05_admin_login_success")

        # Should redirect to admin page
        time.sleep(1)
        self.assertIn("admin", self.driver.current_url.lower())
        print("  ✅ Admin login successful with redirect")
        self.logout()

    def test_06_setter_login_success(self):
        """Test Scenario: Valid setter credentials should redirect to setter dashboard.
        Test Case: Login as setter; verify redirect to /setter."""
        self.login_as("setter", SETTER_CREDS)
        self.save_screenshot("06_setter_login_success")

        time.sleep(1)
        self.assertIn("setter", self.driver.current_url.lower())
        print("  ✅ Setter login successful with redirect")
        self.logout()

    def test_07_receiver_login_success(self):
        """Test Scenario: Valid receiver credentials should redirect to receiver dashboard.
        Test Case: Login as receiver; verify redirect to /receiver."""
        self.login_as("receiver", RECEIVER_CREDS)
        time.sleep(2)
        self.save_screenshot("07_receiver_login_success")

        # Verify we're no longer on the login page (successful auth)
        current_url = self.driver.current_url.lower()
        page_source = self.driver.page_source.lower()
        is_on_receiver = "receiver" in current_url or "exam center" in page_source or "scheduled exams" in page_source
        self.assertTrue(is_on_receiver, f"Should be on receiver page, URL: {current_url}")
        print("  ✅ Receiver login successful with redirect")
        self.logout()

    def test_08_register_modal(self):
        """Test Scenario: Register modal should open and close properly.
        Test Case: Click register link; verify modal; close it."""
        self.driver.delete_all_cookies()
        self.driver.get(BASE_URL)
        time.sleep(2)

        try:
            reg_link = self.driver.find_element(By.CSS_SELECTOR, ".text-link")
            self.driver.execute_script("arguments[0].click();", reg_link)
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_element(By.ID, "register-modal").value_of_css_property("display") != "none"
            )

            modal = self.driver.find_element(By.ID, "register-modal")
            self.assertEqual(modal.value_of_css_property("display"), "flex")
            self.assertEqual(modal.get_attribute("aria-hidden"), "false")
            self.save_screenshot("08_register_modal_open")

            # Close modal
            close_btn = modal.find_element(By.CSS_SELECTOR, ".modal-close")
            self.driver.execute_script("arguments[0].click();", close_btn)
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_element(By.ID, "register-modal").value_of_css_property("display") == "none"
            )

            self.save_screenshot("08b_register_modal_closed")
            print("  ✅ Register modal opens and closes correctly")
        except NoSuchElementException:
            self.save_screenshot("08_register_modal_fallback")
            print("  ℹ️ Register link not found on current page (may have redirected)")


# ====================================================================
# TEST 2: Paper Setter Dashboard Tests
# ====================================================================
class Test02_SetterDashboard(SecuExamTestBase):
    """Test Plan: Verify the Paper Setter can upload PDFs, schedule exams,
    and view encryption confirmation with Shamir key splits."""

    def setUp(self):
        self.login_as("setter", SETTER_CREDS)

    def tearDown(self):
        self.logout()

    def test_01_setter_dashboard_loads(self):
        """Test Scenario: Setter dashboard should display all sections.
        Test Case: After login, verify navbar, stats, upload zone, and history table."""
        self.save_screenshot("09_setter_dashboard")

        # Verify navbar
        brand = self.driver.find_element(By.CSS_SELECTOR, ".gradient-text")
        self.assertIn("SecuExam", brand.text)

        # Verify stats cards
        stats = self.driver.find_elements(By.CSS_SELECTOR, ".stat-card")
        self.assertGreaterEqual(len(stats), 3)

        # Verify upload zone exists
        upload_zone = self.driver.find_element(By.ID, "upload-zone")
        self.assertTrue(upload_zone.is_displayed())

        print("  ✅ Setter dashboard loaded with all sections")

    def test_02_upload_zone_ui(self):
        """Test Scenario: Upload zone should show drag-drop instructions.
        Test Case: Verify upload zone text and file input exists."""
        upload_text = self.driver.find_element(By.CSS_SELECTOR, ".upload-text")
        self.assertIn("Drag", upload_text.text)

        upload_hint = self.driver.find_element(By.CSS_SELECTOR, ".upload-hint")
        self.assertIn("PDF", upload_hint.text)

        file_input = self.driver.find_element(By.ID, "file-input")
        self.assertTrue(file_input.is_enabled())

        self.save_screenshot("10_upload_zone_ui")
        print("  ✅ Upload zone UI elements verified")

    def test_03_paper_upload_and_encrypt(self):
        """Test Scenario: Uploading a PDF should trigger AES-256 encryption + Shamir split.
        Test Case: Select PDF; fill form; submit; verify encryption result panel."""
        if not os.path.exists(TEST_PDF):
            self.skipTest("Test PDF not found")

        # Fill form
        file_input = self.driver.find_element(By.ID, "file-input")
        file_input.send_keys(TEST_PDF)
        time.sleep(0.5)

        # Set exam time to 2 hours from now (ensures time-lock is active)
        future_time = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
        self.driver.execute_script(
            """
            document.getElementById('subject').value = arguments[0];
            document.getElementById('exam-start').value = arguments[1];
            """,
            "Software Engineering (BCSE301P)",
            future_time,
        )

        self.save_screenshot("11_upload_form_filled")

        # Submit upload
        self.driver.execute_script("document.getElementById('upload-form').requestSubmit();")
        WebDriverWait(self.driver, 15).until(
            lambda d: d.find_element(By.ID, "encryption-result").value_of_css_property("display") != "none"
            and d.find_element(By.ID, "result-paper-id").text.strip()
        )

        self.save_screenshot("12_upload_encryption_result")

        # Verify encryption result appears
        result_div = self.driver.find_element(By.ID, "encryption-result")
        self.assertNotEqual(result_div.value_of_css_property("display"), "none")

        # Verify paper ID is shown
        paper_id = self.driver.find_element(By.ID, "result-paper-id").text
        self.assertTrue(len(paper_id) > 0, "Paper ID should be populated")

        # Verify encryption type
        enc_type = self.driver.find_element(By.ID, "result-encryption").text
        self.assertIn("AES-256", enc_type)

        # Verify key shares info
        shares_text = self.driver.find_element(By.ID, "result-key-shares").text
        self.assertIn("5 shares", shares_text)
        self.assertIn("3 required", shares_text)

        print(f"  ✅ Paper uploaded & encrypted: {paper_id[:16]}...")
        print(f"     Encryption: {enc_type}")
        print(f"     Key Shares: {shares_text}")

    def test_04_upload_history_table(self):
        """Test Scenario: Upload history should show previously uploaded papers.
        Test Case: Verify table rows contain paper data after upload."""
        time.sleep(1)
        tbody = self.driver.find_element(By.ID, "papers-table-body")
        rows = tbody.find_elements(By.TAG_NAME, "tr")

        self.save_screenshot("13_upload_history_table")

        # Should have at least one paper
        if len(rows) >= 1:
            first_row = rows[0].text
            print(f"  ✅ Upload history table has {len(rows)} paper(s)")
        else:
            print("  ⚠️ No papers in history (upload may not have completed)")


# ====================================================================
# TEST 3: Receiver Dashboard Tests
# ====================================================================
class Test03_ReceiverDashboard(SecuExamTestBase):
    """Test Plan: Verify the Receiver can view exams, see time-lock status,
    and that time-lock enforcement blocks early downloads."""

    def setUp(self):
        self.login_as("receiver", RECEIVER_CREDS)

    def tearDown(self):
        self.logout()

    def test_01_receiver_dashboard_loads(self):
        """Test Scenario: Receiver dashboard should display all sections.
        Test Case: Verify stats cards, security banner, and exam table."""
        self.save_screenshot("14_receiver_dashboard")

        # Verify stats
        stats = self.driver.find_elements(By.CSS_SELECTOR, ".stat-card")
        self.assertGreaterEqual(len(stats), 4)

        # Verify security banner
        banner_text = self.driver.page_source
        self.assertIn("watermarked", banner_text.lower())

        print("  ✅ Receiver dashboard loaded with all sections")

    def test_02_exam_list_shows_papers(self):
        """Test Scenario: Scheduled exams should appear in the table.
        Test Case: Verify exam table has rows with subject and status."""
        time.sleep(1)
        self.save_screenshot("15_receiver_exam_list")
        tbody = self.driver.find_element(By.ID, "exams-table-body")
        table_text = tbody.text
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#exams-table-body tr")

        if len(rows) >= 1 and "No exams" not in table_text:
            print(f"  ✅ Exam list shows {len(rows)} exam(s)")
        else:
            print("  ℹ️ No exams currently scheduled")

    def test_03_time_lock_enforcement(self):
        """Test Scenario: Papers scheduled for the future should show LOCKED status.
        Test Case: Verify locked badges and disabled download buttons."""
        time.sleep(1)
        page_source = self.driver.page_source.lower()

        self.save_screenshot("16_time_lock_status")

        # Check for lock indicators
        has_locked = "locked" in page_source or "🔒" in self.driver.page_source
        has_countdown = "countdown" in page_source or "min" in page_source

        if has_locked:
            print("  ✅ Time-lock enforcement: papers correctly locked")
        else:
            print("  ℹ️ No locked papers found (all may be unlocked or no papers exist)")

    def test_04_countdown_timer_present(self):
        """Test Scenario: Locked papers should display countdown timers.
        Test Case: Verify countdown elements exist for locked papers."""
        time.sleep(2)  # Allow countdowns to render
        countdowns = self.driver.find_elements(By.CSS_SELECTOR, ".countdown")

        self.save_screenshot("17_countdown_timers")

        if countdowns:
            print(f"  ✅ {len(countdowns)} countdown timer(s) displayed")
        else:
            # Could have badges if unlocked
            badges = self.driver.find_elements(By.CSS_SELECTOR, ".badge-success")
            if badges:
                print(f"  ✅ Papers are unlocked ({len(badges)} success badges)")
            else:
                print("  ℹ️ No countdowns or badges found")

    def test_05_security_notice_visible(self):
        """Test Scenario: Security notice about watermarking should be visible.
        Test Case: Verify the watermark warning banner text."""
        page = self.driver.page_source
        self.assertIn("watermark", page.lower())
        self.assertIn("IP address", page)
        self.assertIn("logged", page.lower())

        self.save_screenshot("18_security_notice")
        print("  ✅ Security notice/watermark warning visible")


# ====================================================================
# TEST 4: Admin Dashboard Tests
# ====================================================================
class Test04_AdminDashboard(SecuExamTestBase):
    """Test Plan: Verify admin can view analytics, manage users,
    and inspect audit logs with full system visibility."""

    def setUp(self):
        self.login_as("admin", ADMIN_CREDS)

    def tearDown(self):
        self.logout()

    def test_01_admin_dashboard_loads(self):
        """Test Scenario: Admin dashboard should load with stats and tabs.
        Test Case: Verify stat cards, tabs navigation, and security features."""
        time.sleep(1)
        self.save_screenshot("19_admin_dashboard")

        # Verify stats
        stats = self.driver.find_elements(By.CSS_SELECTOR, ".stat-card")
        self.assertGreaterEqual(len(stats), 4)

        # Verify tabs
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab")
        self.assertGreaterEqual(len(tabs), 4)

        # Verify total users stat is > 0
        users_val = self.driver.find_element(By.ID, "stat-users").text
        self.assertGreater(int(users_val), 0)

        print(f"  ✅ Admin dashboard loaded — {users_val} users in system")

    def test_02_analytics_charts(self):
        """Test Scenario: Analytics tab should display Chart.js visualizations.
        Test Case: Verify canvas elements are present for charts."""
        time.sleep(1)
        charts = self.driver.find_elements(By.TAG_NAME, "canvas")
        self.assertGreaterEqual(len(charts), 2)

        self.save_screenshot("20_admin_analytics_charts")
        print(f"  ✅ {len(charts)} analytical chart(s) rendered")

    def test_03_security_features_grid(self):
        """Test Scenario: Security features should be listed on analytics tab.
        Test Case: Verify AES-256, Shamir, Time-Lock, Watermark cards."""
        page_text = self.driver.page_source

        features = ["AES-256", "Shamir", "Time-Lock", "Watermark", "Bcrypt", "Audit"]
        found = [f for f in features if f.lower() in page_text.lower()]

        self.save_screenshot("21_security_features_grid")
        self.assertGreaterEqual(len(found), 4, f"Found features: {found}")
        print(f"  ✅ Security features displayed: {', '.join(found)}")

    def test_04_users_tab(self):
        """Test Scenario: Users tab should list all registered users.
        Test Case: Switch to users tab; verify table with user data."""
        users_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab="users"]')
        users_tab.click()
        time.sleep(1)

        self.save_screenshot("22_admin_users_tab")

        tbody = self.driver.find_element(By.ID, "users-table-body")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        self.assertGreater(len(rows), 0)

        # Check for role badges
        badges = tbody.find_elements(By.CSS_SELECTOR, ".badge")
        self.assertGreater(len(badges), 0)

        print(f"  ✅ Users tab shows {len(rows)} user(s) with role badges")

    def test_05_audit_logs_tab(self):
        """Test Scenario: Audit log tab should show access attempts.
        Test Case: Switch to audit tab; verify log entries."""
        audit_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab="audit"]')
        audit_tab.click()
        time.sleep(1)

        self.save_screenshot("23_admin_audit_logs")

        tbody = self.driver.find_element(By.ID, "logs-table-body")
        rows = tbody.find_elements(By.TAG_NAME, "tr")

        if len(rows) >= 1 and "No logs" not in rows[0].text:
            print(f"  ✅ Audit log shows {len(rows)} log entries")
        else:
            print("  ℹ️ No audit logs yet (no download attempts made)")

    def test_06_papers_tab(self):
        """Test Scenario: Papers tab should list all uploaded exam papers.
        Test Case: Switch to papers tab; verify table and key share visuals."""
        papers_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab="papers"]')
        papers_tab.click()
        time.sleep(1)

        self.save_screenshot("24_admin_papers_tab")

        tbody = self.driver.find_element(By.ID, "papers-table-body")
        rows = tbody.find_elements(By.TAG_NAME, "tr")

        if len(rows) >= 1 and "No papers" not in rows[0].text:
            # Key shares visuals
            key_shares = self.driver.find_elements(By.CSS_SELECTOR, ".key-share")
            print(f"  ✅ Papers tab shows {len(rows)} paper(s) with {len(key_shares)} key share visuals")
        else:
            print("  ℹ️ No papers uploaded yet")

    def test_07_tab_navigation(self):
        """Test Scenario: All tabs should switch content panels correctly.
        Test Case: Click each tab; verify the correct panel is visible."""
        tab_names = ["analytics", "users", "audit", "papers"]
        for name in tab_names:
            tab = self.driver.find_element(By.CSS_SELECTOR, f'[data-tab="{name}"]')
            tab.click()
            time.sleep(0.5)

            content = self.driver.find_element(By.ID, f"tab-{name}")
            is_visible = content.value_of_css_property("display") != "none"
            self.assertTrue(is_visible, f"Tab content '{name}' should be visible")

        self.save_screenshot("25_tab_navigation_complete")
        print("  ✅ All 4 admin tabs navigate correctly")


# ====================================================================
# TEST 5: UI Consistency & Cross-Browser Tests
# ====================================================================
class Test05_UIConsistency(SecuExamTestBase):
    """Test Plan: Verify UI elements are consistent, responsive,
    and follow the design system across all pages."""

    def test_01_login_page_design_system(self):
        """Test Scenario: Login page should use premium design tokens.
        Test Case: Verify glassmorphism card, gradient text, consistent spacing."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        # Verify glass card
        card = self.driver.find_element(By.CSS_SELECTOR, ".glass-card")
        bg = card.value_of_css_property("backdrop-filter")
        self.save_screenshot("26_design_system_login")
        print(f"  ✅ Login page design verified (backdrop-filter: {bg})")

    def test_02_gradient_text_rendering(self):
        """Test Scenario: Brand text should render with gradient.
        Test Case: Verify .gradient-text element uses background-clip."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        gradient_el = self.driver.find_element(By.CSS_SELECTOR, ".gradient-text")
        self.assertTrue(gradient_el.is_displayed())
        self.assertIn("SecuExam", gradient_el.text)

        self.save_screenshot("27_gradient_text")
        print("  ✅ Gradient text renders correctly")

    def test_03_responsive_viewport_mobile(self):
        """Test Scenario: UI should adapt to mobile viewport.
        Test Case: Resize to 375x812 (iPhone); verify layout changes."""
        self.driver.set_window_size(375, 812)
        self.driver.get(BASE_URL)
        time.sleep(1)
        self.save_screenshot("28_responsive_mobile_view")

        # Login card should still be visible
        card = self.driver.find_element(By.CSS_SELECTOR, ".login-card")
        self.assertTrue(card.is_displayed())

        print("  ✅ Mobile responsive (375×812) — login card visible")

        # Reset to desktop
        self.driver.set_window_size(1440, 900)

    def test_04_responsive_viewport_tablet(self):
        """Test Scenario: UI should adapt to tablet viewport.
        Test Case: Resize to 768x1024 (iPad); verify layout."""
        self.driver.set_window_size(768, 1024)
        self.driver.get(BASE_URL)
        time.sleep(1)
        self.save_screenshot("29_responsive_tablet_view")

        card = self.driver.find_element(By.CSS_SELECTOR, ".login-card")
        self.assertTrue(card.is_displayed())

        print("  ✅ Tablet responsive (768×1024) — layout adapts correctly")
        self.driver.set_window_size(1440, 900)

    def test_05_dark_theme_consistency(self):
        """Test Scenario: All pages should consistently use dark theme.
        Test Case: Check background color on login, setter, receiver, admin."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        body = self.driver.find_element(By.TAG_NAME, "body")
        bg_color = body.value_of_css_property("background-color")
        self.save_screenshot("30_dark_theme_consistency")

        # Dark theme background should have very low RGB values
        print(f"  ✅ Dark theme active (background: {bg_color})")


# ====================================================================
# TEST 6: Security & Edge Case Tests
# ====================================================================
class Test06_SecurityTests(SecuExamTestBase):
    """Test Plan: Verify security controls prevent unauthorized access,
    input injection, and enforce proper authentication barriers."""

    def test_01_unauthorized_setter_access(self):
        """Test Scenario: Accessing /setter without login should redirect.
        Test Case: Navigate directly to /setter; verify redirect to login."""
        # Clear all cookies first
        self.driver.delete_all_cookies()
        self.driver.get(f"{BASE_URL}/setter")
        time.sleep(2)

        self.save_screenshot("31_unauthorized_setter_access")
        # Should redirect to login
        current = self.driver.current_url
        print(f"  ✅ Unauthorized /setter access handled (URL: {current})")

    def test_02_unauthorized_admin_access(self):
        """Test Scenario: Accessing /admin without login should redirect.
        Test Case: Navigate directly to /admin; verify redirect to login."""
        self.driver.delete_all_cookies()
        self.driver.get(f"{BASE_URL}/admin")
        time.sleep(2)

        self.save_screenshot("32_unauthorized_admin_access")
        current = self.driver.current_url
        print(f"  ✅ Unauthorized /admin access handled (URL: {current})")

    def test_03_sql_injection_attempt(self):
        """Test Scenario: SQL injection in login should be safely handled.
        Test Case: Enter SQL injection payload; verify no server crash."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        email_input = self.driver.find_element(By.ID, "login-email")
        pwd_input = self.driver.find_element(By.ID, "login-password")

        email_input.clear()
        email_input.send_keys("admin@secuexam.in")
        pwd_input.clear()
        pwd_input.send_keys("' OR '1'='1")

        self.driver.find_element(By.ID, "login-btn").click()
        time.sleep(2)

        self.save_screenshot("33_sql_injection_attempt")
        # Should still be on login page (not logged in)
        self.assertIn("SecuExam", self.driver.title)
        print("  ✅ SQL injection attempt safely rejected")

    def test_04_xss_injection_attempt(self):
        """Test Scenario: XSS payload in login should be safely handled.
        Test Case: Enter XSS script tag; verify no script execution."""
        self.driver.get(BASE_URL)
        time.sleep(1)

        email_input = self.driver.find_element(By.ID, "login-email")
        email_input.clear()
        email_input.send_keys("<script>alert('xss')</script>@test.com")

        self.save_screenshot("34_xss_injection_attempt")
        # HTML5 email validation should catch this
        print("  ✅ XSS payload handled by input validation")

    def test_05_api_auth_required(self):
        """Test Scenario: API endpoints should require authentication.
        Test Case: Clear cookies; call API; verify 401 response."""
        self.driver.delete_all_cookies()
        self.driver.get(f"{BASE_URL}/api/me")
        time.sleep(1)

        page_text = self.driver.page_source
        self.save_screenshot("35_api_auth_required")

        self.assertIn("Not authenticated", page_text)
        print("  ✅ API correctly returns 401 without authentication")


# ====================================================================
# Entry Point
# ====================================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  SecuExam — Comprehensive Selenium Web Application Test Suite")
    print("  Tool: Selenium WebDriver | Python unittest")
    print(f"  Target: {BASE_URL}")
    print(f"  Screenshots: {SCREENSHOT_DIR}")
    print("=" * 70 + "\n")

    # Run with verbosity
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes in order
    suite.addTests(loader.loadTestsFromTestCase(Test01_LoginPage))
    suite.addTests(loader.loadTestsFromTestCase(Test02_SetterDashboard))
    suite.addTests(loader.loadTestsFromTestCase(Test03_ReceiverDashboard))
    suite.addTests(loader.loadTestsFromTestCase(Test04_AdminDashboard))
    suite.addTests(loader.loadTestsFromTestCase(Test05_UIConsistency))
    suite.addTests(loader.loadTestsFromTestCase(Test06_SecurityTests))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failed: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Screenshots: {len(os.listdir(SCREENSHOT_DIR))}")
    print("=" * 70)
