<script>
	import { onMount } from 'svelte';
	import { currentView, students, educator, selectedClass, filteredStudents } from '$lib/stores';
	import { getStudents, syncWithGoogleClassroom } from '$lib/api';
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
	import { classes } from '$lib/stores';

	let isSyncing = false;
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

	// Watch for view changes to load student data
	$: if ($currentView !== 'teacher' && $currentView) {
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
			currentRecommendations = recommendations.recommendations || recommendations || [];
			// For demo, use mock assignments - in real app, fetch from API
			assignments = [];
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

	async function handleAssignmentSubmit(event) {
		const { studentId, assignments: selectedAssignments } = event.detail;
		try {
			// Process all assignments and handle partial failures
			const results = await Promise.allSettled(
				selectedAssignments.map((assignment) => submitAssignments(studentId, assignment))
			);

			const succeeded = results.filter((r) => r.status === 'fulfilled').length;
			const failed = results.filter((r) => r.status === 'rejected');

			if (failed.length > 0) {
				// Sanitize error messages for production (prevent information disclosure)
				const errorDetails = failed.map((f) => {
					if (import.meta.env.PROD) {
						// In production, return generic string only (no error object access)
						return 'Submission failed';
					}
					// In development, include full error details for debugging
					return f.reason;
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

			// Reload student data to show updates
			if (succeeded > 0) {
				await loadStudentData(studentId);
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
</script>

<Header />

<div class="container mt-4">
	{#if $currentView === 'teacher'}
		<div class="row mb-3">
			<div class="col-md-6">
				<h2>My Students</h2>
			</div>
			<div class="col-md-6 text-end">
				<button class="btn btn-primary" on:click={handleSync} disabled={isSyncing} type="button">
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
			<StudentStats studentProfile={currentStudentProfile} />

			<VocabularyChart {assignments} />

			<RecommendationsList recommendations={currentRecommendations} />

			<AssignmentSelector studentId={$currentView} on:submit={handleAssignmentSubmit} />
		{:else}
			<div class="alert alert-danger">
				Failed to load student data.
			</div>
		{/if}
	{/if}
</div>
