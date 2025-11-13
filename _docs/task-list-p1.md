# Dashboard Implementation Task List

## Project Overview

Build a minimalist teacher/student vocabulary dashboard using Svelte, Bootstrap 5, and Chart.js. The dashboard demonstrates core P1 PRD functionality with mock data integration to show Google Classroom sync capabilities without actual platform integration.

## Technology Stack

- Frontend Framework: Svelte with SvelteKit
- UI Framework: Bootstrap 5
- Charts: Chart.js
- API Communication: Fetch API with utility wrapper
- Deployment: Vercel
- Backend: Existing FastAPI (no changes required)
- Data: Frontend JSON mocks + backend seeding script

## Implementation Tasks

### Phase 1: Project Setup

#### Task 1.1: Initialize SvelteKit Project
**Objective:** Create new SvelteKit project with required dependencies

**Steps:**
1. Run SvelteKit initialization
2. Install dependencies:
   - Bootstrap 5
   - Chart.js
   - Bootstrap Icons (optional)
3. Configure Vercel deployment settings
4. Set up project structure

**File Structure:**
```
dashboard/
├── src/
│   ├── routes/
│   │   └── +page.svelte          # Main dashboard page
│   ├── lib/
│   │   ├── components/           # Reusable components
│   │   ├── stores.js             # Svelte stores for state
│   │   ├── api.js                # API utility functions
│   │   └── utils.js              # Helper functions
│   ├── data/
│   │   ├── mockEducator.json     # Teacher data
│   │   ├── mockAssignments.json  # Assignment templates
│   │   └── mockClasses.json      # Class information
│   └── app.html                  # HTML template
├── static/                       # Static assets
└── vercel.json                   # Vercel config
```

**Acceptance Criteria:**
- SvelteKit dev server runs successfully
- Bootstrap CSS loads correctly
- Project builds without errors
- Basic routing works

**Dependencies:**
- Node.js 18+
- npm or pnpm

---

#### Task 1.2: Create Mock Data Files
**Objective:** Create JSON files with mock educator, class, and assignment data

**Files to Create:**

**src/data/mockEducator.json:**
```json
{
  "id": "TEACHER-001",
  "name": "Ms. Johnson",
  "email": "mjohnson@school.edu",
  "classes": ["7A-ELA", "7B-ELA", "8A-ELA"]
}
```

**src/data/mockClasses.json:**
```json
[
  {
    "id": "7A-ELA",
    "name": "Grade 7A - English Language Arts",
    "grade": 7,
    "period": "Period 2"
  },
  {
    "id": "7B-ELA",
    "name": "Grade 7B - English Language Arts",
    "grade": 7,
    "period": "Period 4"
  },
  {
    "id": "8A-ELA",
    "name": "Grade 8A - English Language Arts",
    "grade": 8,
    "period": "Period 3"
  }
]
```

**src/data/mockAssignments.json:**
```json
[
  {
    "id": "ASSIGN-001",
    "title": "Persuasive Essay - Renewable Energy",
    "text": "In this essay, I will argue that renewable energy is essential for our future. First, fossil fuels contribute to climate change by releasing carbon dioxide into the atmosphere. Scientists have demonstrated that increased CO2 levels correlate with rising global temperatures...",
    "date": "2025-11-10",
    "type": "writing"
  },
  {
    "id": "ASSIGN-002",
    "title": "Science Discussion - Photosynthesis",
    "text": "Today we discussed photosynthesis and how plants convert sunlight into energy using chlorophyll in their chloroplasts. The process requires water, carbon dioxide, and light energy to produce glucose and oxygen...",
    "date": "2025-11-11",
    "type": "transcript"
  },
  {
    "id": "ASSIGN-003",
    "title": "Book Report - To Kill a Mockingbird",
    "text": "Harper Lee's novel explores themes of prejudice, justice, and moral complexity in the American South. The protagonist, Scout Finch, observes her father defending an innocent man accused of a crime he didn't commit...",
    "date": "2025-11-12",
    "type": "writing"
  }
]
```

