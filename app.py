"""
SCM Honours Track - Marks Portal
Backend Flask Application
"""

import csv
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, render_template, request

# Base paths for local and Vercel serverless environments
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "marks.csv"

# Configuration for marks calculation (default 100 marks per subject)
# Set to None if maximum marks should not be assumed
DEFAULT_MAX_MARKS_PER_SUBJECT: Optional[int] = 30

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_header(header: str) -> str:
    """
    Normalize column header string by stripping whitespace,
    removing delimiters, and converting to lowercase.
    Example: 'Seat_Number' -> 'seatnumber', 'Seat No' -> 'seatno'
    """
    return re.sub(r"[\s_\-#]+", "", header.strip().lower())


def find_seat_number_column(headers: List[str]) -> int:
    """
    Find the index of the seat number column in the CSV header row.
    Supports variations: Seat_Number, Seat Number, seat_number, SeatNo, Seat_No, etc.
    """
    recognized_names = {"seatnumber", "seatno", "seatnum", "seat"}
    for idx, header in enumerate(headers):
        normalized = normalize_header(header)
        if normalized in recognized_names:
            return idx
    raise ValueError("Seat number column not found in marks data header.")


def read_student_marks(seat_number_query: str) -> Optional[Dict[str, Any]]:
    """
    Search data/marks.csv for the student seat number.
    Returns only the matching student's data or None if not found.
    Does NOT leak other students' records or the full CSV.
    """
    if not CSV_PATH.exists():
        logger.error(f"Marks file not found at {CSV_PATH}")
        raise FileNotFoundError("Marks data file is missing.")

    trimmed_query = seat_number_query.strip()
    if not trimmed_query:
        return None

    # Open with utf-8-sig to automatically handle any UTF-8 BOM
    with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        # Retrieve headers
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError("Marks data file is empty.")

        # Clean headers
        headers = [h.strip() for h in headers]
        if not headers or all(not h for h in headers):
            raise ValueError("Marks data file contains no valid headers.")

        # Identify the seat number column
        seat_col_idx = find_seat_number_column(headers)

        # Dynamic subjects: all other columns
        subject_cols: List[Tuple[str, int]] = [
            (header, idx) for idx, header in enumerate(headers) if idx != seat_col_idx and header
        ]

        if not subject_cols:
            raise ValueError("No subject columns detected in marks data.")

        # Search for exact seat number (case-insensitive, trimmed)
        for row in reader:
            if not row or len(row) <= seat_col_idx:
                continue

            row_seat = row[seat_col_idx].strip()
            # Perform exact lookup while being case-tolerant
            if row_seat.lower() == trimmed_query.lower():
                actual_seat_number = row_seat
                marks: Dict[str, Any] = {}
                numeric_marks: List[float] = []
                all_numeric = True

                for subject_name, col_idx in subject_cols:
                    val = row[col_idx].strip() if col_idx < len(row) else ""
                    marks[subject_name] = val

                    # Check if numeric
                    if val != "":
                        try:
                            num = float(val)
                            # Convert integer floats like 85.0 to 85
                            if num.is_integer():
                                num = int(num)
                            numeric_marks.append(num)
                        except ValueError:
                            all_numeric = False
                    else:
                        all_numeric = False

                total_marks = None
                max_total_marks = None
                percentage = None

                # Calculate total and percentage if all subject values are numeric
                if all_numeric and len(numeric_marks) == len(subject_cols):
                    sum_val = sum(numeric_marks)
                    total_marks = int(sum_val) if isinstance(sum_val, (int, float)) and float(sum_val).is_integer() else round(sum_val, 2)

                    if DEFAULT_MAX_MARKS_PER_SUBJECT is not None and DEFAULT_MAX_MARKS_PER_SUBJECT > 0:
                        max_total_marks = len(subject_cols) * DEFAULT_MAX_MARKS_PER_SUBJECT
                        percentage = round((float(total_marks) / float(max_total_marks)) * 100.0, 2)

                return {
                    "seat_number": actual_seat_number,
                    "marks": marks,
                    "total_marks": total_marks,
                    "max_total_marks": max_total_marks,
                    "percentage": percentage,
                }

    return None


@app.route("/", methods=["GET"])
def index():
    """Render student portal homepage."""
    return render_template("index.html")


@app.route("/admin", methods=["GET"])
def admin_info():
    """
    Render administrative information page.
    Explains the redeployment workflow without web upload or exposing data.
    """
    return render_template("admin.html")


@app.route("/api/student/marks", methods=["POST"])
def get_student_marks():
    """
    Search student marks by Seat Number.
    Returns only the matching student's marks.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "error": "Invalid Request",
            "message": "Please provide a valid JSON payload."
        }), 400

    seat_number = data.get("seat_number")
    if not seat_number or not isinstance(seat_number, str) or not seat_number.strip():
        return jsonify({
            "error": "Invalid Request",
            "message": "Please enter a valid seat number."
        }), 400

    try:
        student_data = read_student_marks(seat_number)
    except FileNotFoundError:
        return jsonify({
            "error": "Marks Unavailable",
            "message": "Marks are currently unavailable. Please try again later."
        }), 500
    except ValueError as ve:
        logger.error(f"Data configuration error: {ve}")
        return jsonify({
            "error": "Marks Unavailable",
            "message": "Marks are currently unavailable. Please try again later."
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error querying marks: {e}")
        return jsonify({
            "error": "Server Error",
            "message": "Unable to retrieve marks right now. Please try again later."
        }), 500

    if not student_data:
        return jsonify({
            "error": "Seat Number Not Found",
            "message": "Please check your seat number and try again."
        }), 404

    # Return strictly the requested student's data
    return jsonify(student_data), 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        "error": "Server Error",
        "message": "An internal server error occurred. Please try again later."
    }), 500


if __name__ == "__main__":
    # Local development server
    app.run(host="127.0.0.1", port=5000, debug=True)
