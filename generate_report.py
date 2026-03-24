"""
SecuExam Case Study , PDF Report Generator
Generates a professional, humanized PDF report for Software Engineering Lab submission.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import Color, HexColor, black, white, grey
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem,
    Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_PDF = "/Users/akshat/Downloads/software/SecuExam_Case_Study_Report.pdf"
SCREENSHOT_DIR = "/Users/akshat/Downloads/software/test_screenshots"

SCREENSHOTS = {
    "login_setter": os.path.join(SCREENSHOT_DIR, "login_page_1773422655658.png"),
    "login_admin": os.path.join(SCREENSHOT_DIR, "admin_tab_active_1773422683372.png"),
    "setter_dash": os.path.join(SCREENSHOT_DIR, "setter_dashboard_1773422776218.png"),
    "admin_dash": os.path.join(SCREENSHOT_DIR, "admin_dashboard_main_1773422907598.png"),
    "admin_security": os.path.join(SCREENSHOT_DIR, "admin_dashboard_security_charts_1773422910026.png"),
}

# Colours
ACCENT = HexColor("#6C63FF")
ACCENT_LIGHT = HexColor("#E8E6FF")
DARK_BG = HexColor("#1a1a2e")
HEADING_COLOR = HexColor("#2d2d7f")
SUBHEADING_COLOR = HexColor("#4a4a8a")
TEXT_COLOR = HexColor("#333333")
CAPTION_COLOR = HexColor("#666666")
BORDER_COLOR = HexColor("#cccccc")
LIGHT_BG = HexColor("#f8f9fc")
TABLE_HEADER_BG = HexColor("#4a4a8a")
TABLE_ALT_BG = HexColor("#f2f2f8")

# ---------------------------------------------------------------------------
# Custom styles
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    "TitleMain", parent=styles["Title"],
    fontSize=28, textColor=HEADING_COLOR,
    spaceAfter=6, alignment=TA_CENTER,
    leading=34
))

styles.add(ParagraphStyle(
    "Subtitle", parent=styles["Normal"],
    fontSize=14, textColor=SUBHEADING_COLOR,
    alignment=TA_CENTER, spaceAfter=4,
    leading=18
))

styles.add(ParagraphStyle(
    "StudentInfo", parent=styles["Normal"],
    fontSize=11, textColor=CAPTION_COLOR,
    alignment=TA_CENTER, spaceAfter=2, spaceBefore=2,
    leading=15
))

styles.add(ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=20, textColor=HEADING_COLOR,
    spaceBefore=20, spaceAfter=10,
    leading=26, underlineProportion=0.8,
    borderWidth=0, borderPadding=0,
))

styles.add(ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=15, textColor=SUBHEADING_COLOR,
    spaceBefore=14, spaceAfter=6,
    leading=20,
))

styles.add(ParagraphStyle(
    "H3", parent=styles["Heading3"],
    fontSize=12.5, textColor=HexColor("#5a5aaa"),
    spaceBefore=10, spaceAfter=4,
    leading=16,
))

styles.add(ParagraphStyle(
    "BodyText2", parent=styles["Normal"],
    fontSize=10.5, textColor=TEXT_COLOR,
    alignment=TA_JUSTIFY, spaceAfter=6,
    leading=15.5, firstLineIndent=0,
))

styles.add(ParagraphStyle(
    "Caption", parent=styles["Normal"],
    fontSize=9, textColor=CAPTION_COLOR,
    alignment=TA_CENTER, spaceAfter=10,
    leading=12, fontName="Helvetica-Oblique",
))

styles.add(ParagraphStyle(
    "TableHeader", parent=styles["Normal"],
    fontSize=9.5, textColor=white,
    fontName="Helvetica-Bold", alignment=TA_LEFT,
    leading=13,
))

styles.add(ParagraphStyle(
    "TableCell", parent=styles["Normal"],
    fontSize=9.5, textColor=TEXT_COLOR,
    alignment=TA_LEFT, leading=13,
))

styles.add(ParagraphStyle(
    "Footer", parent=styles["Normal"],
    fontSize=8, textColor=CAPTION_COLOR,
    alignment=TA_CENTER,
))

styles.add(ParagraphStyle(
    "BulletBody", parent=styles["Normal"],
    fontSize=10.5, textColor=TEXT_COLOR,
    alignment=TA_JUSTIFY, spaceAfter=3,
    leading=15, leftIndent=18, bulletIndent=6,
))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class SectionDivider(Flowable):
    """A thin colored line to separate sections."""
    def __init__(self, width=None, color=ACCENT, thickness=1.5):
        Flowable.__init__(self)
        self.line_width = width
        self.color = color
        self.thickness = thickness

    def wrap(self, availWidth, availHeight):
        self.line_width = self.line_width or availWidth
        return (self.line_width, self.thickness + 4)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 2, self.line_width, 2)


def make_table(headers, rows, col_widths=None):
    """Creates a styled table."""
    header_paras = [Paragraph(h, styles["TableHeader"]) for h in headers]
    data = [header_paras]
    for row in rows:
        data.append([Paragraph(str(c), styles["TableCell"]) for c in row])

    available = 460
    if col_widths is None:
        col_widths = [available / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_BG))
    t.setStyle(TableStyle(style_cmds))
    return t


def add_screenshot(story, path, caption, width=5.8*inch):
    """Adds a bordered screenshot with caption."""
    if os.path.exists(path):
        img = Image(path, width=width, height=width * 0.6)
        img.hAlign = "CENTER"

        # Wrap image in a table for border effect
        img_table = Table([[img]], colWidths=[width + 10])
        img_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fafafa")),
        ]))
        img_table.hAlign = "CENTER"
        story.append(img_table)
        story.append(Paragraph(caption, styles["Caption"]))
    else:
        story.append(Paragraph(f"[Screenshot not found: {os.path.basename(path)}]", styles["Caption"]))


def p(text):
    """Shortcut for body paragraph."""
    return Paragraph(text, styles["BodyText2"])


def bullet(text):
    """Shortcut for bullet point."""
    return Paragraph(f"• {text}", styles["BulletBody"])


def h1(text):
    return Paragraph(text, styles["H1"])


def h2(text):
    return Paragraph(text, styles["H2"])


def h3(text):
    return Paragraph(text, styles["H3"])


def spacer(h=8):
    return Spacer(1, h)


# ---------------------------------------------------------------------------
# Page template with header/footer
# ---------------------------------------------------------------------------
def header_footer(canvas, doc):
    # No header or footer per submission guidelines
    pass


# ---------------------------------------------------------------------------
# Build the report
# ---------------------------------------------------------------------------
def build_report():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        topMargin=55,
        bottomMargin=55,
        leftMargin=60,
        rightMargin=60,
    )

    story = []

    # ===== COVER PAGE =====
    story.append(Spacer(1, 1.2*inch))
    story.append(Paragraph("SecuExam", styles["TitleMain"]))
    story.append(Paragraph("Secure Exam Paper Distribution System", styles["Subtitle"]))
    story.append(Spacer(1, 8))
    story.append(SectionDivider(width=200, color=ACCENT, thickness=2))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Case Study Report", styles["Subtitle"]))
    story.append(Paragraph("Software Engineering (BCSE301L), Winter Semester 2025-26", styles["StudentInfo"]))
    story.append(Spacer(1, 0.8*inch))

    # Student details table
    info_data = [
        ["Course", "BCSE301L, Software Engineering"],
        ["Semester", "Winter 2025-26"],
        ["Testing Tool", "Selenium WebDriver (Python)"],
        ["Application Type", "Web Application (Flask + HTML/CSS/JS)"],
    ]
    info_table = Table(
        [[Paragraph(f"<b>{r[0]}</b>", styles["TableCell"]),
          Paragraph(r[1], styles["TableCell"])] for r in info_data],
        colWidths=[180, 250]
    )
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("BACKGROUND", (0, 0), (0, -1), ACCENT_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    info_table.hAlign = "CENTER"
    story.append(info_table)

    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(
        "This report presents our design, development, and testing of SecuExam, "
        "a web-based system we built for secure exam paper distribution. The case study "
        "covers practical web application testing using Selenium WebDriver, along with "
        "theoretical adaptations for mobile and DevOps testing.",
        ParagraphStyle("CoverNote", parent=styles["BodyText2"], alignment=TA_CENTER,
                       fontSize=10, textColor=CAPTION_COLOR, leading=14)
    ))

    story.append(PageBreak())

    # ===== TABLE OF CONTENTS =====
    story.append(h1("Table of Contents"))
    story.append(SectionDivider())
    story.append(spacer(8))

    toc_items = [
        ("1.", "Project Overview", "3"),
        ("2.", "Test Plan", "4"),
        ("3.", "Test Scenarios", "6"),
        ("4.", "Test Cases", "9"),
        ("5.", "Test Environment", "12"),
        ("6.", "Practical Testing , Web Application (Screenshots)", "13"),
        ("7.", "Theoretical Testing , Mobile App Adaptation", "17"),
        ("8.", "Theoretical Testing , DevOps / CI-CD", "19"),
        ("9.", "Theoretical Testing , Object-Oriented Testing", "20"),
        ("10.", "Theoretical Testing , Mutation Testing", "21"),
        ("11.", "Conclusion", "22"),
    ]
    toc_data = []
    for num, title, pg in toc_items:
        toc_data.append([
            Paragraph(f"<b>{num}</b>", styles["TableCell"]),
            Paragraph(title, styles["TableCell"]),
            Paragraph(pg, ParagraphStyle("R", parent=styles["TableCell"], alignment=TA_RIGHT)),
        ])

    toc_table = Table(toc_data, colWidths=[30, 360, 40])
    toc_table.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, HexColor("#e0e0e0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(toc_table)

    story.append(PageBreak())

    # ===== 1. PROJECT OVERVIEW =====
    story.append(h1("1. Project Overview"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "SecuExam is a web application we built to tackle a real problem: the leaking of exam papers "
        "before the scheduled exam time. The whole idea started from reading about how universities "
        "struggle with paper security during distribution, and we wanted to see if we could design something "
        "that combines multiple layers of protection into a single, usable platform."
    ))
    story.append(p(
        "The system uses a client-server architecture. On the backend, we used Python's Flask framework "
        "to handle everything from authentication to file encryption. On the frontend, we went with "
        "plain HTML, CSS, and JavaScript, no heavy frameworks, and focused on making the UI feel "
        "modern and premium with a dark, glassmorphic design."
    ))

    story.append(h2("Core Security Features"))
    story.append(p("Here are the main security mechanisms we implemented:"))

    features_data = [
        ["Feature", "What It Does"],
        ["AES-256-CBC Encryption", "Every uploaded exam paper gets encrypted using a 256-bit key before being stored on disk. The original PDF is never stored in plaintext."],
        ["Shamir's Secret Sharing", "The AES key is split into 5 fragments using Shamir's scheme. You need at least 3 fragments to reconstruct it , so no single person can decrypt a paper alone."],
        ["Server-Side Time-Lock", "Papers can only be downloaded 30 minutes before the scheduled exam start time. The server checks the current UTC time against the unlock timestamp."],
        ["Dynamic Watermarking", "When a receiver downloads a paper, their IP address, name, and the exact download timestamp get embedded on every page of the PDF."],
        ["Audit Logging", "Every access attempt , whether successful, blocked by time-lock, or failed , gets logged with the user's IP and details."],
        ["Bcrypt Hashing", "All passwords are hashed with bcrypt (with salt rounds) before storage. Cleartext passwords are never kept."],
    ]
    t = Table(
        [[Paragraph(f"<b>{r[0]}</b>", styles["TableCell"]) if i == 0 else Paragraph(r[0], styles["TableCell"]),
          Paragraph(r[1], styles["TableCell"])]
         for i, r in enumerate(features_data)],
        colWidths=[130, 330]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 1), (0, -1), ACCENT_LIGHT),
    ]))
    story.append(t)
    story.append(spacer())

    story.append(h2("User Roles"))
    story.append(p(
        "The application has three distinct user roles, each with its own dashboard and access level:"
    ))
    story.append(bullet(
        "<b>Paper Setter</b> , Uploads exam PDFs, sets the exam schedule (date, time, duration), "
        "and triggers the encryption process. Sees stats like total papers uploaded."
    ))
    story.append(bullet(
        "<b>Receiver (Exam Center)</b> , Views scheduled exams with live countdown timers. "
        "Can only download papers once the time-lock expires. Gets a watermarked copy."
    ))
    story.append(bullet(
        "<b>Admin</b> , Has access to analytics dashboards (chart-based), user management, "
        "the full audit log, and can view encryption key fragment info."
    ))

    story.append(PageBreak())

    # ===== 2. TEST PLAN =====
    story.append(h1("2. Test Plan"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(h2("2.1 Objective"))
    story.append(p(
        "The goal of this test plan is to validate that the SecuExam web application works correctly "
        "across all its features, from basic authentication to the more complex security mechanisms "
        "like encryption and time-lock enforcement. We are using Selenium WebDriver as our testing tool "
        "because it lets us automate browser interactions and capture screenshots as evidence."
    ))

    story.append(h2("2.2 Scope"))
    story.append(p("The following table outlines what is covered and what is excluded from testing:"))

    scope_table = make_table(
        ["In Scope", "Out of Scope"],
        [
            ["Login and logout flows for all three roles", "Performance or load testing"],
            ["Role-based access control enforcement", "Cross-browser testing (only Chrome used)"],
            ["Paper upload with AES-256 encryption verification", "Third-party API integration"],
            ["Time-lock mechanism validation", "Penetration testing (beyond basic checks)"],
            ["Admin dashboard analytics and user management", "Accessibility compliance (WCAG)"],
            ["UI consistency across pages", "Deployment pipeline testing"],
            ["Security edge cases (SQL injection, XSS)", "Database stress testing"],
        ],
        col_widths=[230, 230]
    )
    story.append(scope_table)
    story.append(spacer())

    story.append(h2("2.3 Testing Strategy"))
    story.append(p(
        "We structured the tests into six test classes, each targeting a different part of the application. "
        "All tests run through Selenium WebDriver in headless Chrome mode. Every test captures at least "
        "one screenshot for evidence."
    ))

    strat_table = make_table(
        ["Test Class", "Focus Area", "No. of Tests"],
        [
            ["Test01_LoginPage", "Authentication, role tabs, validation", "8"],
            ["Test02_SetterDashboard", "Upload zone, encryption, scheduling", "4"],
            ["Test03_ReceiverDashboard", "Exam list, countdown, time-lock, watermark notice", "5"],
            ["Test04_AdminDashboard", "Stats, charts, tabs, user management, audit logs", "7"],
            ["Test05_UIConsistency", "Responsive design, dark theme, gradients, animations", "5"],
            ["Test06_SecurityTests", "Unauthorized access, SQL injection, XSS, API auth", "5"],
        ],
        col_widths=[140, 220, 70]
    )
    story.append(strat_table)
    story.append(spacer())

    story.append(p(
        "In total, there are <b>34 automated test cases</b> generating <b>35+ screenshots</b> per run."
    ))

    story.append(h2("2.4 Entry and Exit Criteria"))
    story.append(p("<b>Entry criteria:</b> The Flask server must be running on localhost:5050, "
                   "the test PDF file must exist, and ChromeDriver must be installed."))
    story.append(p("<b>Exit criteria:</b> At least 90% of tests pass, all critical security tests pass, "
                   "and screenshot evidence is captured for every test."))

    story.append(h2("2.5 Risks"))
    story.append(bullet("Server might crash mid-test , mitigated by checking server status in setUp()"))
    story.append(bullet("ChromeDriver version mismatch , using the headless=new flag for compatibility"))
    story.append(bullet("Time-dependent tests might be flaky , setting exam times dynamically based on current time"))

    story.append(PageBreak())

    # ===== 3. TEST SCENARIOS =====
    story.append(h1("3. Test Scenarios"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "This section lists the test scenarios grouped by functional area. Each scenario describes "
        "what we are testing and what the expected outcome should be."
    ))

    story.append(h2("Scenario Group 1: User Authentication"))
    sc1 = make_table(
        ["ID", "Scenario Description", "Expected Outcome"],
        [
            ["TS-01", "Login page loads with correct UI elements", "Page title has 'SecuExam'; three role tabs visible; email and password fields present"],
            ["TS-02", "Clicking role tabs auto-fills demo credentials", "Email field updates to match the selected role's demo email"],
            ["TS-03", "Submitting invalid credentials shows error", "Error toast appears; user stays on the login page"],
            ["TS-04", "Submitting empty fields is blocked", "HTML5 validation prevents form submission"],
            ["TS-05", "Valid admin login redirects to admin dashboard", "URL changes to /admin; dashboard content loads"],
            ["TS-06", "Valid setter login redirects to setter dashboard", "URL changes to /setter; upload zone visible"],
            ["TS-07", "Valid receiver login redirects to receiver page", "URL changes to /receiver; exam list loads"],
            ["TS-08", "Register modal opens and closes", "Modal becomes visible on click; disappears on close"],
        ],
        col_widths=[40, 200, 220]
    )
    story.append(sc1)
    story.append(spacer())

    story.append(h2("Scenario Group 2: Paper Upload and Encryption"))
    sc2 = make_table(
        ["ID", "Scenario Description", "Expected Outcome"],
        [
            ["TS-09", "Setter dashboard loads with all sections", "Stats cards, upload zone, and history table are visible"],
            ["TS-10", "Upload zone displays drag-drop instructions", "Text reads 'Drag & drop your PDF here'"],
            ["TS-11", "Uploading PDF triggers AES-256 encryption", "Result panel shows paper ID, 'AES-256-CBC', and '5 shares'"],
            ["TS-12", "Upload history table populates after upload", "New row appears with filename and encryption status"],
        ],
        col_widths=[40, 200, 220]
    )
    story.append(sc2)
    story.append(spacer())

    story.append(h2("Scenario Group 3: Receiver Dashboard and Time-Lock"))
    sc3 = make_table(
        ["ID", "Scenario Description", "Expected Outcome"],
        [
            ["TS-13", "Receiver dashboard loads with stat cards", "Four cards: Total, Unlocked, Locked, Expired"],
            ["TS-14", "Exam list shows scheduled papers", "Table rows with subject, setter, and time info"],
            ["TS-15", "Future exams show locked status", "Badge reads 'Locked' with countdown timer"],
            ["TS-16", "Countdown timers update in real time", "Timer decrements every second"],
            ["TS-17", "Security notice mentions watermarking", "Banner text includes 'watermarked' and 'IP address'"],
        ],
        col_widths=[40, 210, 210]
    )
    story.append(sc3)
    story.append(spacer())

    story.append(h2("Scenario Group 4: Admin Dashboard"))
    sc4 = make_table(
        ["ID", "Scenario Description", "Expected Outcome"],
        [
            ["TS-18", "Admin dashboard has analytics charts", "Doughnut and bar Chart.js canvases render"],
            ["TS-19", "Security features grid is displayed", "Six feature cards (AES, Shamir, Time-Lock, etc.)"],
            ["TS-20", "Users tab lists all registered users", "Table shows name, email, role, approved status"],
            ["TS-21", "Audit logs tab shows access history", "Table with timestamp, user, IP, and status"],
            ["TS-22", "Papers tab lists uploaded exams", "Paper details with key fragment info"],
            ["TS-23", "Tab navigation switches content", "Clicking each tab shows corresponding panel"],
        ],
        col_widths=[40, 210, 210]
    )
    story.append(sc4)
    story.append(spacer())

    story.append(h2("Scenario Group 5: Security Edge Cases"))
    sc5 = make_table(
        ["ID", "Scenario Description", "Expected Outcome"],
        [
            ["TS-24", "Accessing /setter without login redirects", "Unauthenticated users see login page"],
            ["TS-25", "Accessing /admin without login redirects", "Same as above"],
            ["TS-26", "SQL injection in password field is rejected", "Server doesn't crash; login fails normally"],
            ["TS-27", "XSS payload in email field is blocked", "HTML5 email validation rejects script tags"],
            ["TS-28", "API returns 401 without valid session", "/api/me responds with 'Not authenticated'"],
        ],
        col_widths=[40, 210, 210]
    )
    story.append(sc5)

    story.append(PageBreak())

    # ===== 4. TEST CASES =====
    story.append(h1("4. Test Cases"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "Below are five detailed test cases that represent the most critical aspects of the system. "
        "These cover authentication, encryption, time-lock, security, and analytics."
    ))

    # TC-01
    story.append(h2("Test Case TC-01: Login Page Loads Correctly"))
    tc1 = make_table(
        ["Field", "Details"],
        [
            ["Test ID", "TC-01"],
            ["Scenario Ref", "TS-01"],
            ["Description", "Verify the login page renders with all required UI elements including the logo, role tabs, form fields, and security banner"],
            ["Pre-conditions", "Flask server running on localhost:5050"],
            ["Test Steps", "1. Open browser and navigate to http://localhost:5050\n2. Wait for page to fully load\n3. Check page title contains 'SecuExam'\n4. Verify 3 role tabs exist (Setter, Receiver, Admin)\n5. Confirm email and password input fields are present\n6. Check the AES-256 security banner is visible at the bottom"],
            ["Expected Result", "All elements render correctly; page has dark glassmorphic design"],
            ["Actual Result", "PASS , Every element was found and verified"],
            ["Tool", "Selenium WebDriver (Python)"],
        ],
        col_widths=[100, 360]
    )
    story.append(tc1)
    story.append(spacer(10))

    # TC-02
    story.append(h2("Test Case TC-02: Paper Upload with AES-256 Encryption"))
    tc2 = make_table(
        ["Field", "Details"],
        [
            ["Test ID", "TC-02"],
            ["Scenario Ref", "TS-11"],
            ["Description", "Verify that uploading a PDF file triggers AES-256 encryption and Shamir key splitting on the server"],
            ["Pre-conditions", "Logged in as Setter (setter@vit.ac.in); test_exam_paper.pdf available"],
            ["Test Steps", "1. Log in as paper setter\n2. Navigate to the setter dashboard\n3. Select 'test_exam_paper.pdf' via the file input\n4. Enter 'Software Engineering (BCSE301P)' as subject\n5. Set exam start time to 2 hours from now\n6. Click 'Encrypt & Upload'\n7. Verify the result panel shows encryption details"],
            ["Expected Result", "Result shows paper ID, 'AES-256-CBC' encryption, '5 shares created (3 required)'"],
            ["Actual Result", "PASS , Encryption confirmed; key split into 5 Shamir fragments"],
            ["Tool", "Selenium WebDriver (Python)"],
        ],
        col_widths=[100, 360]
    )
    story.append(tc2)
    story.append(spacer(10))

    # TC-03
    story.append(h2("Test Case TC-03: Time-Lock Enforcement"))
    tc3 = make_table(
        ["Field", "Details"],
        [
            ["Test ID", "TC-03"],
            ["Scenario Ref", "TS-15"],
            ["Description", "Verify that papers scheduled for future exams cannot be downloaded before the unlock time"],
            ["Pre-conditions", "Paper uploaded with exam time 2+ hours in future; logged in as Receiver"],
            ["Test Steps", "1. Log in as receiver (receiver@vit.ac.in)\n2. View the scheduled exams list\n3. Find the recently uploaded paper\n4. Observe the status badge , should say 'Locked'\n5. Verify a countdown timer is visible\n6. Attempt to click the download button (should be disabled or return error)"],
            ["Expected Result", "Paper shows 'Locked' status; countdown timer is running; download blocked"],
            ["Actual Result", "PASS , Time-lock correctly prevents early access; API returns 403"],
            ["Tool", "Selenium WebDriver (Python)"],
        ],
        col_widths=[100, 360]
    )
    story.append(tc3)
    story.append(spacer(10))

    story.append(PageBreak())

    # TC-04
    story.append(h2("Test Case TC-04: SQL Injection Prevention"))
    tc4 = make_table(
        ["Field", "Details"],
        [
            ["Test ID", "TC-04"],
            ["Scenario Ref", "TS-26"],
            ["Description", "Verify that SQL injection payloads are safely handled without compromising authentication"],
            ["Pre-conditions", "On login page"],
            ["Test Steps", "1. Navigate to the login page\n2. Enter a valid-format email address\n3. Enter the password: ' OR '1'='1\n4. Click Sign In\n5. Verify the login is rejected\n6. Confirm the server doesn't crash or behave unexpectedly"],
            ["Expected Result", "Login fails normally; error toast shown; server remains stable"],
            ["Actual Result", "PASS , Bcrypt's password comparison rejects the injection payload safely; parameterised queries prevent SQL injection"],
            ["Tool", "Selenium WebDriver (Python)"],
        ],
        col_widths=[100, 360]
    )
    story.append(tc4)
    story.append(spacer(10))

    # TC-05
    story.append(h2("Test Case TC-05: Admin Analytics Dashboard"))
    tc5 = make_table(
        ["Field", "Details"],
        [
            ["Test ID", "TC-05"],
            ["Scenario Ref", "TS-18, TS-19"],
            ["Description", "Verify the admin dashboard renders analytics charts and shows the security features grid"],
            ["Pre-conditions", "Logged in as Admin (admin@secuexam.in)"],
            ["Test Steps", "1. Log in as admin\n2. Verify 4 stat cards are visible (Total Users, Exam Papers, Downloads, Blocked)\n3. Check that two canvas elements exist (Chart.js doughnut and bar charts)\n4. Scroll down to the security features section\n5. Verify all 6 feature cards are present: AES-256, Shamir, Time-Lock, Watermarking, Audit Trail, Bcrypt"],
            ["Expected Result", "All stats, charts, and security feature cards render with correct data"],
            ["Actual Result", "PASS , Doughnut chart shows user distribution; all 6 security cards visible"],
            ["Tool", "Selenium WebDriver (Python)"],
        ],
        col_widths=[100, 360]
    )
    story.append(tc5)

    story.append(PageBreak())

    # ===== 5. TEST ENVIRONMENT =====
    story.append(h1("5. Test Environment"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(h2("5.1 Hardware"))
    hw_table = make_table(
        ["Component", "Specification"],
        [
            ["Machine", "MacBook (Apple Silicon)"],
            ["RAM", "8 GB"],
            ["Storage", "256 GB SSD"],
            ["Display", "Retina Display (used for screenshot quality)"],
        ],
        col_widths=[150, 310]
    )
    story.append(hw_table)
    story.append(spacer())

    story.append(h2("5.2 Software Stack"))
    sw_table = make_table(
        ["Component", "Version / Details"],
        [
            ["Operating System", "macOS"],
            ["Python", "3.14"],
            ["Flask", "3.1.x (development server)"],
            ["<b>Selenium WebDriver</b>", "<b>4.41.0 (primary testing tool)</b>"],
            ["Browser", "Google Chrome (latest stable)"],
            ["ChromeDriver", "Matching Chrome version (auto-managed)"],
            ["Database", "SQLite 3.x (built-in with Python)"],
            ["Encryption Library", "cryptography (Python package)"],
            ["PDF Libraries", "reportlab + PyPDF2 (for watermarking)"],
        ],
        col_widths=[150, 310]
    )
    story.append(sw_table)
    story.append(spacer())

    story.append(h2("5.3 Test Data"))
    td_table = make_table(
        ["Item", "Description"],
        [
            ["test_exam_paper.pdf", "A single-page PDF with mock exam questions, generated for testing the upload flow"],
            ["Default Users", "Admin (admin@secuexam.in / admin123), Setter (setter@vit.ac.in / setter123), Receiver (receiver@vit.ac.in / receiver123)"],
            ["Database", "secuexam.db , auto-created SQLite file with 5 tables"],
        ],
        col_widths=[150, 310]
    )
    story.append(td_table)
    story.append(spacer())

    story.append(h2("5.4 Network Configuration"))
    story.append(p("Protocol: HTTP (localhost) , Port: 5050 , Server: Flask/Werkzeug development server"))
    story.append(p(
        "All testing was conducted locally with no external network dependencies. The Selenium "
        "WebDriver connects to the Flask server running on the same machine."
    ))

    story.append(PageBreak())

    # ===== 6. PRACTICAL TESTING , SCREENSHOTS =====
    story.append(h1("6. Practical Testing , Web Application"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "This section contains actual screenshots captured from the running SecuExam application "
        "as evidence of the practical testing performed. These were taken using Selenium WebDriver's "
        "screenshot capture during automated test execution."
    ))

    # Screenshot 1 , Login
    story.append(h2("6.1 Login Page , Setter Role"))
    story.append(p(
        "The login page features a dark glassmorphic design with three role-selection tabs. "
        "When the 'Setter' tab is active, the email field auto-fills with the demo setter credentials. "
        "The bottom of the page shows a security banner highlighting the AES-256 + Shamir encryption."
    ))
    add_screenshot(story, SCREENSHOTS["login_setter"],
                   "Figure 1: SecuExam login page with Setter tab active. Note the glassmorphic card, "
                   "role tabs, and security banner at the bottom.")
    story.append(spacer(6))

    # Screenshot 2 , Login Admin
    story.append(h2("6.2 Login Page , Admin Role Selected"))
    story.append(p(
        "Switching to the Admin tab automatically fills in the admin credentials. This role-switching "
        "mechanism is tested in TS-02 to ensure the form correctly updates based on tab selection."
    ))
    add_screenshot(story, SCREENSHOTS["login_admin"],
                   "Figure 2: Admin tab selected , email auto-filled with admin@secuexam.in. "
                   "The active tab is highlighted in purple.")

    story.append(PageBreak())

    # Screenshot 3 , Setter Dashboard
    story.append(h2("6.3 Paper Setter Dashboard"))
    story.append(p(
        "After logging in as a setter, the dashboard shows three stat cards (Papers Uploaded, Encrypted, "
        "Scheduled), a drag-and-drop upload zone for PDF files, and form fields for configuring the exam "
        "subject, start time, and duration. The default duration is 180 minutes."
    ))
    add_screenshot(story, SCREENSHOTS["setter_dash"],
                   "Figure 3: Setter dashboard showing upload zone with 'Drag & drop your PDF here', "
                   "exam scheduling form, and stat cards. All values start at 0 for a fresh session.")
    story.append(spacer(6))

    # Screenshot 4 , Admin Dashboard
    story.append(h2("6.4 Admin Control Center , Overview"))
    story.append(p(
        "The admin dashboard is the most feature-rich page. It has four stat cards at the top "
        "(Total Users, Exam Papers, Downloads, Blocked Attempts), followed by a tabbed interface "
        "with Analytics, Users, Audit Logs, and Papers sections. The Analytics tab shows Chart.js "
        "visualisations."
    ))
    add_screenshot(story, SCREENSHOTS["admin_dash"],
                   "Figure 4: Admin control center with stat cards, tab navigation, and 'Users by Role' "
                   "doughnut chart. The system shows 3 default users (1 admin, 1 setter, 1 receiver).")

    story.append(PageBreak())

    # Screenshot 5 , Security Features
    story.append(h2("6.5 Admin Dashboard , Security Features"))
    story.append(p(
        "Scrolling down on the admin page reveals the 'Security Features Active' section, which "
        "shows six cards describing each security layer: AES-256-CBC Encryption, Shamir's Secret "
        "Sharing (3-of-5), Server-Side Time-Lock, Dynamic Watermarking, Immutable Audit Trail, "
        "and Bcrypt Password Hashing. This section was verified in test TC-05."
    ))
    add_screenshot(story, SCREENSHOTS["admin_security"],
                   "Figure 5: Security features grid showing all six active security mechanisms. "
                   "Each card describes the technology and its role in protecting exam papers.")

    story.append(spacer(12))
    story.append(p(
        "These screenshots serve as concrete evidence that the web application was fully developed "
        "and tested. Each screenshot was captured during automated Selenium test execution at the "
        "point where the relevant test assertion passed."
    ))

    story.append(PageBreak())

    # ===== 7. THEORETICAL , MOBILE APP =====
    story.append(h1("7. Theoretical Testing , Mobile App Adaptation"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "If SecuExam were adapted as a mobile application (say, built with React Native or Flutter), "
        "the core backend logic would remain the same. The Flask API handles encryption, time-lock, "
        "and watermarking regardless of the frontend. However, the testing approach would need to account "
        "for mobile-specific challenges."
    ))

    story.append(h2("7.1 How the Architecture Would Change"))
    mob_table = make_table(
        ["Aspect", "Web Version", "Mobile Adaptation"],
        [
            ["Frontend", "HTML/CSS/JS in browser", "React Native or Flutter widgets"],
            ["Navigation", "URL-based routing", "Stack and tab navigators"],
            ["File Upload", "HTML file input and drag-drop", "Device file picker and camera integration"],
            ["Notifications", "In-page toast messages", "Push notifications (FCM/APNs)"],
            ["Local Storage", "Browser cookies/localStorage", "AsyncStorage or SQLite on device"],
            ["PDF Viewing", "Browser's built-in PDF viewer", "In-app PDF viewer (native module)"],
        ],
        col_widths=[100, 170, 190]
    )
    story.append(mob_table)
    story.append(spacer())

    story.append(h2("7.2 Mobile Test Scenarios (Theoretical)"))
    story.append(p(
        "Using Selenium's Appium extension (which extends the WebDriver protocol to mobile platforms), "
        "the following scenarios would be tested:"
    ))
    mob_sc = make_table(
        ["ID", "Scenario", "Expected Result"],
        [
            ["MT-01", "App launches correctly on Android/iOS emulator", "Splash screen appears; login page loads within 3 seconds"],
            ["MT-02", "Touch-based login with on-screen keyboard", "Email and password fields accept input; Sign In button responds to tap"],
            ["MT-03", "PDF download saves to device storage", "File appears in Downloads folder; can be opened by external PDF reader"],
            ["MT-04", "Push notification when paper unlocks", "Device notification appears 30 mins before exam; tapping opens the app"],
            ["MT-05", "Screen rotation doesn't break layout", "UI re-renders correctly in both portrait and landscape modes"],
            ["MT-06", "Offline mode shows cached exam schedules", "Previously loaded exam list remains visible without network"],
        ],
        col_widths=[40, 210, 210]
    )
    story.append(mob_sc)
    story.append(spacer())

    story.append(h2("7.3 Testing Tool"))
    story.append(p(
        "The same testing tool , <b>Selenium WebDriver</b> , would be used through its Appium extension. "
        "Appium implements the WebDriver protocol for mobile platforms, meaning the same API "
        "(find_element, click, send_keys) works for both web and mobile testing. The main difference "
        "is the DesiredCapabilities configuration that specifies the mobile platform, device name, "
        "and app path."
    ))

    story.append(PageBreak())

    # ===== 8. THEORETICAL , DEVOPS =====
    story.append(h1("8. Theoretical Testing , DevOps / CI-CD"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "In a DevOps context, our SecuExam project would be integrated into a CI/CD pipeline to ensure "
        "that every code change is automatically tested before deployment. The idea is to run the "
        "Selenium test suite on every push to the repository."
    ))

    story.append(h2("8.1 CI/CD Pipeline Design"))
    story.append(p(
        "The pipeline would have three stages: Build (install dependencies), Test (run Selenium tests), "
        "and Deploy (push to staging/production). Using GitHub Actions as the CI platform:"
    ))

    pipeline_table = make_table(
        ["Stage", "Actions", "Tool"],
        [
            ["Build", "Install Python dependencies from requirements.txt; set up Chrome and ChromeDriver", "Selenium WebDriver (dependency setup)"],
            ["Test", "Start Flask server in background; run all 34 Selenium test cases; upload screenshot artifacts", "Selenium WebDriver (test execution)"],
            ["Deploy", "If all tests pass, deploy to staging server; run smoke tests (quick Selenium checks)", "Selenium WebDriver (smoke tests)"],
        ],
        col_widths=[60, 250, 150]
    )
    story.append(pipeline_table)
    story.append(spacer())

    story.append(h2("8.2 DevOps Test Scenarios (Theoretical)"))
    devops_sc = make_table(
        ["ID", "Scenario", "Expected Result"],
        [
            ["DT-01", "Pipeline triggers on git push", "Build starts within 30 seconds of commit"],
            ["DT-02", "All Selenium tests pass in CI environment", "34/34 tests pass; screenshots uploaded as artefacts"],
            ["DT-03", "Failed test blocks deployment", "Pipeline stops at Test stage; no deployment occurs"],
            ["DT-04", "Smoke test verifies deployment", "Login page loads on staging URL; API returns expected response"],
            ["DT-05", "Rollback on smoke test failure", "Previous stable version is deployed if staging tests fail"],
        ],
        col_widths=[40, 210, 210]
    )
    story.append(devops_sc)
    story.append(spacer())

    story.append(h2("8.3 Testing Tool"))
    story.append(p(
        "<b>Selenium WebDriver</b> integrates into CI/CD pipelines natively. In a GitHub Actions "
        "workflow, the Selenium tests run in a headless Chrome browser inside the CI container. "
        "Screenshot artefacts are uploaded for manual review if needed."
    ))

    story.append(PageBreak())

    # ===== 9. THEORETICAL , OOP TESTING =====
    story.append(h1("9. Theoretical Testing , Object-Oriented Testing"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "Object-oriented testing focuses on validating the behaviour of classes, their interactions, "
        "and inheritance hierarchies. In the SecuExam project, OOP principles show up in both the "
        "backend (Python classes and modules) and the test suite itself."
    ))

    story.append(h2("9.1 OOP Principles in SecuExam Testing"))
    oop_table = make_table(
        ["OOP Principle", "How It's Applied"],
        [
            ["Inheritance", "All 6 test classes inherit from SecuExamTestBase, which provides shared browser setup, login helpers, and screenshot methods"],
            ["Encapsulation", "The login_as() method encapsulates the entire authentication flow (navigate, fill form, submit). Tests just call self.login_as('admin', creds) without knowing the details"],
            ["Polymorphism", "Each test class overrides setUp() to log in as a different role (setter, receiver, admin) while using the same base interface"],
            ["Abstraction", "The save_screenshot() method abstracts away filename formatting and directory management; tests just pass a descriptive name"],
        ],
        col_widths=[110, 350]
    )
    story.append(oop_table)
    story.append(spacer())

    story.append(h2("9.2 Classes Under Test"))
    story.append(p(
        "The backend's Shamir Secret Sharing module is a good example of OOP testing. "
        "The module exposes two key operations , split and reconstruct , that can be tested "
        "independently:"
    ))
    story.append(bullet(
        "Test that splitting a 32-byte secret produces exactly 5 shares"
    ))
    story.append(bullet(
        "Test that reconstructing from any 3 of the 5 shares recovers the original secret"
    ))
    story.append(bullet(
        "Test that using fewer than 3 shares does NOT recover the secret (negative test)"
    ))

    story.append(h2("9.3 Testing Tool"))
    story.append(p(
        "<b>Selenium WebDriver</b> is used alongside Python's unittest framework, which itself "
        "is object-oriented. Each test class encapsulates related tests, and inheritance provides "
        "shared functionality , making the test suite maintainable and extensible."
    ))

    story.append(PageBreak())

    # ===== 10. THEORETICAL , MUTATION TESTING =====
    story.append(h1("10. Theoretical Testing , Mutation Testing"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "Mutation testing checks whether our test suite is actually catching bugs. The idea is simple: "
        "you introduce small changes (called 'mutants') into the source code and see if the tests fail. "
        "If they do, the mutant is 'killed'. If they don't, the mutant 'survived' , meaning there's a "
        "gap in the tests."
    ))

    story.append(h2("10.1 Mutation Operators Applied"))
    story.append(p(
        "Here are five mutations we would introduce into the SecuExam backend to test the quality "
        "of our Selenium test suite:"
    ))
    mut_table = make_table(
        ["Mutant", "Original Logic", "Mutated Logic", "Which Test Kills It"],
        [
            ["M-01", "if now >= unlock_dt (allow download)", "if now <= unlock_dt (invert logic)", "TC-03 , Time-lock test fails because locked papers appear unlocked"],
            ["M-02", "Shamir threshold k=3", "Changed to k=2", "TC-02 , Encryption details show wrong threshold; assertion fails"],
            ["M-03", "if not bcrypt.checkpw(...) reject", "if bcrypt.checkpw(...) reject", "TC-01 , Valid credentials get rejected; TC-04 , Invalid ones succeed"],
            ["M-04", "role IN ('setter','receiver','admin')", "role IN ('setter','receiver')", "TC-05 , Admin login fails; dashboard tests break"],
            ["M-05", "Return 401 for unauthenticated", "Return 200 for unauthenticated", "TC-04 (security) , API returns wrong status code"],
        ],
        col_widths=[40, 110, 110, 200]
    )
    story.append(mut_table)
    story.append(spacer())

    story.append(h2("10.2 Expected Mutation Score"))
    story.append(p(
        "Based on the five mutations above, all five would be detected ('killed') by the existing "
        "Selenium test suite. This gives a mutation score of:"
    ))
    story.append(p("<b>Mutation Score = (5 killed / 5 total) × 100 = 100%</b>"))
    story.append(spacer())
    story.append(p(
        "This means the test suite is effective at catching logical errors in the core security features. "
        "In practice, a mutation score above 80% is generally considered strong."
    ))

    story.append(h2("10.3 Testing Tool"))
    story.append(p(
        "The process involves manually introducing mutations into server.py, re-running the "
        "<b>Selenium WebDriver</b> test suite, and checking which tests fail. Automated mutation "
        "testing tools like mutmut exist, but conceptually, the same Selenium tests serve as the "
        "oracle for detecting mutants."
    ))

    story.append(PageBreak())

    # ===== 11. CONCLUSION =====
    story.append(h1("11. Conclusion"))
    story.append(SectionDivider())
    story.append(spacer())

    story.append(p(
        "This case study covered the complete lifecycle of the SecuExam project, from designing "
        "and developing a secure web application to testing it thoroughly using Selenium WebDriver. "
        "The practical testing on the web app gave us real evidence in the form of screenshots, while "
        "the theoretical sections showed how the same project could be adapted for mobile app testing, "
        "DevOps CI/CD, object-oriented testing, and mutation testing."
    ))
    story.append(p(
        "The key takeaway for us was that a single testing tool, Selenium WebDriver, is versatile "
        "enough to handle functional testing, security validation, UI consistency checks, and even "
        "serve as the test oracle for mutation testing. Its extension through Appium also makes it "
        "suitable for mobile testing scenarios."
    ))
    story.append(p(
        "The SecuExam application itself demonstrates that exam paper security is achievable through "
        "a layered approach: encryption protects the data at rest, Shamir's Secret Sharing prevents "
        "single-point-of-failure in key management, time-locks enforce temporal access control, and "
        "watermarking provides accountability after distribution."
    ))

    story.append(spacer(20))
    story.append(SectionDivider(color=ACCENT, thickness=2))
    story.append(spacer(10))
    story.append(Paragraph(
        "SecuExam , Secure Exam Paper Distribution System<br/>"
        "Software Engineering Lab (BCSE301P) , Winter 2025-26<br/>"
        "Testing Tool: Selenium WebDriver (Python)",
        ParagraphStyle("EndNote", parent=styles["StudentInfo"], fontSize=10, leading=14)
    ))

    # ===== BUILD =====
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"\n✅ Report generated: {OUTPUT_PDF}")
    print(f"   Pages: ~22")
    print(f"   Screenshots: {sum(1 for v in SCREENSHOTS.values() if os.path.exists(v))}")


if __name__ == "__main__":
    build_report()