**Acceptance Criteria:**
- JSON files are valid and parse correctly
- Data structure matches API response format from existing backend
- Mock assignments contain realistic middle-school vocabulary
- Assignments span multiple dates for chart testing

---

#### Task 1.3: Create API Utility Module
**Objective:** Build simple fetch wrapper for backend API communication

**File to Create:** src/lib/api.js

**Required Functions:**
```javascript
// Get all students (with optional grade filter)
export async function getStudents(gradeLevel = null)

// Get single student profile
export async function getStudentProfile(studentId)

// Get student recommendations
export async function getStudentRecommendations(studentId)

// Mock: Sync students (calls backend to insert mock data)
export async function syncWithGoogleClassroom()

// Mock: Submit assignments (sends assignment data to backend)
export async function submitAssignments(studentId, assignments)
```

**Implementation Details:**
- Base API URL should be configurable via environment variable
- Include error handling with try/catch
- Return JSON responses
- Log errors to console for debugging
- Handle network failures gracefully

**Example Implementation:**
```javascript
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

export async function getStudents(gradeLevel = null) {
  try {
    const url = gradeLevel
      ? `${API_BASE}/students?grade_level=${gradeLevel}`
      : `${API_BASE}/students`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch students:', error);
    throw error;
  }
}
```

**Acceptance Criteria:**
- All API functions are async and return promises
- Error handling is consistent across all functions
- API base URL is configurable
- Functions match existing FastAPI endpoints
- Mock functions have clear "mock" prefix or comment

---

#### Task 1.4: Create Svelte Stores for State Management
**Objective:** Set up reactive state management using Svelte stores

**File to Create:** src/lib/stores.js

**Required Stores:**
```javascript
// Current view: 'teacher' or student ID
export const currentView = writable('teacher');

// All students data
export const students = writable([]);

// Current educator data
export const educator = writable(null);

// Available classes (derived from students)
export const classes = derived(students, $students => {
  const classSet = new Set($students.map(s => s.class));
  return Array.from(classSet);
});

// Filtered students by selected class
export const selectedClass = writable(null);
export const filteredStudents = derived(
  [students, selectedClass],
  ([$students, $selectedClass]) => {
    if (!$selectedClass) return $students;
    return $students.filter(s => s.class === $selectedClass);
  }
);

// Current student (when in student view)
export const currentStudent = derived(
  [students, currentView],
  ([$students, $currentView]) => {
    if ($currentView === 'teacher') return null;
    return $students.find(s => s.student_id === $currentView);
  }
);
```

**Acceptance Criteria:**
- Stores are properly exported
- Derived stores update reactively
- currentView defaults to 'teacher'
- Store updates trigger component re-renders

---

### Phase 2: Backend Mock Data Script

#### Task 2.1: Create Database Seeding Script
**Objective:** Python script to populate DynamoDB with mock student data

**File to Create:** scripts/seed_mock_dashboard_data.py

**Requirements:**
- Create 15-20 mock students across 3 classes (7A-ELA, 7B-ELA, 8A-ELA)
- Each student has:
  - Anonymous ID (STU-XXX format)
  - Grade level (7 or 8)
  - Class assignment
  - Vocabulary list with 50-150 words
  - Proficiency score (40-90 range)
  - Created/updated timestamps
- Students have varied proficiency levels (some low, some high)
- Use existing StudentRepository for database operations

**Script Structure:**
```python
#!/usr/bin/env python3
"""Seed mock student data for dashboard demo."""

from datetime import datetime, timezone
from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.repositories.student_repository import StudentRepository

MOCK_STUDENTS = [
    {
        "student_id": "STU-001",
        "grade_level": 7,
        "class": "7A-ELA",
        "vocab_size": 120,
        "proficiency_score": 75.5
    },
    # ... more students
]

def generate_vocabulary(size: int) -> list:
    """Generate mock vocabulary entries."""
    # Return list of VocabularyEntry objects
    pass

def seed_students():
    """Populate DynamoDB with mock students."""
    repo = StudentRepository()
    for student_data in MOCK_STUDENTS:
        # Create StudentProfile and save
        pass

if __name__ == "__main__":
    seed_students()
```

