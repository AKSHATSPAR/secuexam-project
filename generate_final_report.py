#!/usr/bin/env python3
"""Generate the final SecuExam report PDF with appendices and TOC."""

from __future__ import annotations

import subprocess
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PDF = BASE_DIR / "SecuExam_Final_Project_Report.pdf"
ASSET_DIR = BASE_DIR / "report_assets"
GENERATED_DIR = ASSET_DIR / "generated"
SCREENSHOT_DIR = BASE_DIR / "test_screenshots"

VIT_LOGO = ASSET_DIR / "vit_extract-000.png"

TIMES_REGULAR = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
TIMES_BOLD = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
TIMES_ITALIC = "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
COURIER_NEW = "/System/Library/Fonts/Supplemental/Courier New.ttf"
COURIER_NEW_BOLD = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"

PAGE_WIDTH, PAGE_HEIGHT = A4


@dataclass(frozen=True)
class DiagramPage:
    pdf_name: str
    page_number: int
    caption: str


@dataclass(frozen=True)
class CodeScreenshotSpec:
    output_name: str
    title: str
    file_path: Path
    start_marker: str
    end_marker: str
    screenshot_suffix: str
    caption: str


DIAGRAM_PAGES = [
    DiagramPage("Software Engineering Lab Submission 1 (3).pdf", 2, "SecuExam WBS page from Assignment 1"),
    DiagramPage("Software Engineering Lab Submission 1 (3).pdf", 4, "SecuExam activity diagram page from Assignment 1"),
    DiagramPage("Software Engineering Lab Submission 1 (3).pdf", 6, "SecuExam ER diagram page from Assignment 1"),
    DiagramPage("Software Engineering Lab Submission 2 (3).pdf", 8, "SecuExam RE model page from Assignment 2"),
    DiagramPage("Software Engineering Lab Submission 2 (3).pdf", 9, "SecuExam state diagram page from Assignment 2"),
    DiagramPage("Software Engineering Lab Submission 2 (3).pdf", 10, "SecuExam class diagram page from Assignment 2"),
    DiagramPage("Software Engineering Lab Submission 2 (3).pdf", 11, "SecuExam DFD page from Assignment 2"),
    DiagramPage("Software Engineering Lab Submission 2 (3).pdf", 12, "SecuExam use-case page from Assignment 2"),
    DiagramPage("23BDS0149_SW_LAB_ASGNMT3 (1).pdf", 3, "SecuExam UI / UX page from Assignment 3"),
    DiagramPage("23BDS0149_SW_LAB_ASGNMT3 (1).pdf", 4, "SecuExam component diagram page from Assignment 3"),
    DiagramPage("23BDS0149_SW_LAB_ASGNMT3 (1).pdf", 5, "SecuExam package diagram page from Assignment 3"),
    DiagramPage("23BDS0149_SW_LAB_ASGNMT3 (1).pdf", 6, "SecuExam deployment diagram page from Assignment 3"),
    DiagramPage("23BDS0149_SW_LAB_ASGNMT3 (1).pdf", 7, "SecuExam sequence diagram page from Assignment 3"),
]


SCREENSHOT_SUFFIXES = [
    ("_01_login_page_load.png", "Login page"),
    ("_08_register_modal_open.png", "Registration modal"),
    ("_09_setter_dashboard.png", "Setter dashboard"),
    ("_11_upload_form_filled.png", "Setter upload form"),
    ("_12_upload_encryption_result.png", "Setter upload result"),
    ("_14_receiver_dashboard.png", "Receiver dashboard"),
    ("_15_receiver_exam_list.png", "Receiver exam list"),
    ("_16_time_lock_status.png", "Time-lock enforcement"),
    ("_17_countdown_timers.png", "Receiver countdown state"),
    ("_18_security_notice.png", "Receiver security notice"),
    ("_19_admin_dashboard.png", "Admin dashboard"),
    ("_20_admin_analytics_charts.png", "Admin analytics"),
    ("_22_admin_users_tab.png", "Admin user management"),
    ("_23_admin_audit_logs.png", "Admin audit logs"),
    ("_24_admin_papers_tab.png", "Admin paper registry"),
]


