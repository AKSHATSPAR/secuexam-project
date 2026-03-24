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
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
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
MANUAL_SCREENSHOT_DIR = ASSET_DIR / "manual_code_screenshots"

VIT_LOGO = ASSET_DIR / "vit_extract-000.png"
REPO_URL = "https://github.com/AKSHATSPAR/secuexam-project"

TIMES_REGULAR = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
TIMES_BOLD = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
TIMES_ITALIC = "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
COURIER_NEW = "/System/Library/Fonts/Supplemental/Courier New.ttf"

PAGE_WIDTH, PAGE_HEIGHT = A4


@dataclass(frozen=True)
class DiagramPage:
    pdf_name: str
    page_number: int
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

UML_DESCRIPTIONS = [
    ("WBS", "The Work Breakdown Structure decomposes SecuExam into planning, implementation, testing, and deployment activities. It shows that security features such as encryption, time-locking, and auditability were treated as first-class development tasks rather than add-ons."),
    ("Activity Diagram", "The activity diagram captures the operational flow for paper upload and secure retrieval. It shows how validation, encryption, scheduling, time checks, decryption, watermarking, and download are sequenced inside the application."),
    ("ER Diagram", "The ER diagram defines the persistent structure used by SecuExam. It models users, papers, schedules, key fragments, and download logs, which directly correspond to the implemented SQLite schema."),
    ("RE Model", "The requirements engineering model organizes the project from problem identification through elicitation, specification, validation, and management. It explains how the SecuExam scope was derived and controlled across the project lifecycle."),
    ("State Diagram", "The state diagram represents the paper lifecycle from uploaded to encrypted to time-locked and finally retrievable. It also reflects blocked paths such as early download attempts and expiry after the exam window."),
    ("Class Diagram", "The class diagram describes the logical object structure of the system, including user roles, papers, schedules, download requests, and logs. It is the design-level representation of the current implementation model."),
    ("DFD", "The data-flow diagrams show how information moves through authentication, upload, download, and admin modules. They make explicit where the system checks permissions, schedules, keys, and logs during each transaction."),
    ("Use Case Diagram", "The use-case diagram maps the responsibilities of the paper setter, receiver, and administrator. It shows which actions are available to each role and what internal security actions are triggered as part of those use cases."),
    ("UI / UX Design", "The UI / UX design page documents the intended flow of each dashboard and the minimal interaction model used by SecuExam. It explains why the interface remains focused on clarity and operational safety."),
    ("Component Diagram", "The component diagram explains how frontend pages, backend services, security functions, database access, and storage work together. It shows the implemented system as a set of cooperating modules rather than one undifferentiated block."),
    ("Package Diagram", "The package diagram organizes the project into presentation, application, domain, security, and infrastructure concerns. This reflects the way the final codebase separates user interface code from backend and security logic."),
    ("Deployment Diagram", "The deployment diagram describes the runtime placement of the browser client, Flask backend, database, and encrypted storage. It also highlights the importance of trusted server time for time-lock enforcement."),
    ("Sequence Diagram", "The sequence diagram explains the most security-critical interaction in the system: receiver download. It shows request validation, time-lock check, key reconstruction, decryption, watermarking, log creation, and file delivery in order."),
]