**Acceptance Criteria:**
- Script runs without errors
- Creates 15-20 students in DynamoDB
- Students are distributed across 3 classes
- Vocabulary lists contain realistic academic words
- Proficiency scores vary (demonstrate range)
- Script is idempotent (can run multiple times safely)

---

#### Task 2.2: Create Mock Assignment Submission Endpoint
**Objective:** Add backend endpoint to receive mock assignment submissions

**File to Modify:** src/api/routes/upload.py

**New Endpoint:**
```python
@router.post(
    "/mock/submit-assignment",
    response_model=WritingUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Mock assignment submission for dashboard demo"
)
async def mock_submit_assignment(
    request: WritingUploadRequest,
    pipeline: Annotated[TextProcessingPipeline, Depends(get_text_processing_pipeline)],
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)]
):
    """
    Accept assignment submission from dashboard mock.
    Identical to real upload but labeled as mock for clarity.
    """
    # Use existing upload logic
    pass
```

**Acceptance Criteria:**
- Endpoint accepts assignment data
- Processes text through existing pipeline
- Updates student vocabulary profile
- Generates new recommendations
- Returns success response with words_extracted count

---

#### Task 2.3: Create Mock Google Classroom Sync Endpoint
**Objective:** Endpoint that simulates syncing students from Google Classroom

**File to Create:** src/api/routes/mock.py

**New Endpoint:**
```python
@router.post(
    "/mock/sync-google-classroom",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Simulate Google Classroom student sync"
)
async def sync_google_classroom(
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)]
):
    """
    Simulate syncing students from Google Classroom.
    In reality, would call Google Classroom API.
    For demo, returns success with student count.
    """
    # Check if students already exist
    # If not, call seeding logic
    # Return count of students synced
    pass
```

**Acceptance Criteria:**
- Endpoint checks if mock students already exist
- Returns student count and success message
- Idempotent (safe to call multiple times)
- Response indicates whether new students were added or already existed

---

### Phase 3: Core Components

#### Task 3.1: Create Header Component
**Objective:** Build navigation header with view switcher dropdown

**File to Create:** src/lib/components/Header.svelte

**Requirements:**
- Bootstrap navbar
- App title: "Vocabulator Dashboard"
- Dropdown select for view switching:
  - "Teacher View" (value: 'teacher', always first)
  - Divider
  - List of student names (value: student_id)
- Dropdown should be styled with Bootstrap
- Current selection is highlighted

**Component Structure:**
```svelte
<script>
  import { currentView, students, educator } from '$lib/stores';

  function handleViewChange(event) {
    currentView.set(event.target.value);
  }
</script>

<nav class="navbar navbar-dark bg-primary">
  <div class="container-fluid">
    <span class="navbar-brand">Vocabulator Dashboard</span>
    <select class="form-select w-auto" on:change={handleViewChange} value={$currentView}>
      <option value="teacher">Teacher View - {$educator?.name || 'Loading...'}</option>
      <option disabled>──────────</option>
      {#each $students as student}
        <option value={student.student_id}>
          {student.student_id} - Grade {student.grade_level}
        </option>
      {/each}
    </select>
  </div>
</nav>
```

**Acceptance Criteria:**
- Header displays at top of page
- Dropdown lists teacher view first, then students
- Selecting option changes currentView store
- UI updates reactively when view changes
- Bootstrap styling applied correctly

---

#### Task 3.2: Create Student Stats Component
**Objective:** Display student profile statistics

**File to Create:** src/lib/components/StudentStats.svelte

**Requirements:**
- Display student information:
  - Student ID
  - Grade level
  - Vocabulary size
  - Proficiency score
- Bootstrap card layout
- Props: studentProfile object

