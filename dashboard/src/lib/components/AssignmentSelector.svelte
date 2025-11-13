<script>
	import { createEventDispatcher } from 'svelte';
	import mockAssignments from '../../data/mockAssignments.json';

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
			const assignments = mockAssignments.filter((a) => selectedAssignments.has(a.id));
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
	<div class="card-header bg-primary text-white">
		<h5 class="mb-0">Submit Mock Assignments</h5>
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
					/>
					<div>
						<strong>{assignment.title}</strong>
						<br />
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
			type="button"
		>
			{isSubmitting ? 'Submitting...' : 'Submit Selected Assignments'}
		</button>
	</div>
</div>

