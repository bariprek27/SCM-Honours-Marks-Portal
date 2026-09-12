/**
 * SCM Honours Track - Marks Portal
 * Frontend Application Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const marksForm = document.getElementById('marks-form');
  const seatInput = document.getElementById('seat-number-input');
  const clearBtn = document.getElementById('clear-input-btn');
  const submitBtn = document.getElementById('submit-btn');
  const btnText = submitBtn.querySelector('.btn-text');
  const spinner = submitBtn.querySelector('.spinner');

  const searchSection = document.getElementById('search-section');
  const resultsSection = document.getElementById('results-section');
  const errorBanner = document.getElementById('error-banner');
  const errorTitle = document.getElementById('error-title');
  const errorMessage = document.getElementById('error-message');
  const liveAnnouncer = document.getElementById('live-announcer');

  const displaySeatNumber = document.getElementById('display-seat-number');
  const marksTableBody = document.getElementById('marks-table-body');
  const marksSummary = document.getElementById('marks-summary');
  const displayTotalMarks = document.getElementById('display-total-marks');
  const displayPercentage = document.getElementById('display-percentage');

  const searchAgainBtn = document.getElementById('search-again-btn');
  const printResultBtn = document.getElementById('print-result-btn');

  // Input Clear Button Toggle
  seatInput.addEventListener('input', () => {
    clearBtn.style.display = seatInput.value.trim().length > 0 ? 'flex' : 'none';
    hideError();
  });

  clearBtn.addEventListener('click', () => {
    seatInput.value = '';
    clearBtn.style.display = 'none';
    seatInput.focus();
    hideError();
  });

  // Announce messages to screen readers
  function announce(message) {
    if (liveAnnouncer) {
      liveAnnouncer.textContent = message;
    }
  }

  // Display Error Banner
  function showError(title, message) {
    errorTitle.textContent = title || 'Error';
    errorMessage.textContent = message || 'An error occurred. Please try again.';
    errorBanner.style.display = 'flex';
    announce(`${title}: ${message}`);
  }

  // Hide Error Banner
  function hideError() {
    errorBanner.style.display = 'none';
  }

  // Set Loading State
  function setLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      btnText.textContent = 'Checking your marks...';
      spinner.style.display = 'inline-block';
      hideError();
    } else {
      submitBtn.disabled = false;
      btnText.textContent = 'View Marks';
      spinner.style.display = 'none';
    }
  }

  // Form Submit Handler
  marksForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const rawSeatNumber = seatInput.value;
    const seatNumber = rawSeatNumber.trim();

    if (!seatNumber) {
      showError('Seat Number Required', 'Please enter your seat number to view marks.');
      seatInput.focus();
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/student/marks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ seat_number: seatNumber })
      });

      const data = await response.json();

      if (response.ok && data.seat_number) {
        // Success: Render Student Marks
        renderResults(data);
      } else if (response.status === 404) {
        showError('Seat Number Not Found', data.message || 'Please check your seat number and try again.');
        seatInput.focus();
      } else if (response.status === 400) {
        showError('Invalid Request', data.message || 'Please enter a valid seat number.');
        seatInput.focus();
      } else {
        // 500 or other server errors
        showError('Marks Unavailable', data.message || 'Unable to retrieve marks right now. Please try again later.');
      }
    } catch (err) {
      console.error('Fetch error:', err);
      showError('Connection Error', 'Unable to reach the marks server. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  });

  // Render Result Function
  function renderResults(studentData) {
    // Set Verified Seat Number
    displaySeatNumber.textContent = studentData.seat_number;

    // Clear Previous Table Rows
    marksTableBody.innerHTML = '';

    const marksObj = studentData.marks || {};
    const subjects = Object.keys(marksObj);

    subjects.forEach((subject) => {
      const tr = document.createElement('tr');

      const tdSubject = document.createElement('td');
      tdSubject.className = 'subject-name';
      tdSubject.textContent = subject;

      const tdMark = document.createElement('td');
      tdMark.className = 'mark-value text-right';
      tdMark.textContent = marksObj[subject] !== '' ? marksObj[subject] : '—';

      tr.appendChild(tdSubject);
      tr.appendChild(tdMark);
      marksTableBody.appendChild(tr);
    });

    // Handle Total & Percentage
    if (studentData.total_marks !== null && studentData.total_marks !== undefined) {
      marksSummary.style.display = 'grid';

      if (studentData.max_total_marks) {
        displayTotalMarks.textContent = `${studentData.total_marks} / ${studentData.max_total_marks}`;
      } else {
        displayTotalMarks.textContent = studentData.total_marks;
      }

      if (studentData.percentage !== null && studentData.percentage !== undefined) {
        displayPercentage.textContent = `${studentData.percentage}%`;
      } else {
        document.getElementById('percentage-card').style.display = 'none';
      }
    } else {
      marksSummary.style.display = 'none';
    }

    // Switch View
    searchSection.style.display = 'none';
    resultsSection.style.display = 'block';

    // Announce to Screen Reader & Scroll smoothly
    announce(`Marks for seat number ${studentData.seat_number} loaded successfully.`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Search Another Seat Number
  searchAgainBtn.addEventListener('click', () => {
    resultsSection.style.display = 'none';
    searchSection.style.display = 'block';
    hideError();
    seatInput.value = '';
    clearBtn.style.display = 'none';
    seatInput.focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // Print Marks / Save PDF
  printResultBtn.addEventListener('click', () => {
    window.print();
  });

  // Dynamic Theme Listener for System/Browser Theme Changes
  if (window.matchMedia) {
    const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    colorSchemeQuery.addEventListener('change', (e) => {
      // The CSS @media (prefers-color-scheme: dark) updates automatically.
      // This listener ensures any JS-rendered canvas or dynamic elements respond in real time.
      const newTheme = e.matches ? 'dark' : 'light';
      console.log(`System color scheme dynamically switched to: ${newTheme}`);
    });
  }
});