**Component Structure:**
```svelte
<script>
  export let studentProfile;
</script>

<div class="card mb-3">
  <div class="card-header">
    <h5>Student Profile</h5>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-3">
        <strong>Student ID:</strong><br>
        {studentProfile.student_id}
      </div>
      <div class="col-md-3">
        <strong>Grade Level:</strong><br>
        {studentProfile.grade_level}
      </div>
      <div class="col-md-3">
        <strong>Vocabulary Size:</strong><br>
        {studentProfile.vocabulary_size} words
      </div>
      <div class="col-md-3">
        <strong>Proficiency Score:</strong><br>
        {studentProfile.proficiency_score.toFixed(1)}/100
      </div>
    </div>
  </div>
</div>
```

**Acceptance Criteria:**
- Stats display in responsive grid
- Numbers format correctly
- Card styling matches Bootstrap theme
- Component accepts studentProfile prop

---

#### Task 3.3: Create Vocabulary Growth Chart Component
**Objective:** Time-series chart showing vocabulary growth over 30 days

**File to Create:** src/lib/components/VocabularyChart.svelte

**Requirements:**
- Chart.js line chart
- X-axis: Last 30 days (date labels)
- Y-axis: Vocabulary size
- One data point per day (aggregated if multiple assignments)
- Only show dots for days with assignments
- Bootstrap card wrapper

**Data Processing:**
```javascript
// Input: array of assignments with dates
// Output: chart data with one point per day

function prepareChartData(assignments) {
  // Group assignments by date
  // Calculate vocabulary size for each date
  // Fill in dates with no assignments (null or previous value)
  // Return Chart.js compatible data structure
}
```

**Component Structure:**
```svelte
<script>
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';

  export let assignments = [];

  let chartCanvas;
  let chart;

  onMount(() => {
    const ctx = chartCanvas.getContext('2d');
    const chartData = prepareChartData(assignments);

    chart = new Chart(ctx, {
      type: 'line',
      data: chartData,
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Vocabulary Size' }
          },
          x: {
            title: { display: true, text: 'Date' }
          }
        }
      }
    });
  });
</script>

<div class="card mb-3">
  <div class="card-header">
    <h5>Vocabulary Growth (Last 30 Days)</h5>
  </div>
  <div class="card-body">
    <canvas bind:this={chartCanvas}></canvas>
  </div>
</div>
```

**Acceptance Criteria:**
- Chart renders correctly
- Shows last 30 days on X-axis
- Data points only appear for days with assignments
- Chart is responsive
- Tooltips show date and vocabulary count
- Chart updates when assignments prop changes

---

#### Task 3.4: Create Recommendations List Component
**Objective:** Display vocabulary word recommendations

**File to Create:** src/lib/components/RecommendationsList.svelte

**Requirements:**
- Bootstrap list group or table
- Display for each word:
  - Word
  - Definition
  - Difficulty score (visual indicator)
  - Example sentences (collapsible)
  - Rationale
- Props: recommendations array
- Empty state message if no recommendations

**Component Structure:**
```svelte
<script>
  export let recommendations = [];

  let expandedWords = new Set();

  function toggleWord(word) {
    if (expandedWords.has(word)) {
      expandedWords.delete(word);
    } else {
      expandedWords.add(word);
    }
    expandedWords = expandedWords; // Trigger reactivity
  }
</script>

<div class="card mb-3">
  <div class="card-header">
    <h5>Recommended Vocabulary Words</h5>
  </div>
  <div class="card-body">
    {#if recommendations.length === 0}
      <p class="text-muted">No recommendations yet. Upload an assignment to generate recommendations.</p>
    {:else}
      <div class="list-group">
        {#each recommendations as rec}
          <div class="list-group-item">
            <div class="d-flex justify-content-between align-items-start">
              <div class="flex-grow-1">
                <h6 class="mb-1">{rec.word}</h6>
                <p class="mb-1">{rec.definition}</p>
                <small class="text-muted">
                  Difficulty: {(rec.difficulty_score * 10).toFixed(0)}/10
                </small>
              </div>
              <button
                class="btn btn-sm btn-outline-primary"
                on:click={() => toggleWord(rec.word)}
              >
                {expandedWords.has(rec.word) ? 'Hide' : 'Show'} Details
              </button>
            </div>

            {#if expandedWords.has(rec.word)}
              <div class="mt-2">
                <strong>Rationale:</strong>
                <p class="mb-2">{rec.rationale}</p>
                <strong>Example Sentences:</strong>
                <ul class="mb-0">
                  {#each rec.example_sentences as sentence}
                    <li>{sentence}</li>
                  {/each}
                </ul>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
```

