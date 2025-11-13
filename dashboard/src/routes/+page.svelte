<script>
	import { onMount } from 'svelte';
	import { currentView, students, educator, selectedClass, filteredStudents, classes, sortColumn, sortDirection, sortedStudents } from '$lib/stores';
	import { getStudents, syncWithGoogleClassroom, clearStudents } from '$lib/api';
	import Header from '$lib/components/Header.svelte';
	import StudentStats from '$lib/components/StudentStats.svelte';
	import VocabularyChart from '$lib/components/VocabularyChart.svelte';
	import RecommendationsList from '$lib/components/RecommendationsList.svelte';
	import AssignmentSelector from '$lib/components/AssignmentSelector.svelte';
	import {
		getStudentProfile,
		getStudentRecommendations,
		submitAssignments
	} from '$lib/api';
	import mockEducator from '../data/mockEducator.json';
	import mockAssignments from '../data/mockAssignments.json';

	let isSyncing = false;
	let isClearing = false;
	let syncMessage = null;
	let isLoading = false;
	let currentStudentProfile = null;
	let currentRecommendations = [];
	let assignments = [];

	onMount(async () => {
		educator.set(mockEducator);
		try {
			const studentData = await getStudents();
			// API returns { students: [...] } or direct array
			const studentList = studentData.students || studentData || [];
			students.set(studentList);
		} catch (error) {
			console.error('Failed to load students:', error);
		}
	});

	// Watch for view changes to load student data (only in browser)
	$: if (typeof window !== 'undefined' && $currentView !== 'teacher' && $currentView) {
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
			
			// Flatten recommendations: API returns array of recommendation objects,
			// each containing a words array. We need to extract all words from all recommendations.
			const recommendationsList = recommendations.recommendations || recommendations || [];
			if (Array.isArray(recommendationsList) && recommendationsList.length > 0) {
				// Check if first item has a 'words' property (it's a recommendation object)
				if (recommendationsList[0].words && Array.isArray(recommendationsList[0].words)) {
					// Flatten: extract all words from all recommendations
					currentRecommendations = recommendationsList.flatMap(rec => rec.words || []);
				} else {
					// Already a flat array of words
					currentRecommendations = recommendationsList;
				}
			} else {
				currentRecommendations = [];
			}
			
			// For demo, use mock assignments - in real app, fetch from API
			// Use mock assignments for timeline visualization
			// Import is at top of file, use it here
			assignments = Array.isArray(mockAssignments) ? mockAssignments : [];
		} catch (error) {
			console.error('Failed to load student data:', error);
		} finally {
			isLoading = false;
		}
	}

	async function handleSync() {
		isSyncing = true;
		syncMessage = null;
		try {
			await syncWithGoogleClassroom();
			const studentData = await getStudents();
			const studentList = studentData.students || studentData || [];
			students.set(studentList);
			syncMessage = { type: 'success', text: 'Successfully synced with Google Classroom' };
		} catch (error) {
			syncMessage = { type: 'danger', text: `Sync failed: ${error.message}` };
		} finally {
			isSyncing = false;
		}
	}

	async function handleClear() {
		if (!confirm('Are you sure you want to clear all students? This will delete all mock student data.')) {
			return;
		}
		isClearing = true;
		syncMessage = null;
		try {
			const result = await clearStudents();
			const studentData = await getStudents();
			const studentList = studentData.students || studentData || [];
			students.set(studentList);
			syncMessage = { 
				type: 'success', 
				text: `Successfully cleared ${result.deleted_count || 0} students. You can now sync again to reload data.` 
			};
		} catch (error) {
			syncMessage = { type: 'danger', text: `Clear failed: ${error.message}` };
		} finally {
			isClearing = false;
		}
	}

	async function handleAssignmentSubmit(event) {
		const { studentId, assignments: selectedAssignments } = event.detail;
		try {
			// Get current student profile to pass grade_level to assignments
			const gradeLevel = currentStudentProfile?.grade_level || 7;
			
			// Process all assignments and handle partial failures
			const results = await Promise.allSettled(
				selectedAssignments.map((assignment) => 
					submitAssignments(studentId, { ...assignment, grade_level: gradeLevel })
				)
			);

			const succeeded = results.filter((r) => r.status === 'fulfilled').length;
			const failed = results.filter((r) => r.status === 'rejected');

			if (failed.length > 0) {
				// Sanitize error messages for production (prevent information disclosure)
				const errorDetails = failed.map((f) => {
					// Always return string only, never expose error objects
					return import.meta.env.PROD
						? 'Submission failed'
						: String(f.reason?.message || f.reason || 'Unknown error');
				});
				console.error('Some assignments failed:', errorDetails);
				// Show user-facing error message
				if (succeeded > 0) {
					syncMessage = {
						type: 'warning',
						text: `${succeeded} assignment(s) submitted successfully, ${failed.length} failed. Check console for details.`
					};
				} else {
					syncMessage = {
						type: 'danger',
						text: `Failed to submit assignments. Check console for details.`
					};
				}
			} else {
				syncMessage = {
					type: 'success',
					text: `Successfully submitted ${succeeded} assignment(s)`
				};
			}

			// Reload student data immediately to show chart updates (vocabulary is ready)
			if (succeeded > 0) {
				await loadStudentData(studentId);
				// Scroll to top of page to show updated stats and chart
				if (typeof window !== 'undefined') {
					window.scrollTo({ top: 0, behavior: 'smooth' });
				}
				
				// Poll for recommendations (they're generated in background, may take 5-8 seconds)
				// Poll every 3 seconds for up to 24 seconds
				let pollCount = 0;
				const maxPolls = 8; // 8 polls * 3 seconds = 24 seconds max
				console.log('Starting to poll for recommendations...');
				const pollInterval = setInterval(async () => {
					pollCount++;
					console.log(`Polling for recommendations (attempt ${pollCount}/${maxPolls})...`);
					try {
						const recommendations = await getStudentRecommendations(studentId);
						console.log('Recommendations response:', recommendations);
						const recommendationsList = recommendations.recommendations || recommendations || [];
						console.log('Recommendations list:', recommendationsList);
						
						if (Array.isArray(recommendationsList) && recommendationsList.length > 0) {
							// Check if first item has a 'words' property (it's a recommendation object)
							if (recommendationsList[0].words && Array.isArray(recommendationsList[0].words)) {
								// Flatten: extract all words from all recommendations
								currentRecommendations = recommendationsList.flatMap(rec => rec.words || []);
								console.log('Flattened recommendations:', currentRecommendations);
							} else {
								// Already a flat array of words
								currentRecommendations = recommendationsList;
								console.log('Using recommendations as-is:', currentRecommendations);
							}
							// Stop polling once we have recommendations
							console.log(`Found ${currentRecommendations.length} recommendations, stopping poll`);
							clearInterval(pollInterval);
						} else {
							console.log('No recommendations yet, continuing to poll...');
						}
					} catch (error) {
						console.error('Error polling for recommendations:', error);
					}
					
					// Stop polling after max attempts
					if (pollCount >= maxPolls) {
						console.log('Max poll attempts reached, stopping');
						clearInterval(pollInterval);
					}
				}, 3000); // Poll every 3 seconds
			}
		} catch (error) {
			console.error('Failed to submit assignments:', error);
			syncMessage = {
				type: 'danger',
				text: `Error submitting assignments: ${error.message}`
			};
		}
	}

	function viewStudent(studentId) {
		currentView.set(studentId);
	}

	function backToDashboard() {
		currentView.set('teacher');
	}

	function handleSort(column) {
		if ($sortColumn === column) {
			// Toggle direction if same column
			sortDirection.set($sortDirection === 'asc' ? 'desc' : 'asc');
		} else {
			// New column, default to ascending
			sortColumn.set(column);
			sortDirection.set('asc');
		}
	}

	function getSortIcon(column) {
		if ($sortColumn !== column) return '⇅';
		return $sortDirection === 'asc' ? '↑' : '↓';
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
				<button class="btn btn-outline-danger me-2" on:click={handleClear} disabled={isClearing || isSyncing} type="button">
					{isClearing ? 'Clearing...' : 'Clear Students'}
				</button>
				<button class="btn btn-primary" on:click={handleSync} disabled={isSyncing || isClearing} type="button">
					{isSyncing ? 'Syncing...' : 'Sync with Google Classroom'}
				</button>
			</div>
		</div>

		{#if syncMessage}
			<div
				class="alert"
				class:alert-success={syncMessage.type === 'success'}
				class:alert-warning={syncMessage.type === 'warning'}
				class:alert-danger={syncMessage.type === 'danger'}
				role="alert"
			>
				{syncMessage.text}
			</div>
		{/if}

		<div class="row mb-3">
			<div class="col-md-4">
				<label for="class-filter" class="form-label">Filter by Class:</label>
				<select id="class-filter" class="form-select" bind:value={$selectedClass}>
					<option value={null}>All Classes</option>
					{#each $classes as classId}
						<option value={classId}>{classId}</option>
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
							<th>
								<button
									class="btn btn-link text-decoration-none p-0 fw-bold text-start"
									on:click={() => handleSort('first_name')}
									type="button"
								>
									Name {getSortIcon('first_name')}
								</button>
							</th>
							<th>
								<button
									class="btn btn-link text-decoration-none p-0 fw-bold text-start"
									on:click={() => handleSort('student_id')}
									type="button"
								>
									Student ID {getSortIcon('student_id')}
								</button>
							</th>
							<th>
								<button
									class="btn btn-link text-decoration-none p-0 fw-bold text-start"
									on:click={() => handleSort('grade_level')}
									type="button"
								>
									Grade {getSortIcon('grade_level')}
								</button>
							</th>
							<th>
								<button
									class="btn btn-link text-decoration-none p-0 fw-bold text-start"
									on:click={() => handleSort('class')}
									type="button"
								>
									Class {getSortIcon('class')}
								</button>
							</th>
							<th>
								<button
									class="btn btn-link text-decoration-none p-0 fw-bold text-start"
									on:click={() => handleSort('vocabulary_size')}
									type="button"
								>
									Vocabulary Size {getSortIcon('vocabulary_size')}
								</button>
							</th>
							<th>
								<button
									class="btn btn-link text-decoration-none p-0 fw-bold text-start"
									on:click={() => handleSort('proficiency_score')}
									type="button"
								>
									Proficiency Score {getSortIcon('proficiency_score')}
								</button>
							</th>
							<th>Action</th>
						</tr>
					</thead>
					<tbody>
						{#each $sortedStudents as student}
							<tr>
								<td>
									{student.first_name || 'N/A'}
									{#if student.last_initial}
										{student.last_initial}.
									{/if}
								</td>
								<td>{student.student_id}</td>
								<td>{student.grade_level}</td>
								<td>{student.class || student.metadata?.class || 'N/A'}</td>
								<td>{student.vocabulary_size || 0}</td>
								<td>{(student.proficiency_score || 0).toFixed(1)}</td>
								<td>
									<button
										class="btn btn-sm btn-outline-primary"
										on:click={() => viewStudent(student.student_id)}
										type="button"
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
	{:else}
		<!-- Student Detail View -->
		<div class="row mb-3">
			<div class="col">
				<button class="btn btn-outline-secondary" on:click={backToDashboard} type="button">
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
			<StudentStats
				studentProfile={currentStudentProfile}
				vocabularyList={currentStudentProfile.vocabulary_list || []}
				currentVocabularySize={currentStudentProfile.vocabulary_size || 0}
			/>

			<RecommendationsList recommendations={currentRecommendations} />

			<AssignmentSelector studentId={$currentView} on:submit={handleAssignmentSubmit} />
		{:else}
			<div class="alert alert-danger">
				Failed to load student data.
			</div>
		{/if}
	{/if}
</div>

<style>
	th button {
		color: inherit;
		border: none;
		cursor: pointer;
		transition: opacity 0.2s;
	}
	
	th button:hover {
		opacity: 0.7;
	}
	
	th button:focus {
		outline: 2px solid #0d6efd;
		outline-offset: 2px;
	}
</style>
