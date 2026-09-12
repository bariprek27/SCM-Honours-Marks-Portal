# SCM Honours Track - Marks Portal

A clean, responsive, and privacy-conscious web application designed for students to securely check their **SCM Honours Track** examination marks using their **Seat Number**.

Built specifically for deployment on **Vercel** with a zero-database architecture.

---

## 📌 Project Overview

The **SCM Honours Track Marks Portal** provides an intuitive interface for students to retrieve their official course marks. 

### Key Architectural Highlights:
* **No Database**: Does not require MySQL, PostgreSQL, MongoDB, or SQLite.
* **No Persistent File Uploads**: Eliminates file system write vulnerabilities and maintenance costs.
* **CSV-Driven**: Exam records are loaded server-side from `data/marks.csv`.
* **Privacy by Design**: The complete marks dataset is **never** sent to the client. The Flask backend queries the dataset server-side and transmits *only* the matching student's record.
* **Dynamic Header & Subject Detection**: Automatically identifies the seat number column (supports `Seat_Number`, `Seat Number`, `seat_no`, etc.) and dynamically renders any number of subject columns without hardcoded subject names.
* **Automatic Theme Adaptation**: Seamlessly respects the user's operating system and browser light or dark mode preferences in real-time.
* **Print Ready**: Students can print their official marksheet or save it as a clean PDF using the built-in print style.

---

## 🛠 Technology Stack

* **Frontend**: HTML5, CSS3 (Vanilla CSS with CSS Custom Properties and `@media (prefers-color-scheme)`), Vanilla JavaScript
* **Backend**: Python 3, Flask
* **Data Layer**: Bundled CSV (`data/marks.csv`)
* **Deployment Platform**: Vercel (Python Runtime)

---

## 📂 Project Structure

```text
scm-marks-portal/
│
├── app.py                 # Flask application entry point with CSV lookup & API
├── vercel.json            # Vercel deployment routing and runtime configuration
├── requirements.txt       # Minimal dependencies (Flask)
├── sample_marks.csv       # Sample template reference for administrators
├── .gitignore             # Git ignore configuration (ensures data/marks.csv is tracked)
├── README.md              # Project documentation and viva guide
│
├── data/
│   └── marks.csv          # Active marks dataset deployed with the application
│
├── templates/
│   ├── index.html         # Main student portal interface
│   └── admin.html         # Marks data management guide (no upload, no marks exposure)
│
├── static/
│   ├── css/
│   │   └── style.css      # Design system with responsive layout and dark mode
│   └── js/
│       └── script.js      # Form handling, fetch API client, and dynamic rendering
│
└── tests/
    └── test_app.py        # Automated test suite (security, headers, calculations)
```

---

## 🚀 Local Setup & Running

### Prerequisites
* Python 3.9+ installed on your computer.

### 1. Clone or Open the Repository
```bash
cd "f:\00Preksha\001 SCM marks portal"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Flask Development Server
```bash
python app.py
```

### 4. Open in Browser
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) to view the portal.
Visit [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin) to view the administrator guide.

### 5. Run Automated Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📊 CSV Format Specification

The application reads marks from `data/marks.csv`.

### Example Format:
```csv
Seat_Number,Database Systems,Python,Data Analytics,SCM Honours
SCM001,85,91,88,94
SCM002,78,82,75,89
SCM003,92,87,90,95
SCM004,81,86,84,91
```

### Guidelines:
1. **Seat Number Column**: Must include a column identifying seat numbers. The system automatically normalizes and recognizes:
   * `Seat_Number` *(preferred)*
   * `Seat Number`
   * `seat_number`
   * `SeatNo`
   * `Seat_No`
   * `seat_no`
2. **Subject Columns**: All columns other than the seat number column are treated as subject marks. Subject names are detected dynamically and displayed verbatim.
3. **Numeric Marks & Calculations**: If all subject marks for a student are numeric, the application automatically computes:
   * **Total Marks** (Sum of subject scores)
   * **Percentage** (Based on 100 max marks per subject)
4. **Non-numeric Values**: If grades (`A+`, `Pass`, `Absent`) are present, they are safely displayed in the marks table while suppressing calculated numeric totals.

---

## 🔄 Marks Update Workflow

To update student marks, administrators follow this simple, secure workflow:

```text
Admin receives new marks CSV
            ↓
Verify 'Seat_Number' column exists
            ↓
Replace data/marks.csv
            ↓
Test locally with: python app.py
            ↓
Commit & Push to Git:
git add data/marks.csv
git commit -m "Update SCM Honours marks"
git push origin main
            ↓
Vercel automatically detects push & redeploys
            ↓
New marks are live for students!
```

> **Important**: This architecture deliberately prevents web-based file uploads on the deployed site. This eliminates any risk of arbitrary file execution or unauthorized data modification.

---

## 🌐 Vercel Deployment Guide

### Option 1: Deploy via GitHub (Recommended)
1. Initialize Git in the project directory:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of SCM Marks Portal"
   ```
2. Push your project to a new repository on GitHub.
3. Go to [vercel.com](https://vercel.com) and log in.
4. Click **"Add New Project"** and select your GitHub repository.
5. Vercel automatically detects `vercel.json` and configures the Python runtime.
6. Click **Deploy**. Your application will be live at `https://your-project.vercel.app`.

### Option 2: Deploy via Vercel CLI
1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. Run deployment command in the project root:
   ```bash
   vercel
   ```
3. Follow the CLI prompts to deploy. For production:
   ```bash
   vercel --prod
   ```

---

## 🌓 Theme & Aesthetic System

* **Automatic System Following**: The portal uses `@media (prefers-color-scheme: dark)` and the JavaScript `matchMedia` API. When a student's operating system or browser switches between Light and Dark mode, the portal updates instantly without reloading.
* **Light Palette**: Clean academic aesthetic with off-white background (`#f8fafc`), crisp white cards (`#ffffff`), slate typography, and university navy blue accents (`#1d4ed8`).
* **Dark Palette**: Deep midnight slate background (`#0b0f19`), elevated dark cards (`#1e293b`), soft borders (`#334155`), and high-legibility light text (`#f8fafc`).
* **Typography**: Professional, high-readability Google Font **Inter**.

---

## 🔒 Privacy & Security Guarantee

1. **Exact Lookup Only**: The endpoint `POST /api/student/marks` searches `data/marks.csv` server-side and responds **only** with the matching student's record.
2. **No Full CSV Exposure**: The CSV file is never sent to the browser or embedded into client-side JavaScript.
3. **No Student Rosters**: No student lists, dropdowns, rankings, or other students' marks are ever returned.
4. **No Server Path or Traceback Leaks**: Server-side error handlers capture exceptions and return clean, user-friendly JSON error messages (e.g. `404 Seat Number Not Found` or `500 Marks Unavailable`) without leaking internal paths or stack traces.

---

## 🎓 College Viva / Project Presentation Points

When presenting this project in a viva or evaluation, highlight these design decisions:
1. **Why No Database?**
   * *Examination marks are static snapshots for a given semester.* A database adds unnecessary server costs, connection pool management, and security risks. Bundling a CSV inside a serverless Vercel function provides instant sub-100ms response times with zero maintenance.
2. **Why No Web Admin Upload?**
   * Serverless platforms like Vercel run on ephemeral, read-only file systems. Files uploaded via HTTP are lost when serverless instances spin down. By coupling data updates to Git commits, the application retains a complete audit trail (version history) of all mark changes.
3. **Dynamic Flexibility**:
   * Any change in subjects or subject count in `data/marks.csv` automatically reflects in the frontend table without modifying a single line of code.