**Acceptance Criteria:**
- Words display in list format
- Clicking "Show Details" expands rationale and examples
- Difficulty score displays as X/10 format
- Empty state shows helpful message
- List is scrollable if many words
- Bootstrap styling applied

---

#### Task 3.5: Create Mock Assignment Selector Component
**Objective:** Multi-select list for choosing assignments to submit

**File to Create:** src/lib/components/AssignmentSelector.svelte

**Requirements:**
- Display mock assignments from JSON file
- Checkboxes for multi-select
- "Submit Selected" button
- Loading state during submission
- Success/error message display
- Props: studentId, onSubmit callback

**Component Structure:**
```svelte
<script>
  import { createEventDispatcher } from 'svelte';
  import mockAssignments from '$data/mockAssignments.json';

  export let studentId;

  const dispatch = createEventDispatcher();

  let selectedAssignments = new Set();
  let isSubmitting = false;
  let message = null;

  function toggleAssignment(assignmentId) {
    if (selectedAssignments.has(assignmentId)) {
      selectedAssignments.delete(assignmentId);
    } else {
      selectedAssignments.add(assignmentId);
    }
    selectedAssignments = selectedAssignments;
  }

  async function handleSubmit() {
    if (selectedAssignments.size === 0) {
      message = { type: 'warning', text: 'Please select at least one assignment' };
      return;
    }

    isSubmitting = true;
    message = null;

    try {
      const assignments = mockAssignments.filter(a => selectedAssignments.has(a.id));
      dispatch('submit', { studentId, assignments });
      message = { type: 'success', text: `Submitted ${assignments.length} assignment(s)` };
      selectedAssignments.clear();
      selectedAssignments = selectedAssignments;
    } catch (error) {
      message = { type: 'danger', text: `Error: ${error.message}` };
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="card mb-3">
  <div class="card-header">
    <h5>Submit Mock Assignments</h5>
  </div>
  <div class="card-body">
    {#if message}
      <div class="alert alert-{message.type}" role="alert">
        {message.text}
      </div>
    {/if}

    <div class="list-group mb-3">
      {#each mockAssignments as assignment}
        <label class="list-group-item">
          <input
            type="checkbox"
            class="form-check-input me-2"
            checked={selectedAssignments.has(assignment.id)}
            on:change={() => toggleAssignment(assignment.id)}
            disabled={isSubmitting}
          >
          <div>
            <strong>{assignment.title}</strong>
            <br>
            <small class="text-muted">
              {assignment.date} · {assignment.type}
            </small>
            <p class="mb-0 mt-1" style="font-size: 0.9em;">
              {assignment.text.substring(0, 100)}...
            </p>
          </div>
        </label>
      {/each}
    </div>

    <button
      class="btn btn-primary"
      on:click={handleSubmit}
      disabled={isSubmitting || selectedAssignments.size === 0}
    >
      {isSubmitting ? 'Submitting...' : 'Submit Selected Assignments'}
    </button>
  </div>
</div>
```

**Acceptance Criteria:**
- Assignments display with title, date, and preview
- Checkboxes allow multi-select
- Submit button is disabled when nothing selected
- Loading state shows during submission
- Success/error messages display
- Selected assignments clear after successful submit
- Component emits 'submit' event with assignment data

---

### Phase 4: Page Views

#### Task 4.1: Create Teacher Dashboard Page
**Objective:** Main dashboard view showing classroom overview

**File to Create:** src/routes/+page.svelte (teacher view)

**Requirements:**
- Header with view switcher
- "Sync with Google Classroom" button
- Class filter dropdown
- Student list table showing:
  - Student ID
  - Grade
  - Vocabulary Size
  - Proficiency Score
  - Click to view student details
