# Dashboard Testing Guide

## End-to-End Workflow Testing

### Prerequisites

1. **Backend Running**: FastAPI backend must be running on `http://localhost:8000`
2. **Database Seeded**: Run the mock data seeding script:
   ```bash
   cd /path/to/vocabulator
   python scripts/seed_mock_dashboard_data.py
   ```
3. **Dashboard Running**: Start the dashboard dev server:
   ```bash
   cd dashboard
   npm run dev
   ```

### Test Workflow

#### 1. Teacher Dashboard View

1. **Navigate to Dashboard**
   - Open `http://localhost:5173` (or the port shown in terminal)
   - Verify header shows "Vocabulator Dashboard"
   - Verify dropdown shows "Teacher View" as first option

2. **Sync with Google Classroom**
   - Click "Sync with Google Classroom" button
   - Verify success message appears
   - Verify student list populates with 18 mock students (STU-001 to STU-018)
   - Verify students are distributed across 3 classes (7A-ELA, 7B-ELA, 8A-ELA)

3. **Filter by Class**
   - Select a class from the "Filter by Class" dropdown
   - Verify only students from that class are shown
   - Select "All Classes" and verify all students appear

4. **View Student Details**
   - Click "View Details" button for any student
   - Verify page switches to student detail view
   - Verify "Back to Dashboard" button appears

#### 2. Student Detail View

1. **Student Profile Display**
   - Verify StudentStats component shows:
     - Student ID (format: STU-###)
     - Grade level (7 or 8)
     - Vocabulary size (number of words)
     - Proficiency score (0-100)

2. **Vocabulary Growth Chart**
   - Verify chart displays (may be empty if no assignments submitted)
   - Chart should show "Last 30 Days" in header
   - If assignments exist, verify data points appear

3. **Recommendations List**
   - Verify recommendations display (may be empty initially)
   - If recommendations exist:
     - Verify word, definition, and difficulty score display
     - Click "Show Details" to expand rationale and examples
     - Click "Hide Details" to collapse

4. **Assignment Submission**
   - Verify AssignmentSelector component displays mock assignments
   - Select one or more assignments using checkboxes
   - Click "Submit Selected Assignments"
   - Verify success message appears
   - Verify student data refreshes (vocabulary size may increase)
   - Verify chart updates if assignments have dates

#### 3. View Switching

1. **Header Dropdown**
   - Use header dropdown to switch between:
     - Teacher View
     - Individual student views (STU-001, STU-002, etc.)
   - Verify view changes correctly
   - Verify data loads for selected student

2. **Navigation**
   - From student view, click "Back to Dashboard"
   - Verify returns to teacher view
   - Verify student list still shows filtered students

### Error Scenarios

#### 1. Backend Not Running

1. Stop the FastAPI backend
2. Try to sync with Google Classroom
3. Verify error message appears
4. Verify error message is user-friendly (not exposing technical details)

#### 2. Invalid Student ID

1. Manually navigate to a non-existent student ID
2. Verify error handling (should show error message or redirect)

#### 3. Network Errors

1. Disconnect network
2. Try to submit assignments
3. Verify error message appears
4. Verify error message is appropriate for production

### Browser Compatibility

Test in the following browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

### Responsive Design Testing

See `RESPONSIVE_TESTING.md` for detailed responsive design test cases.

## Known Limitations

1. **Mock Data**: Uses mock assignments from JSON files (not real API data)
2. **Authentication**: Not implemented (demo/mock only)
3. **CSRF Protection**: Not implemented (demo/mock only)
4. **Assignment History**: Chart uses simulated data, not real historical data

## Troubleshooting

### Students Not Loading

- Check backend is running: `curl http://localhost:8000/health`
- Check CORS configuration in backend
- Check browser console for errors
- Verify `VITE_API_BASE` is set correctly

### Chart Not Displaying

- Check browser console for Chart.js errors
- Verify assignments have valid date fields
- Check that Chart.js is loaded (should be in dependencies)

### API Errors

- Check browser Network tab for failed requests
- Verify request IDs are being sent (check `X-Request-ID` header)
- Check backend logs for error details

