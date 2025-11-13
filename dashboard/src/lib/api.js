// API base URL - must be set via environment variable
// Note: import.meta.env is replaced at build time by Vite
const API_BASE = import.meta.env.VITE_API_BASE;
// In development, allow localhost fallback; in production, VITE_API_BASE must be set at build time
const API_BASE_URL = API_BASE || (import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '');
if (!API_BASE_URL) {
	// Production build requires VITE_API_BASE. Application will fail at runtime if not set.
	// Use generic error message to avoid exposing configuration details
	const isProduction = !import.meta.env.DEV;
	throw new Error(
		isProduction
			? 'Application configuration error. Please contact support.'
			: 'VITE_API_BASE environment variable is required. Set it in your .env file or build configuration.'
	);
}

/**
 * Generate a request ID for correlation with backend logs
 * Uses crypto.randomUUID() if available, falls back to timestamp-based ID
 * @returns {string} Request ID
 */
function generateRequestId() {
	if (typeof crypto !== 'undefined' && crypto.randomUUID) {
		return crypto.randomUUID();
	}
	// Fallback for environments without crypto.randomUUID
	return `req-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Sanitize string input by removing potentially dangerous characters
 * Used for metadata fields (titles, IDs) that are used in API paths or displayed
 * @param {string} input - Input string to sanitize
 * @returns {string} Sanitized string
 * @throws {Error} If input is not a string
 */
function sanitizeString(input) {
	if (typeof input !== 'string') {
		throw new Error('Expected string input for sanitization');
	}
	// Remove control characters and HTML tags
	// Note: Path traversal sanitization only needed for file paths, not general text
	return input
		.replace(/[\x00-\x1F\x7F]/g, '') // Control characters
		.replace(/<[^>]*>/g, '') // HTML tags
		.trim();
}

/**
 * Student ID validation pattern (STU-### with exactly 3 digits)
 */
const STUDENT_ID_PATTERN = /^STU-\d{3}$/;

/**
 * Get all students (with optional grade filter)
 * @param {number|null} gradeLevel - Optional grade level filter
 * @returns {Promise<Object>} Response with students array
 */
export async function getStudents(gradeLevel = null) {
	const requestId = generateRequestId();
	try {
		// Validate grade level if provided
		if (gradeLevel !== null && (typeof gradeLevel !== 'number' || gradeLevel < 6 || gradeLevel > 8)) {
			throw new Error('Invalid grade level. Must be 6, 7, or 8');
		}
		const url = gradeLevel
			? `${API_BASE_URL}/students?grade_level=${gradeLevel}`
			: `${API_BASE_URL}/students`;
		const response = await fetch(url, {
			headers: {
				'X-Request-ID': requestId
			}
		});
		if (!response.ok) {
			const message = `Failed to fetch students: HTTP ${response.status} [Request ID: ${requestId}]`;
			throw new Error(message);
		}
		return await response.json();
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error occurred';
		console.error(`[${requestId}] Failed to fetch students:`, message);
		throw new Error(`Failed to fetch students: ${message} [Request ID: ${requestId}]`);
	}
}

/**
 * Get single student profile
 * @param {string} studentId - Student ID (format: STU-###)
 * @returns {Promise<Object>} Student profile
 */
export async function getStudentProfile(studentId) {
	const requestId = generateRequestId();
	if (!studentId || typeof studentId !== 'string' || !STUDENT_ID_PATTERN.test(studentId)) {
		throw new Error('Invalid student ID format. Expected format: STU-### (3 digits)');
	}
	// Student ID already validated by regex, no need for additional sanitization
	try {
		const response = await fetch(`${API_BASE_URL}/students/${studentId}/profile`, {
			headers: {
				'X-Request-ID': requestId
			}
		});
		if (!response.ok) {
			const message = `Failed to fetch student profile: HTTP ${response.status} [Request ID: ${requestId}]`;
			throw new Error(message);
		}
		return await response.json();
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error occurred';
		console.error(`[${requestId}] Failed to fetch student profile:`, message);
		throw new Error(`Failed to fetch student profile: ${message} [Request ID: ${requestId}]`);
	}
}

/**
 * Get student recommendations
 * @param {string} studentId - Student ID (format: STU-###)
 * @returns {Promise<Object>} Response with recommendations array
 */
export async function getStudentRecommendations(studentId) {
	const requestId = generateRequestId();
	if (!studentId || typeof studentId !== 'string' || !STUDENT_ID_PATTERN.test(studentId)) {
		throw new Error('Invalid student ID format. Expected format: STU-### (3 digits)');
	}
	// Student ID already validated by regex, no need for additional sanitization
	try {
		const response = await fetch(`${API_BASE_URL}/students/${studentId}/recommendations`, {
			headers: {
				'X-Request-ID': requestId
			}
		});
		if (!response.ok) {
			const message = `Failed to fetch recommendations: HTTP ${response.status} [Request ID: ${requestId}]`;
			throw new Error(message);
		}
		return await response.json();
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error occurred';
		console.error(`[${requestId}] Failed to fetch recommendations:`, message);
		throw new Error(`Failed to fetch recommendations: ${message} [Request ID: ${requestId}]`);
	}
}

/**
 * Mock: Sync students (calls backend to insert mock data)
 * @returns {Promise<Object>} Response with sync status
 */
export async function syncWithGoogleClassroom() {
	const requestId = generateRequestId();
	try {
		const response = await fetch(`${API_BASE_URL}/mock/sync-google-classroom`, {
			method: 'POST',
			headers: {
				'X-Request-ID': requestId,
				'Content-Type': 'application/json'
			}
		});
		if (!response.ok) {
			const message = `Failed to sync with Google Classroom: HTTP ${response.status} [Request ID: ${requestId}]`;
			throw new Error(message);
		}
		return await response.json();
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error occurred';
		console.error(`[${requestId}] Failed to sync with Google Classroom:`, message);
		throw new Error(`Failed to sync with Google Classroom: ${message} [Request ID: ${requestId}]`);
	}
}

/**
 * Mock: Submit assignments (sends assignment data to backend)
 * @param {string} studentId - Student ID (format: STU-###)
 * @param {Object} assignment - Assignment data
 * @returns {Promise<Object>} Response with submission status
 */
export async function submitAssignments(studentId, assignment) {
	const requestId = generateRequestId();
	if (!studentId || typeof studentId !== 'string' || !STUDENT_ID_PATTERN.test(studentId)) {
		throw new Error('Invalid student ID format. Expected format: STU-### (3 digits)');
	}
	if (!assignment || typeof assignment !== 'object') {
		throw new Error('Invalid assignment data');
	}
	if (!assignment.text || typeof assignment.text !== 'string' || assignment.text.length === 0) {
		throw new Error('Assignment text is required');
	}
	// Validate text length to prevent oversized payloads
	const MAX_ASSIGNMENT_LENGTH = 50000; // Reasonable limit for middle school writing
	if (assignment.text.length > MAX_ASSIGNMENT_LENGTH) {
		throw new Error(`Assignment text exceeds maximum length (${MAX_ASSIGNMENT_LENGTH} characters)`);
	}
	
	// Student ID already validated by regex, no need for additional sanitization
	// Don't sanitize assignment.text - backend handles content validation
	// Sanitizing could corrupt legitimate educational content
	const sanitizedTitle = assignment.title ? sanitizeString(assignment.title) : '';
	const sanitizedDate = assignment.date || new Date().toISOString().split('T')[0];
	const sanitizedType = assignment.type === 'writing' || assignment.type === 'transcript' 
		? assignment.type 
		: 'writing'; // Default to writing if invalid
	
	try {
		const endpoint =
			sanitizedType === 'writing'
				? `${API_BASE_URL}/writing/upload`
				: `${API_BASE_URL}/transcripts/upload`;

		const response = await fetch(endpoint, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-Request-ID': requestId
			},
			body: JSON.stringify({
				student_id: studentId,
				text: assignment.text,
				metadata: {
					title: sanitizedTitle,
					date: sanitizedDate,
					type: sanitizedType
				}
			})
		});

		if (!response.ok) {
			const message = `Failed to submit assignment: HTTP ${response.status} [Request ID: ${requestId}]`;
			throw new Error(message);
		}
		return await response.json();
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error occurred';
		console.error(`[${requestId}] Failed to submit assignment:`, message);
		throw new Error(`Failed to submit assignment: ${message} [Request ID: ${requestId}]`);
	}
}

