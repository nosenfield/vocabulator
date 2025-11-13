import { writable, derived } from 'svelte/store';

// Current view: 'teacher' or student ID
export const currentView = writable('teacher');

// All students data
export const students = writable([]);

// Current educator data
export const educator = writable(null);

// Available classes (derived from students)
// Returns sorted array of unique class IDs
export const classes = derived(students, ($students) => {
	const classSet = new Set(
		$students.map((s) => s.class || s.metadata?.class).filter(Boolean)
	);
	return Array.from(classSet).sort(); // Sort for consistent ordering
});

// Filtered students by selected class
export const selectedClass = writable(null);
export const filteredStudents = derived(
	[students, selectedClass],
	([$students, $selectedClass]) => {
		if (!$selectedClass) return $students;
		return $students.filter((s) => {
			// Check both class field and metadata.class for compatibility
			const studentClass = s.class || s.metadata?.class;
			return studentClass === $selectedClass;
		});
	}
);

// Sorting state - default to sorting by first_name (alphabetical)
export const sortColumn = writable('first_name'); // 'first_name' | 'student_id' | 'grade_level' | 'class' | 'vocabulary_size' | 'proficiency_score'
export const sortDirection = writable('asc'); // 'asc' | 'desc'

// Sorted and filtered students
export const sortedStudents = derived(
	[filteredStudents, sortColumn, sortDirection],
	([$filteredStudents, $sortColumn, $sortDirection]) => {
		if (!$sortColumn) return $filteredStudents;
		
		const sorted = [...$filteredStudents].sort((a, b) => {
			let aVal, bVal;
			
			switch ($sortColumn) {
				case 'first_name':
					// Sort by first name, then last initial, then student_id as tiebreaker
					aVal = (a.first_name || '') + (a.last_initial || '') + (a.student_id || '');
					bVal = (b.first_name || '') + (b.last_initial || '') + (b.student_id || '');
					return aVal.localeCompare(bVal);
				case 'student_id':
					aVal = a.student_id || '';
					bVal = b.student_id || '';
					return aVal.localeCompare(bVal);
				case 'grade_level':
					aVal = a.grade_level || 0;
					bVal = b.grade_level || 0;
					return aVal - bVal;
				case 'class':
					aVal = a.class || a.metadata?.class || 'N/A';
					bVal = b.class || b.metadata?.class || 'N/A';
					return aVal.localeCompare(bVal);
				case 'vocabulary_size':
					aVal = a.vocabulary_size || 0;
					bVal = b.vocabulary_size || 0;
					return aVal - bVal;
				case 'proficiency_score':
					aVal = a.proficiency_score || 0;
					bVal = b.proficiency_score || 0;
					return aVal - bVal;
				default:
					return 0;
			}
		});
		
		return $sortDirection === 'desc' ? sorted.reverse() : sorted;
	}
);

// Current student (when in student view)
export const currentStudent = derived(
	[students, currentView],
	([$students, $currentView]) => {
		if ($currentView === 'teacher') return null;
		return $students.find((s) => s.student_id === $currentView);
	}
);