MANUAL_SCREENSHOT_SPECS = [
    ("manual_code_login.png", "Open `/Users/akshat/SOFTWARE_COURSE_BASED PROJECT/server.py` in VS Code on the left at the `/api/login` function, and keep the SecuExam login page open on the right."),
    ("manual_code_setter.png", "Open `/Users/akshat/SOFTWARE_COURSE_BASED PROJECT/secuexam_app/setter.html` in VS Code on the left at `handleUpload`, and keep the successful setter upload result screen open on the right."),
    ("manual_code_receiver.png", "Open `/Users/akshat/SOFTWARE_COURSE_BASED PROJECT/secuexam_app/receiver.html` in VS Code on the left at `loadPapers`, and keep the receiver dashboard/time-lock screen open on the right."),
    ("manual_code_admin.png", "Open `/Users/akshat/SOFTWARE_COURSE_BASED PROJECT/test_secuexam.py` in VS Code on the left at `class Test04_AdminDashboard`, and keep the admin dashboard open on the right."),
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
            alignment=TA_JUSTIFY,
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


def append_main_heading(story: list, text: str) -> None:
    story.append(CondPageBreak(4 * cm))
    story.append(main_heading(text))


def append_sub_heading(story: list, text: str) -> None:
    story.append(CondPageBreak(3.5 * cm))
    story.append(sub_heading(text))


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


def build_code_block(path: Path, start_marker: str, end_marker: str, max_lines: int = 60) -> str:
    lines = extract_code_snippet(path, start_marker, end_marker, max_lines=max_lines)
    wrapped = []
    for line in lines:
        chunks = textwrap.wrap(
            line,
            width=98,
            break_long_words=False,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        wrapped.extend(chunks if chunks else [""])
    return "\n".join(wrapped)


def manual_screenshot_paths() -> list[tuple[Path, str]]:
    result = []
    for filename, caption in MANUAL_SCREENSHOT_SPECS:
        image_path = MANUAL_SCREENSHOT_DIR / filename
        if image_path.exists():
            result.append((image_path, caption))
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
    append_main_heading(story, "Index Page")
    story.append(
        table(
            [
                ["Field", "Details"],
                ["Project Title", "SecuExam - Secure Exam Paper Distribution System"],
                ["Scope", "Final project implementation, documentation, testing, screenshots, and SecuExam-only UML appendix."],
                ["Technology Base", "Flask backend, SQLite database, static HTML/CSS/JS frontend, ReportLab and Pillow for report generation."],
                ["Security Focus", "AES-256 encryption, Shamir key splitting, time-lock access control, watermarking, audit logs, bcrypt-based authentication."],
                ["Evidence Included", "Developed system screenshots, code screenshots, testing summary, and diagram pages from previous SecuExam submissions."],
                ["Repository Link", REPO_URL],
            ],
            [5.0, 11.0],
        )
    )
    story.append(PageBreak())


def add_toc_page(story: list, toc: TableOfContents) -> None:
    append_main_heading(story, "Table of Contents")
    story.append(toc)
    story.append(PageBreak())


def section_paragraphs(items: Iterable[str]) -> list[Paragraph]:
    return [p(item) for item in items]


def build_story(toc: TableOfContents) -> list:
    manual_shots = manual_screenshot_paths()
    story: list = []

    add_cover(story)
    add_index_page(story)
    add_toc_page(story, toc)

    append_main_heading(story, "1. Introduction")
    story.extend(
        section_paragraphs(
            [
                "SecuExam is a secure digital platform for distributing examination papers from the university to authorized exam centers without relying on physical transport. The implemented system focuses on the highest-risk stage of the examination pipeline: last-mile paper delivery before the exam starts.",
                "The application is built as a role-based web system with dedicated workflows for Paper Setter, Receiver, and Administrator. Each action is gated by authenticated sessions and explicit role checks. Security is enforced at multiple layers rather than through a single control.",
            ]
        )
    )

    append_main_heading(story, "2. Problem Statement")
    story.extend(
        section_paragraphs(
            [
                "Manual or poorly controlled distribution of exam papers creates a high risk of leaks, tampering, and early access. Physical logistics are expensive, operationally difficult to audit, and still vulnerable to insider compromise during transport and storage.",
                "A secure digital alternative must solve multiple technical problems simultaneously: confidential storage, controlled timed release, identity-aware downloads, and post-incident traceability. Without all of these controls working together, a paper distribution platform remains incomplete.",
            ]
        )
    )

    append_main_heading(story, "3. Objectives")
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

    append_main_heading(story, "4. Proposed System")
    story.append(
        p(
            "The proposed system is a centralized secure distribution platform. A setter uploads a PDF and enters subject, exam start time, and duration. The backend validates the file, encrypts it with AES-256, splits the key into multiple fragments, and stores the encrypted artifact with its schedule metadata. A receiver can see the paper in the scheduled exam list but cannot download it before the unlock time. Once the request is valid, the paper is decrypted on demand, dynamically watermarked, logged, and returned as a downloadable PDF.",
        )
    )
    append_sub_heading(story, "4.1 Software Requirements Specification (SRS)")
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
    append_sub_heading(story, "4.2 Functional Flow")
    story.extend(
        section_paragraphs(
            [
                "Setter flow: login -> upload paper -> enter schedule -> backend encrypts paper -> key shares are generated -> encrypted paper and metadata are stored -> success details are shown in the UI.",
                "Receiver flow: login -> open scheduled exams -> time-lock status is checked continuously -> if unlocked, request download -> backend reconstructs key -> decrypts PDF -> adds watermark -> logs the event -> returns the watermarked file.",
                "Admin flow: login -> inspect analytics -> approve or delete users -> view audit logs -> review all uploaded papers and key-share status.",
            ]
        )
    )

    append_main_heading(story, "5. Technologies Used")
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

    append_main_heading(story, "6. System Architecture")
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

    append_main_heading(story, "7. Modules")
    append_sub_heading(story, "7.1 Authentication Module")
    story.extend(
        section_paragraphs(
            [
                "This module handles login, logout, session storage, role-based route protection, and the current-user identity endpoint. It ensures that setters, receivers, and admins are redirected only to their permitted dashboards.",
            ]
        )
    )
    story.append(KeepTogether([fit_image(latest_screenshot("_01_login_page_load.png"), 16.5, 10.0), p("Step 1 module photo: login page of the developed system.", "caption")]))

    append_sub_heading(story, "7.2 Setter Module")
    story.extend(
        section_paragraphs(
            [
                "The setter module validates file type and schedule input, encrypts the paper, creates key shares, stores encrypted output, and updates the upload history table. The UI also shows the resulting paper ID, encryption type, and key-share summary after a successful upload.",
            ]
        )
    )
    story.append(KeepTogether([fit_image(latest_screenshot("_11_upload_form_filled.png"), 16.5, 10.0), p("Step 2 module photo: setter enters paper metadata and schedule.", "caption")]))
    story.append(KeepTogether([fit_image(latest_screenshot("_12_upload_encryption_result.png"), 16.5, 10.0), p("Step 3 module photo: encryption result and scheduling confirmation.", "caption")]))

    append_sub_heading(story, "7.3 Receiver Module")
    story.extend(
        section_paragraphs(
            [
                "The receiver module lists scheduled exams, continuously updates countdown timers, blocks access before unlock time, and allows secure watermarked download only in the permitted window. The user receives clear security messaging explaining that all downloads are traceable.",
            ]
        )
    )
    story.append(KeepTogether([fit_image(latest_screenshot("_15_receiver_exam_list.png"), 16.5, 10.0), p("Step 4 module photo: receiver views the scheduled exam list.", "caption")]))
    story.append(KeepTogether([fit_image(latest_screenshot("_16_time_lock_status.png"), 16.5, 10.0), p("Step 5 module photo: receiver sees locked state and unlock timing.", "caption")]))

    append_sub_heading(story, "7.4 Admin Module")
    story.extend(
        section_paragraphs(
            [
                "The admin module provides analytics, user management, audit logs, and paper visibility. It is the oversight layer of the system and is responsible for approval workflows and traceability after each paper interaction.",
            ]
        )
    )
    story.append(KeepTogether([fit_image(latest_screenshot("_19_admin_dashboard.png"), 16.5, 10.0), p("Step 6 module photo: admin dashboard overview.", "caption")]))
    story.append(KeepTogether([fit_image(latest_screenshot("_23_admin_audit_logs.png"), 16.5, 10.0), p("Step 7 module photo: admin audit log inspection.", "caption")]))

    append_main_heading(story, "8. UML Diagrams (Description)")
    story.extend(
        section_paragraphs(
            [
                "The UML and design artefacts for SecuExam are part of the final documentation because they explain how the implemented system was analysed and structured before and during development. The diagram images are included later in Appendix C, but their meaning is also described here in text so that the report remains readable without depending on image text.",
            ]
        )
    )
    for title, description in UML_DESCRIPTIONS:
        append_sub_heading(story, f"8.{UML_DESCRIPTIONS.index((title, description)) + 1} {title}")
        story.append(p(description))

    append_main_heading(story, "9. Testing")
    story.extend(
        section_paragraphs(
            [
                "Testing was carried out with Selenium WebDriver using Python `unittest`. The suite validates the developed system across authentication, setter flow, receiver flow, admin oversight, UI consistency, and explicit security edge cases.",
                "The current verified test result in this workspace is 34 out of 34 tests passed. The automated suite now covers the stable project state and produces screenshot evidence during execution.",
            ]
        )
    )
    append_sub_heading(story, "9.1 Test Summary")
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
    append_sub_heading(story, "9.2 UML Testing and Traceability")
    story.extend(
        section_paragraphs(
            [
                "The testing results are consistent with the UML descriptions. Use-case expectations for setter upload, receiver download, and admin monitoring are validated through automated browser tests. State-related checks such as locked versus unlocked access are directly exercised in the receiver suite. The design artefacts are therefore not only descriptive but traceable to working implementation behavior.",
            ]
        )
    )
    append_sub_heading(story, "9.3 Sample Result Table")
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

    append_main_heading(story, "10. Advantages")
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

    append_main_heading(story, "11. Limitations")
    story.extend(
        section_paragraphs(
            [
                "The current deployment is local and SQLite-based, which is appropriate for the lab but not sufficient for production-scale concurrency or disaster recovery.",
                "The time-lock model depends on correct server time and assumes the backend remains available during the exam window.",
                "The system currently uses local encrypted file storage rather than hardened cloud object storage.",
            ]
        )
    )

    append_main_heading(story, "12. Future Enhancements")
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

    append_main_heading(story, "13. Conclusion")
    story.extend(
        section_paragraphs(
            [
                f"SecuExam is implemented as a complete secure exam paper distribution system within the scope of the software engineering lab. The system covers the required secure-delivery lifecycle from upload through timed release and traceable download. The public project repository for review is available at {REPO_URL}.",
            ]
        )
    )

    story.append(PageBreak())
    append_main_heading(story, "Appendix A. Code Appendix")
    story.append(
        p(
            "This appendix contains code extracts from the implemented SecuExam project. These excerpts are taken from the actual files in the current workspace and document the most relevant backend, frontend, and testing logic.",
        )
    )
    code_sections = [
        (
            "A.1 Backend authentication logic (`server.py`)",
            build_code_block(BASE_DIR / "server.py", '@app.route("/api/login", methods=["POST"])', '@app.route("/api/logout", methods=["POST"])', max_lines=34),
        ),
        (
            "A.2 Backend secure upload logic (`server.py`)",
            build_code_block(BASE_DIR / "server.py", '@app.route("/api/papers/upload", methods=["POST"])', "# Routes — Paper Listing & Download (Receiver)", max_lines=42),
        ),
        (
            "A.3 Backend secure download logic (`server.py`)",
            build_code_block(BASE_DIR / "server.py", '@app.route("/api/papers/<paper_id>/download", methods=["GET"])', "def _log_access", max_lines=42),
        ),
        (
            "A.4 Setter upload UI logic (`secuexam_app/setter.html`)",
            build_code_block(BASE_DIR / "secuexam_app" / "setter.html", "async function handleUpload(e)", "async function loadPapers()", max_lines=34),
        ),
        (
            "A.5 Selenium test logic (`test_secuexam.py`)",
            build_code_block(BASE_DIR / "test_secuexam.py", "def login_as(self, role, creds):", "def logout(self):", max_lines=34),
        ),
    ]
    for title, code in code_sections:
        append_sub_heading(story, title)
        story.append(Preformatted(code, ParagraphStyle("code", fontName="Courier", fontSize=9, leading=12)))
        story.append(spacer(0.1))

    story.append(PageBreak())
    append_main_heading(story, "Appendix B. Screenshot of the Developed System")
    for suffix, caption in SCREENSHOT_SUFFIXES:
        append_sub_heading(story, caption)
        story.append(KeepTogether([fit_image(latest_screenshot(suffix), 16.8, 10.2), p(caption, "caption")]))
        story.append(spacer(0.15))

    if manual_shots:
        story.append(PageBreak())
        append_main_heading(story, "Appendix C. VS Code and Running App Screenshots")
        for image_path, caption in manual_shots:
            append_sub_heading(story, image_path.name)
            story.append(KeepTogether([fit_image(image_path, 17.0, 11.5), p(caption, "caption")]))
            story.append(spacer(0.15))

    story.append(PageBreak())
    appendix_letter = "D" if manual_shots else "C"
    append_main_heading(story, f"Appendix {appendix_letter}. SecuExam Diagram Pages from Previous Assignments")
    story.append(
        p(
            "These pages are direct image extracts from the previous SecuExam assignment PDFs. They are included only to preserve the completed SecuExam UML and design artefacts inside one final document.",
        )
    )
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.black))
    story.append(spacer(0.2))

    for item in DIAGRAM_PAGES:
        story.append(PageBreak())
        append_sub_heading(story, item.caption)
        story.append(fit_image(image_for_pdf_page(item.pdf_name, item.page_number), 17.0, 23.0))

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
