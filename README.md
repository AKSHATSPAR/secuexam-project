# SecuExam

Secure exam paper distribution system built with Flask, SQLite, and a static HTML/CSS/JS frontend.

## What is included

- Role-based flows for `setter`, `receiver`, and `admin`
- AES-256 encryption with Shamir-style key splitting
- Server-side time-lock enforcement
- Dynamic PDF watermarking on receiver download
- Admin analytics, approval, audit logs, and paper visibility
- Selenium end-to-end test suite

## Project structure

- `server.py`: Flask backend and database logic
- `secuexam_app/`: frontend pages, CSS, JS, and encrypted upload storage
- `test_secuexam.py`: Selenium test suite
- `reset_demo_state.py`: cleanup/reset utility for generated local state
- `generate_final_report.py`: generator for the final SecuExam documentation PDF
- `SecuExam_Final_Project_Report.pdf`: generated final project report

## Local setup

```bash
cd /Users/akshat/SOFTWARE_COURSE_BASED\ PROJECT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Chrome or Safari WebDriver support is required for the Selenium suite.

## Run the app

```bash
cd /Users/akshat/SOFTWARE_COURSE_BASED\ PROJECT
source venv/bin/activate
python server.py
```

Default URL: `http://127.0.0.1:5050`

## Demo accounts

- `admin@secuexam.in` / `admin123`
- `setter@vit.ac.in` / `setter123`
- `receiver@vit.ac.in` / `receiver123`

## Reset generated state

Use this if you want to clear the local DB, uploaded encrypted files, screenshots, and caches, then restore the default seeded users.

```bash
cd /Users/akshat/SOFTWARE_COURSE_BASED\ PROJECT
source venv/bin/activate
python reset_demo_state.py
```

Useful variants:

```bash
python reset_demo_state.py --dry-run
python reset_demo_state.py --keep-screenshots
```

Stop the running Flask server before performing a real reset.

## Run tests

```bash
cd /Users/akshat/SOFTWARE_COURSE_BASED\ PROJECT
source venv/bin/activate
python test_secuexam.py
```

Current verified result in this workspace: `34/34 tests passed`.

## Final report

The final project documentation PDF is available at:

```bash
/Users/akshat/SOFTWARE_COURSE_BASED PROJECT/SecuExam_Final_Project_Report.pdf
```

To regenerate it:

```bash
cd /Users/akshat/SOFTWARE_COURSE_BASED\ PROJECT
source venv/bin/activate
python generate_final_report.py
```