- Responsive Bootstrap grid layout

**Page Structure:**
```svelte
<script>
  import { onMount } from 'svelte';
  import { currentView, students, educator, selectedClass, filteredStudents } from '$lib/stores';
  import { getStudents, syncWithGoogleClassroom } from '$lib/api';
  import Header from '$lib/components/Header.svelte';
  import mockEducator from '$data/mockEducator.json';
  import mockClasses from '$data/mockClasses.json';

  let isSyncing = false;
  let syncMessage = null;

  onMount(async () => {
    educator.set(mockEducator);
    try {
      const studentData = await getStudents();
      students.set(studentData.students || []);
    } catch (error) {
      console.error('Failed to load students:', error);
    }
  });

  async function handleSync() {
    isSyncing = true;
    syncMessage = null;
    try {
      await syncWithGoogleClassroom();
      const studentData = await getStudents();
      students.set(studentData.students || []);
      syncMessage = { type: 'success', text: 'Successfully synced with Google Classroom' };
    } catch (error) {
      syncMessage = { type: 'danger', text: `Sync failed: ${error.message}` };
    } finally {
      isSyncing = false;
    }
  }

  function viewStudent(studentId) {
    currentView.set(studentId);
  }
</script>

<Header />

<div class="container mt-4">
  {#if $currentView === 'teacher'}
    <div class="row mb-3">
      <div class="col-md-6">
        <h2>My Students</h2>
      </div>
      <div class="col-md-6 text-end">
        <button
          class="btn btn-primary"
          on:click={handleSync}
          disabled={isSyncing}
        >
          {isSyncing ? 'Syncing...' : 'Sync with Google Classroom'}
        </button>
      </div>
    </div>

    {#if syncMessage}
      <div class="alert alert-{syncMessage.type}" role="alert">
        {syncMessage.text}
      </div>
    {/if}

    <div class="row mb-3">
      <div class="col-md-4">
        <label class="form-label">Filter by Class:</label>
        <select class="form-select" bind:value={$selectedClass}>
          <option value={null}>All Classes</option>
          {#each mockClasses as classItem}
            <option value={classItem.id}>{classItem.name}</option>
          {/each}
        </select>
      </div>
    </div>

    {#if $filteredStudents.length === 0}
      <div class="alert alert-info">
        No students found. Click "Sync with Google Classroom" to load student data.
      </div>
    {:else}
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Student ID</th>
              <th>Grade</th>
              <th>Class</th>
              <th>Vocabulary Size</th>
              <th>Proficiency Score</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {#each $filteredStudents as student}
              <tr>
                <td>{student.student_id}</td>
                <td>{student.grade_level}</td>
                <td>{student.class || 'N/A'}</td>
                <td>{student.vocabulary_size}</td>
                <td>{student.proficiency_score.toFixed(1)}</td>
                <td>
                  <button
                    class="btn btn-sm btn-outline-primary"
                    on:click={() => viewStudent(student.student_id)}
                  >
                    View Details
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}
</div>
```

**Acceptance Criteria:**
- Teacher view displays when currentView is 'teacher'
- Sync button calls API and refreshes student list
- Class filter dropdown works
- Student table populates from store
- Clicking "View Details" switches to student view
- Empty state shows when no students
- Responsive layout works on mobile

---

#### Task 4.2: Create Student Detail Page
**Objective:** Detailed view for individual student

**File to Modify:** src/routes/+page.svelte (add student view)

**Requirements:**
- Conditional rendering based on currentView store
- Display components:
  - StudentStats
  - VocabularyChart
  - RecommendationsList
  - AssignmentSelector
- Back to dashboard functionality
- Load student data and recommendations on view change

