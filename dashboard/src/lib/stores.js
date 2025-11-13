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

// Current student (when in student view)
export const currentStudent = derived(
	[students, currentView],
	([$students, $currentView]) => {
		if ($currentView === 'teacher') return null;
		return $students.find((s) => s.student_id === $currentView);
	}
);