CODE_SCREENSHOT_SPECS = [
    CodeScreenshotSpec(
        output_name="code_auth_login.png",
        title="server.py + Login Page",
        file_path=BASE_DIR / "server.py",
        start_marker='@app.route("/api/login", methods=["POST"])',
        end_marker='@app.route("/api/logout", methods=["POST"])',
        screenshot_suffix="_01_login_page_load.png",
        caption="Code screenshot showing backend authentication logic with the developed login interface.",
    ),
    CodeScreenshotSpec(
        output_name="code_setter_upload.png",
        title="setter.html + Upload Result",
        file_path=BASE_DIR / "secuexam_app" / "setter.html",
        start_marker="async function handleUpload(e)",
        end_marker="async function loadPapers()",
        screenshot_suffix="_12_upload_encryption_result.png",
        caption="Code screenshot showing the setter upload workflow beside the live encryption result screen.",
    ),
    CodeScreenshotSpec(
        output_name="code_receiver_download.png",
        title="receiver.html + Receiver Dashboard",
        file_path=BASE_DIR / "secuexam_app" / "receiver.html",
        start_marker="async function loadPapers()",
        end_marker="function closeDownloadModal()",
        screenshot_suffix="_16_time_lock_status.png",
        caption="Code screenshot showing receiver-side paper listing and time-lock UI behavior.",
    ),
    CodeScreenshotSpec(
        output_name="code_admin_tests.png",
        title="test_secuexam.py + Admin Dashboard",
        file_path=BASE_DIR / "test_secuexam.py",
        start_marker="class Test04_AdminDashboard(SecuExamTestBase):",
        end_marker="class Test05_UIConsistency(SecuExamTestBase):",
        screenshot_suffix="_19_admin_dashboard.png",
        caption="Code screenshot showing automated admin validation logic beside the admin control center UI.",
    ),
]


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("TimesNewRoman", TIMES_REGULAR))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", TIMES_BOLD))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Italic", TIMES_ITALIC))


SAMPLE_STYLES = getSampleStyleSheet()


def build_styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "title",
            parent=SAMPLE_STYLES["Title"],
            fontName="TimesNewRoman-Bold",
            fontSize=20,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "cover": ParagraphStyle(
            "cover",
            parent=SAMPLE_STYLES["Normal"],
            fontName="TimesNewRoman",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=5,
        ),
        "heading": ParagraphStyle(
            "heading",
            parent=SAMPLE_STYLES["Heading1"],
            fontName="TimesNewRoman-Bold",
            fontSize=14,
            leading=21,
            alignment=TA_LEFT,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "subheading": ParagraphStyle(
            "subheading",
            parent=SAMPLE_STYLES["Heading2"],
            fontName="TimesNewRoman-Bold",
            fontSize=12,
            leading=18,
            alignment=TA_LEFT,
            spaceBefore=5,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=SAMPLE_STYLES["BodyText"],
            fontName="TimesNewRoman",
            fontSize=12,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            splitLongWords=False,
        ),
        "body_center": ParagraphStyle(
            "body_center",
            parent=SAMPLE_STYLES["BodyText"],
            fontName="TimesNewRoman",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "caption",
            parent=SAMPLE_STYLES["BodyText"],
            fontName="TimesNewRoman-Italic",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "toc_entry": ParagraphStyle(
            "toc_entry",
            parent=SAMPLE_STYLES["BodyText"],
            fontName="TimesNewRoman",
            fontSize=12,
            leading=18,
            leftIndent=12,
            firstLineIndent=0,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=SAMPLE_STYLES["BodyText"],
            fontName="TimesNewRoman",
            fontSize=12,
            leading=18,
            alignment=TA_JUSTIFY,
            splitLongWords=False,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=SAMPLE_STYLES["BodyText"],
            fontName="TimesNewRoman-Bold",
            fontSize=12,
            leading=18,
            alignment=TA_LEFT,
        ),
    }


STYLES = build_styles()


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        template = PageTemplate(id="main", frames=[frame], onPage=draw_page_number)
        self.addPageTemplates([template])

    def afterFlowable(self, flowable):
        if hasattr(flowable, "toc_level"):
            text = flowable.getPlainText()
            key = getattr(flowable, "bookmark_name", None)
            if key:
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level=flowable.toc_level, closed=False)
            self.notify("TOCEntry", (flowable.toc_level, text, self.page, key))


