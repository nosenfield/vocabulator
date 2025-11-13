<script>
	import { currentView, students, educator } from '$lib/stores';

	function handleViewChange(event) {
		currentView.set(event.target.value);
	}
</script>

<nav class="navbar navbar-dark bg-primary">
	<div class="container-fluid">
		<span class="navbar-brand mb-0 h1">Vocabulator Dashboard</span>
		<select
			class="form-select w-auto"
			on:change={handleViewChange}
			value={$currentView}
			aria-label="Select view"
		>
			<option value="teacher">
				Teacher View - {$educator?.name || 'Loading...'}
			</option>
			<option disabled>──────────</option>
			{#each $students as student}
				<option value={student.student_id}>
					{student.student_id} - Grade {student.grade_level}
				</option>
			{/each}
		</select>
	</div>
</nav>

<style>
	.navbar {
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}
	
	.form-select {
		max-width: 300px;
	}
</style>

