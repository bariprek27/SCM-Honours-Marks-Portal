"""
Comprehensive Unit and Integration Tests for SCM Honours Track - Marks Portal
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import (
    app,
    find_seat_number_column,
    normalize_header,
    read_student_marks,
)


class TestMarksPortal(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_normalize_header(self):
        self.assertEqual(normalize_header("Seat_Number"), "seatnumber")
        self.assertEqual(normalize_header("Seat Number"), "seatnumber")
        self.assertEqual(normalize_header("seat_number"), "seatnumber")
        self.assertEqual(normalize_header("SeatNo"), "seatno")
        self.assertEqual(normalize_header("Seat_No"), "seatno")
        self.assertEqual(normalize_header("  SEAT-NO  "), "seatno")

    def test_find_seat_number_column(self):
        headers_1 = ["Seat_Number", "DBMS", "Python"]
        self.assertEqual(find_seat_number_column(headers_1), 0)

        headers_2 = ["Roll_No", "Seat No", "SCM"]
        self.assertEqual(find_seat_number_column(headers_2), 1)

        headers_3 = ["Subject 1", "Subject 2"]
        with self.assertRaises(ValueError):
            find_seat_number_column(headers_3)

    def test_get_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SCM Honours Track", response.data)
        self.assertIn(b"Check Your Marks", response.data)

    def test_get_admin_page(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Marks Data Management", response.data)
        # Verify no file upload input exists on the admin page
        self.assertNotIn(b'type="file"', response.data)

    def test_search_valid_student(self):
        response = self.client.post(
            "/api/student/marks",
            data=json.dumps({"seat_number": "SCM002"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # Check required fields
        self.assertEqual(data["seat_number"], "SCM002")
        self.assertIn("marks", data)
        self.assertEqual(data["marks"]["Database Systems"], "78")
        self.assertEqual(data["marks"]["Python"], "82")
        self.assertEqual(data["marks"]["Data Analytics"], "75")
        self.assertEqual(data["marks"]["SCM Honours"], "89")

        # Check total marks calculation (78 + 82 + 75 + 89 = 324)
        self.assertEqual(data["total_marks"], 324)
        self.assertEqual(data["max_total_marks"], 400)
        self.assertEqual(data["percentage"], 81.0)

        # SECURITY TEST: Ensure no other student's data is exposed
        raw_text = response.get_data(as_text=True)
        self.assertNotIn("SCM001", raw_text)
        self.assertNotIn("SCM003", raw_text)
        self.assertNotIn("SCM004", raw_text)

    def test_search_case_insensitivity_and_trimming(self):
        # Lowercase search with spaces
        response = self.client.post(
            "/api/student/marks",
            data=json.dumps({"seat_number": "  scm001  "}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["seat_number"], "SCM001")
        self.assertEqual(data["marks"]["Python"], "91")

    def test_search_not_found(self):
        response = self.client.post(
            "/api/student/marks",
            data=json.dumps({"seat_number": "SCM999"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["error"], "Seat Number Not Found")
        self.assertEqual(data["message"], "Please check your seat number and try again.")
        # Ensure it does not leak any valid seat numbers
        self.assertNotIn("SCM001", json.dumps(data))

    def test_invalid_request_missing_seat(self):
        response = self.client.post(
            "/api/student/marks",
            data=json.dumps({"seat_number": "   "}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid Request")

    def test_invalid_request_no_json(self):
        response = self.client.post(
            "/api/student/marks",
            data="not-a-json",
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, 400)

    @patch("app.CSV_PATH", Path("non_existent_data.csv"))
    def test_missing_csv_file_error(self):
        response = self.client.post(
            "/api/student/marks",
            data=json.dumps({"seat_number": "SCM001"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data["error"], "Marks Unavailable")
        self.assertIn("Marks are currently unavailable", data["message"])
        # Ensure no traceback or server paths are exposed
        self.assertNotIn("Traceback", json.dumps(data))
        self.assertNotIn("non_existent_data.csv", json.dumps(data))

    def test_custom_csv_with_leading_zeros_and_varied_headers(self):
        csv_content = (
            "seat_no,Advanced AI,Robotics\n"
            "00123,95,90\n"
            "00456,88,84\n"
        )
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8", suffix=".csv") as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        try:
            with patch("app.CSV_PATH", tmp_path):
                # Search 00123 preserving leading zeros
                res = self.client.post(
                    "/api/student/marks",
                    data=json.dumps({"seat_number": "00123"}),
                    content_type="application/json",
                )
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["seat_number"], "00123")
                self.assertEqual(data["marks"]["Advanced AI"], "95")
                self.assertEqual(data["marks"]["Robotics"], "90")
                self.assertEqual(data["total_marks"], 185)
                self.assertEqual(data["percentage"], 92.5)

                # Searching without leading zeros should not match 00123
                res_no_zeros = self.client.post(
                    "/api/student/marks",
                    data=json.dumps({"seat_number": "123"}),
                    content_type="application/json",
                )
                self.assertEqual(res_no_zeros.status_code, 404)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_non_numeric_marks(self):
        csv_content = (
            "Seat_Number,Project Viva,Internship\n"
            "SCM099,A+,Pass\n"
        )
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8", suffix=".csv") as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        try:
            with patch("app.CSV_PATH", tmp_path):
                res = self.client.post(
                    "/api/student/marks",
                    data=json.dumps({"seat_number": "SCM099"}),
                    content_type="application/json",
                )
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["seat_number"], "SCM099")
                self.assertEqual(data["marks"]["Project Viva"], "A+")
                self.assertEqual(data["marks"]["Internship"], "Pass")
                self.assertIsNone(data["total_marks"])
                self.assertIsNone(data["percentage"])
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_empty_csv_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8", suffix=".csv") as tmp:
            tmp.write("")
            tmp_path = Path(tmp.name)

        try:
            with patch("app.CSV_PATH", tmp_path):
                res = self.client.post(
                    "/api/student/marks",
                    data=json.dumps({"seat_number": "SCM001"}),
                    content_type="application/json",
                )
                self.assertEqual(res.status_code, 500)
                data = res.get_json()
                self.assertEqual(data["error"], "Marks Unavailable")
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