def draw_page_number(canvas, doc) -> None:
    canvas.setFont("TimesNewRoman", 10)
    canvas.drawCentredString(PAGE_WIDTH / 2, 1.1 * cm, str(doc.page))


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def main_heading(text: str) -> Paragraph:
    para = p(text, "heading")
    para.toc_level = 0
    para.bookmark_name = text.lower().replace(" ", "_").replace(".", "")
    return para


def sub_heading(text: str) -> Paragraph:
    return p(text, "subheading")


def spacer(height: float = 0.25) -> Spacer:
    return Spacer(1, height * cm)


def latest_screenshot(suffix: str) -> Path:
    matches = sorted(SCREENSHOT_DIR.glob(f"*{suffix}"))
    if not matches:
        raise FileNotFoundError(f"Missing screenshot for suffix {suffix}")
    return matches[-1]


def image_for_pdf_page(pdf_name: str, page_number: int) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = BASE_DIR / pdf_name
    stem = GENERATED_DIR / f"{pdf_path.stem.replace(' ', '_')}_page_{page_number}"
    png_path = stem.with_suffix(".png")
    if not png_path.exists():
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-singlefile",
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                str(pdf_path),
                str(stem),
            ],
            check=True,
        )
    return png_path


def fit_image(path: Path, max_width_cm: float, max_height_cm: float) -> Image:
    with PILImage.open(path) as image:
        width_px, height_px = image.size
    max_width = max_width_cm * cm
    max_height = max_height_cm * cm
    scale = min(max_width / width_px, max_height / height_px)
    flowable = Image(str(path), width=width_px * scale, height=height_px * scale)
    flowable.hAlign = "CENTER"
    return flowable


def table(data: list[list[str]], column_widths_cm: list[float]) -> Table:
    rows = []
    for row_index, row in enumerate(data):
        style_name = "table_header" if row_index == 0 else "table_cell"
        rows.append([Paragraph(cell, STYLES[style_name]) for cell in row])
    flowable = Table(rows, colWidths=[width * cm for width in column_widths_cm], hAlign="LEFT")
    flowable.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e5f6")),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return flowable


def extract_code_snippet(path: Path, start_marker: str, end_marker: str, max_lines: int = 22) -> list[str]:
    lines = path.read_text().splitlines()
    start = next(index for index, line in enumerate(lines) if start_marker in line)
    end = next(index for index, line in enumerate(lines[start + 1 :], start=start + 1) if end_marker in line)
    snippet = lines[start:end]
    cleaned = []
    for line in snippet[:max_lines]:
        wrapped = textwrap.wrap(
            line.expandtabs(4),
            width=54,
            break_long_words=False,
            break_on_hyphens=False,
        )
        cleaned.extend(wrapped if wrapped else [""])
    return cleaned[:max_lines]