**Page Addition:**
```svelte
<script>
  // ... existing imports
  import StudentStats from '$lib/components/StudentStats.svelte';
  import VocabularyChart from '$lib/components/VocabularyChart.svelte';
  import RecommendationsList from '$lib/components/RecommendationsList.svelte';
  import AssignmentSelector from '$lib/components/AssignmentSelector.svelte';
  import { getStudentProfile, getStudentRecommendations, submitAssignments } from '$lib/api';

  let currentStudentProfile = null;
  let currentRecommendations = [];
  let isLoading = false;

  $: if ($currentView !== 'teacher') {
    loadStudentData($currentView);
  }

  async function loadStudentData(studentId) {
    isLoading = true;
    try {
      const [profile, recommendations] = await Promise.all([
        getStudentProfile(studentId),
        getStudentRecommendations(studentId)
      ]);
      currentStudentProfile = profile;
      currentRecommendations = recommendations.recommendations || [];
    } catch (error) {
      console.error('Failed to load student data:', error);
    } finally {
      isLoading = false;
    }
  }

  async function handleAssignmentSubmit(event) {
    const { studentId, assignments } = event.detail;
    try {
      for (const assignment of assignments) {
        await submitAssignments(studentId, assignment);
      }
      // Reload student data to show updates
      await loadStudentData(studentId);
    } catch (error) {
      console.error('Failed to submit assignments:', error);
    }
  }

  function backToDashboard() {
    currentView.set('teacher');
  }
</script>

<!-- Add after teacher view -->
{#if $currentView !== 'teacher'}
  <div class="container mt-4">
    <div class="row mb-3">
      <div class="col">
        <button class="btn btn-outline-secondary" on:click={backToDashboard}>
          ← Back to Dashboard
        </button>
      </div>
    </div>

    {#if isLoading}
      <div class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    {:else if currentStudentProfile}
      <StudentStats studentProfile={currentStudentProfile} />

      <VocabularyChart assignments={[]} />

      <RecommendationsList recommendations={currentRecommendations} />

      <AssignmentSelector
        studentId={$currentView}
        on:submit={handleAssignmentSubmit}
      />
    {:else}
      <div class="alert alert-danger">
        Failed to load student data.
      </div>
    {/if}
  </div>
{/if}
```

**Acceptance Criteria:**
- Student view displays when currentView is not 'teacher'
- Student data loads automatically on view change
- All components render correctly
- Assignment submission works and refreshes data
- Back button returns to teacher dashboard
- Loading spinner shows during data fetch
- Error state displays if data load fails

---

### Phase 5: Integration and Testing

#### Task 5.1: Configure Environment Variables
**Objective:** Set up environment configuration for different deployment contexts

**File to Create:** .env.example

```
VITE_API_BASE=http://localhost:8000/api/v1
```

**File to Create:** .env.development

```
VITE_API_BASE=http://localhost:8000/api/v1
```

**File to Create:** .env.production

```
VITE_API_BASE=https://your-api-domain.com/api/v1
```

**Acceptance Criteria:**
- Environment variables load correctly in Svelte
- API calls use correct base URL per environment
- Production build uses production API URL
- .env files are in .gitignore

---

#### Task 5.2: Test End-to-End Workflow
**Objective:** Verify complete user flow works correctly

**Test Scenarios:**

**Scenario 1: Teacher Dashboard Flow**
1. Open dashboard (should show teacher view)
2. Click "Sync with Google Classroom"
3. Verify students appear in table
4. Filter by class
5. Verify filtered list updates
6. Click "View Details" on a student

**Scenario 2: Student View Flow**
1. From teacher dashboard, click student
2. Verify stats display correctly
3. Verify chart renders (even if empty)
4. Verify recommendations list displays
5. Select mock assignments
6. Click "Submit Selected Assignments"
7. Verify success message
8. Verify data refreshes
9. Click back to dashboard

**Scenario 3: View Switching**
1. Use header dropdown to switch views
2. Switch to different students
3. Switch back to teacher view
4. Verify state persists correctly

**Acceptance Criteria:**
- All scenarios complete without errors
- Data loads correctly from API
- UI updates reactively
- No console errors
- Loading states display appropriately
- Error messages show when API fails

---

#### Task 5.3: Responsive Design Testing
**Objective:** Ensure dashboard works on mobile and tablet devices

