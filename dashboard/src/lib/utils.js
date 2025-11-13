/**
 * Helper utility functions
 */

/**
 * Format date string to readable format
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
export function formatDate(dateString) {
	if (!dateString || typeof dateString !== 'string') {
		return 'Invalid date';
	}
	const date = new Date(dateString);
	if (isNaN(date.getTime())) {
		return 'Invalid date';
	}
	return date.toLocaleDateString('en-US', {
		year: 'numeric',
		month: 'short',
		day: 'numeric'
	});
}

/**
 * Format proficiency score with 1 decimal place
 * @param {number} score - Proficiency score
 * @returns {string} Formatted score
 */
export function formatProficiency(score) {
	if (typeof score !== 'number' || isNaN(score)) {
		return '0.0';
	}
	return score.toFixed(1);
}

/**
 * Get difficulty color based on score
 * @param {number} difficultyScore - Difficulty score (0-1)
 * @returns {string} Bootstrap color class
 */
export function getDifficultyColor(difficultyScore) {
	if (typeof difficultyScore !== 'number' || isNaN(difficultyScore) || difficultyScore < 0 || difficultyScore > 1) {
		return 'secondary';
	}
	if (difficultyScore < 0.3) return 'success';
	if (difficultyScore < 0.6) return 'warning';
	return 'danger';
}