def build_code_ui_screenshot(spec: CodeScreenshotSpec) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / spec.output_name
    if output_path.exists():
        return output_path

    code_lines = extract_code_snippet(spec.file_path, spec.start_marker, spec.end_marker)
    ui_path = latest_screenshot(spec.screenshot_suffix)
    ui_image = PILImage.open(ui_path).convert("RGB")

    canvas_width = 1800
    canvas_height = 980
    left_width = 980
    right_width = canvas_width - left_width

    canvas = PILImage.new("RGB", (canvas_width, canvas_height), "#f4f6fa")
    draw = ImageDraw.Draw(canvas)

    header_height = 54
    code_bg = "#1e1e1e"
    code_fg = "#d4d4d4"
    line_no_fg = "#858585"
    accent = "#2d2d30"

    draw.rounded_rectangle((40, 36, left_width - 20, canvas_height - 36), radius=18, fill=code_bg, outline="#111111", width=2)
    draw.rounded_rectangle((left_width + 10, 36, canvas_width - 40, canvas_height - 36), radius=18, fill="#ffffff", outline="#d0d0d0", width=2)
    draw.rectangle((40, 36, left_width - 20, 36 + header_height), fill=accent)
    draw.rectangle((left_width + 10, 36, canvas_width - 40, 36 + header_height), fill="#e9edf5")

    title_font = ImageFont.truetype(TIMES_BOLD, 24)
    code_font = ImageFont.truetype(COURIER_NEW, 22)
    code_font_bold = ImageFont.truetype(COURIER_NEW_BOLD, 22)

    draw.text((66, 52), spec.file_path.name, fill="#ffffff", font=title_font)
    draw.text((left_width + 36, 52), spec.title, fill="#1f2937", font=title_font)

    y = 120
    line_height = 32
    for index, line in enumerate(code_lines, start=1):
        draw.text((70, y), f"{index:>2}", fill=line_no_fg, font=code_font)
        draw.text((125, y), line, fill=code_fg, font=code_font_bold if index == 1 else code_font)
        y += line_height

    target_width = right_width - 90
    target_height = canvas_height - 140
    ui_copy = ui_image.copy()
    ui_copy.thumbnail((target_width, target_height))
    x = left_width + 30 + (target_width - ui_copy.width) // 2
    y = 90 + (target_height - ui_copy.height) // 2
    canvas.paste(ui_copy, (x, y))

    canvas.save(output_path)
    return output_path


def build_code_screenshots() -> list[tuple[Path, str]]:
    result = []
    for spec in CODE_SCREENSHOT_SPECS:
        result.append((build_code_ui_screenshot(spec), spec.caption))
    return result


def add_cover(story: list) -> None:
    story.append(spacer(0.5))
    story.append(fit_image(VIT_LOGO, 15, 4.5))
    story.append(spacer(0.4))
    story.append(p("SecuExam Project Documentation", "title"))
    story.append(p("Secure Exam Paper Distribution System", "cover"))
    story.append(p("Software Engineering Lab (BCSE301P)", "cover"))
    story.append(p("Assignment 4 - Final Project Report", "cover"))
    story.append(spacer(0.4))
    story.append(p("Prepared By", "subheading"))
    story.append(
        table(
            [
                ["Name", "Registration Number", "Role"],
                ["Akshat Sparsh", "23BDS0149", "Primary Submitter"],
                ["Tanuj Kapoor", "23BCT0030", "Team Member"],
                ["Kartik Kandwal", "23BCT0060", "Team Member"],
            ],
            [5.2, 5.4, 4.4],
        )
    )
    story.append(spacer(0.3))
    story.append(p("Vellore Institute of Technology", "body_center"))
    story.append(p(datetime.now().strftime("%d %B %Y"), "body_center"))
    story.append(PageBreak())


def add_index_page(story: list) -> None:
    story.append(p("Index Page", "heading"))
    story.append(
        table(
            [
                ["Field", "Details"],
                ["Project Title", "SecuExam - Secure Exam Paper Distribution System"],
                ["Scope", "Final project implementation, documentation, testing, screenshots, and SecuExam-only UML appendix."],
                ["Technology Base", "Flask backend, SQLite database, static HTML/CSS/JS frontend, ReportLab and Pillow for report generation."],
                ["Security Focus", "AES-256 encryption, Shamir key splitting, time-lock access control, watermarking, audit logs, bcrypt-based authentication."],
                ["Evidence Included", "Developed system screenshots, code screenshots, testing summary, and diagram pages from previous SecuExam submissions."],
            ],
            [5.0, 11.0],
        )
    )
    story.append(spacer(0.25))
    story.append(
        p(
            "This report is prepared only for the SecuExam project. CrowdQuest is not used as an implementation source. The previous assignment pages appended here are limited to SecuExam content only.",
        )
    )
    story.append(PageBreak())