**Test Cases:**
- Desktop (1920x1080)
- Laptop (1366x768)
- Tablet (768x1024)
- Mobile (375x667)

**Elements to Test:**
- Header dropdown
- Student table (should scroll horizontally on mobile)
- Stats cards (should stack on mobile)
- Chart responsiveness
- Buttons and form controls
- Navigation

**Acceptance Criteria:**
- All views are usable on mobile
- No horizontal scroll on mobile (except table)
- Touch targets are at least 44x44px
- Text is readable without zooming
- Bootstrap breakpoints work correctly

---

### Phase 6: Deployment

#### Task 6.1: Configure Vercel Deployment
**Objective:** Set up Vercel project and deployment configuration

**File to Create:** vercel.json

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "framework": "sveltekit",
  "env": {
    "VITE_API_BASE": "https://your-api-domain.com/api/v1"
  }
}
```

**Steps:**
1. Create Vercel account
2. Import GitHub repository
3. Configure environment variables in Vercel dashboard
4. Set production API base URL
5. Deploy

**Acceptance Criteria:**
- Dashboard deploys successfully to Vercel
- Production URL is accessible
- API calls use production endpoint
- Environment variables are set correctly
- HTTPS works properly

---

#### Task 6.2: Create Documentation
**Objective:** Document setup, usage, and deployment process

**File to Create:** dashboard/README.md

**Required Sections:**
1. Project Overview
2. Technology Stack
3. Prerequisites
4. Local Development Setup
5. Environment Variables
6. Running the Development Server
7. Building for Production
8. Deployment to Vercel
9. API Integration
10. Mock Data Strategy
11. Component Structure
12. Troubleshooting

**Acceptance Criteria:**
- README is complete and accurate
- Setup instructions are step-by-step
- Code examples are included
- Links to relevant documentation
- Troubleshooting section addresses common issues

---

## Implementation Order

### Priority 1 (Core Functionality)
1. Task 1.1: Initialize project
2. Task 1.2: Create mock data files
3. Task 1.3: Create API utility
4. Task 1.4: Create Svelte stores
5. Task 2.1: Create seeding script
6. Task 3.1: Create header component

### Priority 2 (Teacher View)
7. Task 4.1: Create teacher dashboard page
8. Task 2.3: Create sync endpoint
9. Test teacher dashboard flow

### Priority 3 (Student View)
10. Task 3.2: Create stats component
11. Task 3.3: Create chart component
12. Task 3.4: Create recommendations component
13. Task 3.5: Create assignment selector
14. Task 4.2: Create student detail view
15. Task 2.2: Create assignment submission endpoint
16. Test student view flow

### Priority 4 (Polish & Deploy)
17. Task 5.1: Configure environment variables
18. Task 5.2: End-to-end testing
19. Task 5.3: Responsive design testing
20. Task 6.1: Deploy to Vercel
21. Task 6.2: Create documentation

## Success Criteria

### Functional Requirements
- Teacher can view list of all students
- Teacher can filter students by class
- Teacher can "sync" with Google Classroom (mock)
- Teacher can view individual student details
- Student view shows vocabulary stats
- Student view shows growth chart
- Student view shows recommendations
- Mock assignments can be submitted
- UI switches between teacher and student views

### Technical Requirements
- Dashboard built with Svelte and Bootstrap
- Chart.js displays vocabulary growth
- API integration uses existing FastAPI backend
- Mock data demonstrates functionality
- Deployed to Vercel
- Responsive on mobile and desktop
- No authentication required

### User Experience Requirements
- Simple, intuitive interface
- Fast load times
- Clear call-to-action buttons
- Helpful empty states
- Success/error feedback messages
- Loading states during async operations

## Notes

- This dashboard is a demonstration/prototype
- Mock data simulates Google Classroom integration
- Backend changes are minimal (only mock endpoints)
- Focus is on UI/UX and frontend functionality
- Production version would require:
  - Real Google Classroom OAuth integration
  - Backend educator and class data models
  - Authentication system
  - Real-time assignment processing
  - Historical data for accurate charts