def add_toc_page(story: list, toc: TableOfContents) -> None:
    story.append(p("Table of Contents", "heading"))
    story.append(toc)
    story.append(PageBreak())


def section_paragraphs(items: Iterable[str]) -> list[Paragraph]:
    return [p(item) for item in items]


def build_story(toc: TableOfContents) -> list:
    code_shots = build_code_screenshots()
    story: list = []

    add_cover(story)
    add_index_page(story)
    add_toc_page(story, toc)

    story.append(main_heading("1. Introduction"))
    story.extend(
        section_paragraphs(
            [
                "SecuExam is a secure digital platform for distributing examination papers from the university to authorized exam centers without relying on physical transport. The implemented system focuses on the highest-risk stage of the examination pipeline: last-mile paper delivery before the exam starts.",
                "The application is built as a role-based web system with dedicated workflows for Paper Setter, Receiver, and Administrator. Each action is gated by authenticated sessions and explicit role checks. Security is enforced at multiple layers rather than through a single control.",
            ]
        )
    )

    story.append(main_heading("2. Problem Statement"))
    story.extend(
        section_paragraphs(
            [
                "Manual or poorly controlled distribution of exam papers creates a high risk of leaks, tampering, and early access. Physical logistics are expensive, operationally difficult to audit, and still vulnerable to insider compromise during transport and storage.",
                "A secure digital alternative must solve multiple technical problems simultaneously: confidential storage, controlled timed release, identity-aware downloads, and post-incident traceability. Without all of these controls working together, a paper distribution platform remains incomplete.",
            ]
        )
    )

    story.append(main_heading("3. Objectives"))
    story.extend(
        section_paragraphs(
            [
                "1. Replace risky physical paper transport with a secure digital delivery workflow.",
                "2. Ensure every uploaded paper is encrypted before storage and inaccessible in plain form.",
                "3. Enforce timed availability through server-side time-lock validation.",
                "4. Record every critical access event in an auditable log.",
                "5. Apply receiver-specific watermarking to trace unauthorized sharing.",
                "6. Provide a simple and role-specific interface that reduces operational mistakes.",
            ]
        )
    )

    story.append(main_heading("4. Proposed System"))
    story.append(
        p(
            "The proposed system is a centralized secure distribution platform. A setter uploads a PDF and enters subject, exam start time, and duration. The backend validates the file, encrypts it with AES-256, splits the key into multiple fragments, and stores the encrypted artifact with its schedule metadata. A receiver can see the paper in the scheduled exam list but cannot download it before the unlock time. Once the request is valid, the paper is decrypted on demand, dynamically watermarked, logged, and returned as a downloadable PDF.",
        )
    )
    story.append(sub_heading("4.1 Software Requirements Specification (SRS)"))
    story.append(
        table(
            [
                ["Requirement Type", "Implemented Requirement"],
                ["Functional", "Role-based login, PDF upload, secure scheduling, time-locked download, watermarking, admin monitoring, audit log visibility."],
                ["Security", "AES-256 encryption, key fragmentation, bcrypt hashing, protected routes, authenticated APIs, access logging."],
                ["Data", "Users, papers, schedules, key fragments, and logs persisted in normalized SQLite tables."],
                ["Usability", "Focused dashboards for each role and visible security notices during critical actions."],
                ["Operational", "Reset utility, seeded demo users, README instructions, and automated Selenium validation."],
            ],
            [4.7, 11.3],
        )
    )
    story.append(sub_heading("4.2 Functional Flow"))
    story.extend(
        section_paragraphs(
            [
                "Setter flow: login -> upload paper -> enter schedule -> backend encrypts paper -> key shares are generated -> encrypted paper and metadata are stored -> success details are shown in the UI.",
                "Receiver flow: login -> open scheduled exams -> time-lock status is checked continuously -> if unlocked, request download -> backend reconstructs key -> decrypts PDF -> adds watermark -> logs the event -> returns the watermarked file.",
                "Admin flow: login -> inspect analytics -> approve or delete users -> view audit logs -> review all uploaded papers and key-share status.",
            ]
        )
    )

    story.append(main_heading("5. Technologies Used"))
    story.append(
        table(
            [
                ["Technology", "Use in SecuExam"],
                ["Python Flask", "HTTP routing, backend logic, session handling, API endpoints."],
                ["SQLite", "Persistent storage for users, exam papers, schedules, key fragments, and logs."],
                ["HTML / CSS / JavaScript", "Role-specific dashboards and frontend workflows."],
                ["bcrypt", "Secure password hashing."],
                ["cryptography", "AES-256 encryption and decryption support."],
                ["ReportLab and PyPDF2", "Dynamic watermarking and PDF report generation."],
                ["Selenium WebDriver", "End-to-end automated testing of the developed system."],
            ],
            [4.6, 11.4],
        )
    )

    story.append(main_heading("6. System Architecture"))
    story.extend(
        section_paragraphs(
            [
                "SecuExam is organized around a Flask backend in `server.py`, frontend pages in `secuexam_app/`, encrypted file storage in `secuexam_app/uploads/`, and a SQLite database. This structure keeps the application simple enough for the lab while still covering the full secure-delivery pipeline.",
                "At runtime, the browser interacts with the backend through authenticated sessions and JSON/FormData API calls. The backend routes the request into the correct workflow: authentication, upload and scheduling, paper listing, secure download, or admin management. Database writes and reads are isolated through helper functions and table relationships.",
            ]
        )
    )
    story.append(
        table(
            [
                ["Architecture Layer", "Responsibility"],
                ["Presentation Layer", "Login page, setter dashboard, receiver dashboard, admin dashboard, countdowns, result cards, security banners."],
                ["Application Layer", "Request validation, upload flow, schedule handling, time-lock logic, admin operations."],
                ["Security Layer", "AES encryption, Shamir-style key fragment handling, watermarking, session checks, client IP capture."],
                ["Persistence Layer", "SQLite storage and encrypted file persistence."],
            ],
            [4.8, 11.2],
        )
    )

    story.append(main_heading("7. Modules"))
    story.append(sub_heading("7.1 Authentication Module"))
    story.extend(
        section_paragraphs(
            [
                "This module handles login, logout, session storage, role-based route protection, and the current-user identity endpoint. It ensures that setters, receivers, and admins are redirected only to their permitted dashboards.",
            ]
        )
    )
    auth_image = fit_image(latest_screenshot("_01_login_page_load.png"), 16.5, 10.0)
    story.append(auth_image)
    story.append(p("Step 1 module photo: login page of the developed system.", "caption"))

    story.append(sub_heading("7.2 Setter Module"))
    story.extend(
        section_paragraphs(
            [
                "The setter module validates file type and schedule input, encrypts the paper, creates key shares, stores encrypted output, and updates the upload history table. The UI also shows the resulting paper ID, encryption type, and key-share summary after a successful upload.",
            ]
        )
    )
    story.append(fit_image(latest_screenshot("_11_upload_form_filled.png"), 16.5, 10.0))
    story.append(p("Step 2 module photo: setter enters paper metadata and schedule.", "caption"))
    story.append(fit_image(latest_screenshot("_12_upload_encryption_result.png"), 16.5, 10.0))
    story.append(p("Step 3 module photo: encryption result and scheduling confirmation.", "caption"))

    story.append(sub_heading("7.3 Receiver Module"))
    story.extend(
        section_paragraphs(
            [
                "The receiver module lists scheduled exams, continuously updates countdown timers, blocks access before unlock time, and allows secure watermarked download only in the permitted window. The user receives clear security messaging explaining that all downloads are traceable.",
            ]
        )
    )
    story.append(fit_image(latest_screenshot("_15_receiver_exam_list.png"), 16.5, 10.0))
    story.append(p("Step 4 module photo: receiver views the scheduled exam list.", "caption"))
    story.append(fit_image(latest_screenshot("_16_time_lock_status.png"), 16.5, 10.0))
    story.append(p("Step 5 module photo: receiver sees locked state and unlock timing.", "caption"))

    story.append(sub_heading("7.4 Admin Module"))
    story.extend(
        section_paragraphs(
            [
                "The admin module provides analytics, user management, audit logs, and paper visibility. It is the oversight layer of the system and is responsible for approval workflows and traceability after each paper interaction.",
            ]
        )
    )
    story.append(fit_image(latest_screenshot("_19_admin_dashboard.png"), 16.5, 10.0))
    story.append(p("Step 6 module photo: admin dashboard overview.", "caption"))
    story.append(fit_image(latest_screenshot("_23_admin_audit_logs.png"), 16.5, 10.0))
    story.append(p("Step 7 module photo: admin audit log inspection.", "caption"))

    story.append(main_heading("8. UML Diagrams (Description)"))
    story.extend(
        section_paragraphs(
            [
                "The UML and design artefacts for SecuExam were produced in the earlier lab assignments and are included again in Appendix C as direct SecuExam-only page extracts. These include the WBS, activity diagram, ER diagram, RE model, state diagram, class diagram, DFDs, use-case diagram, UI / UX design page, component diagram, package diagram, deployment diagram, and sequence diagram.",
                "These diagrams map directly to the implemented system. The class and ER diagrams align with the SQLite schema and role model; the sequence and activity diagrams align with the implemented setter and receiver workflows; the deployment and component views align with the current Flask-based architecture.",
            ]
        )
    )
    story.append(
        table(
            [
                ["Diagram", "Purpose in the Final System"],
                ["WBS", "Shows project breakdown across planning, development, testing, and deployment."],
                ["Activity / Sequence", "Explains the secure upload and controlled download workflow."],
                ["ER / Class", "Matches the entities and object relationships implemented in the backend."],
                ["DFD / Use Case", "Shows actor actions and data movement across the application."],
                ["Component / Package / Deployment", "Describes code organization and runtime placement of the system."],
            ],
            [4.8, 11.2],
        )
    )

    story.append(main_heading("9. Testing"))
    story.extend(
        section_paragraphs(
            [
                "Testing was carried out with Selenium WebDriver using Python `unittest`. The suite validates the developed system across authentication, setter flow, receiver flow, admin oversight, UI consistency, and explicit security edge cases.",
                "The current verified test result in this workspace is 34 out of 34 tests passed. The automated suite now covers the stable project state and produces screenshot evidence during execution.",
            ]
        )
    )
    story.append(sub_heading("9.1 Test Summary"))
    story.append(
        table(
            [
                ["Test Area", "Coverage"],
                ["Login", "Page load, role switching, invalid login, empty validation, role redirects, register modal."],
                ["Setter", "Dashboard, upload zone, secure upload, encryption result, upload history."],
                ["Receiver", "Dashboard, exam list, time-lock, countdown, security notice."],
                ["Admin", "Analytics, user management, audit logs, papers, tab navigation."],
                ["Security", "Unauthorized route access, SQL injection, XSS attempt, unauthenticated API handling."],
            ],
            [4.8, 11.2],
        )
    )
    story.append(sub_heading("9.2 UML Testing and Traceability"))
    story.extend(
        section_paragraphs(
            [
                "The testing results are consistent with the UML descriptions. Use-case expectations for setter upload, receiver download, and admin monitoring are validated through automated browser tests. State-related checks such as locked versus unlocked access are directly exercised in the receiver suite. The design artefacts are therefore not only descriptive but traceable to working implementation behavior.",
            ]
        )
    )
    story.append(sub_heading("9.3 Sample Result Table"))
    story.append(
        table(
            [
                ["Test Case", "Expected Output", "Result"],
                ["Authenticated setter upload", "Encrypted paper scheduled and shown in result panel", "Pass"],
                ["Receiver before unlock", "Locked status visible and no early access", "Pass"],
                ["Admin audit log view", "Download attempts visible with trace data", "Pass"],
                ["Unauthenticated API access", "401 returned", "Pass"],
            ],
            [7.6, 7.1, 2.0],
        )
    )

    story.append(main_heading("10. Advantages"))
    story.extend(
        section_paragraphs(
            [
                "SecuExam reduces leakage risk through layered security rather than a single mechanism.",
                "The application is operationally simple for the three required roles and avoids unnecessary UI complexity.",
                "The system provides traceability through watermarking and audit logs, which is essential for accountability.",
                "The implemented test suite makes the current build reproducible and verifiable.",
            ]
        )
    )

    story.append(main_heading("11. Limitations"))
    story.extend(
        section_paragraphs(
            [
                "The current deployment is local and SQLite-based, which is appropriate for the lab but not sufficient for production-scale concurrency or disaster recovery.",
                "The time-lock model depends on correct server time and assumes the backend remains available during the exam window.",
                "The system currently uses local encrypted file storage rather than hardened cloud object storage.",
            ]
        )
    )

    story.append(main_heading("12. Future Enhancements"))
    story.extend(
        section_paragraphs(
            [
                "Move the backend to a managed deployment target with persistent storage and HTTPS termination.",
                "Add stronger administrative controls around key-fragment ownership and recovery workflows.",
                "Introduce richer reporting and downloadable audit summaries for exam governance.",
                "Replace local file storage with a cloud object store and move from SQLite to a server-grade relational database.",
            ]
        )
    )

    story.append(main_heading("13. Conclusion"))
    story.extend(
        section_paragraphs(
            [
                "SecuExam is implemented as a complete secure exam paper distribution system within the scope of the software engineering lab. The system covers the required secure-delivery lifecycle from upload through timed release and traceable download. It also includes the required documentation artefacts, UML continuity from previous assignments, and end-to-end automated validation.",
            ]
        )
    )

    story.append(PageBreak())
    story.append(main_heading("Appendix A. Code Screenshots"))
    story.append(
        p(
            "The following pages show code from the actual SecuExam implementation paired with screenshots of the developed system. These are generated from the current workspace files and the latest successful application screenshots.",
        )
    )
    for image_path, caption in code_shots:
        story.append(sub_heading(caption))
        story.append(fit_image(image_path, 17.0, 11.5))
        story.append(p(caption, "caption"))
        story.append(spacer(0.15))

    story.append(PageBreak())
    story.append(main_heading("Appendix B. Screenshot of the Developed System"))
    for suffix, caption in SCREENSHOT_SUFFIXES:
        story.append(sub_heading(caption))
        story.append(fit_image(latest_screenshot(suffix), 16.8, 10.2))
        story.append(p(caption, "caption"))
        story.append(spacer(0.15))

    story.append(PageBreak())
    story.append(main_heading("Appendix C. SecuExam Diagram Pages from Previous Assignments"))
    story.append(
        p(
            "These pages are direct image extracts from the previous SecuExam assignment PDFs. Only SecuExam pages are included here. CrowdQuest pages are not appended.",
        )
    )
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.black))
    story.append(spacer(0.2))

    for item in DIAGRAM_PAGES:
        story.append(PageBreak())
        story.append(sub_heading(item.caption))
        story.append(fit_image(image_for_pdf_page(item.pdf_name, item.page_number), 17.0, 23.0))
        story.append(p(f"Source: {item.pdf_name}, page {item.page_number}", "caption"))

    return story


def build_toc() -> TableOfContents:
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            name="TOCLevel1",
            fontName="TimesNewRoman",
            fontSize=12,
            leading=18,
            leftIndent=16,
            firstLineIndent=0,
        )
    ]
    toc.dotsMinLevel = 0
    return toc


def build_report() -> None:
    register_fonts()
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    doc = ReportDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=1.8 * cm,
        title="SecuExam Project Documentation",
        author="Akshat Sparsh",
    )

    toc = build_toc()
    story = build_story(toc)
    doc.multiBuild(story)
    print(f"Generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_report()
