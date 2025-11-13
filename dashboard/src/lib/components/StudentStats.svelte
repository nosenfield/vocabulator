<script>
	import VocabularyChart from './VocabularyChart.svelte';
	
	export let studentProfile;
	export let vocabularyList = [];
	export let currentVocabularySize = 0;
</script>

<div class="card mb-3">
	<div class="card-header bg-primary text-white">
		<h5 class="mb-0">Student Profile</h5>
	</div>
	<div class="card-body">
		<div class="row">
			<div class="col-md-5">
				<div class="row">
					<div class="col-6 mb-3">
						<strong>Name:</strong><br />
						<span class="text-muted">
							{studentProfile.first_name || 'N/A'}
							{#if studentProfile.last_initial}
								{studentProfile.last_initial}.
							{/if}
						</span>
					</div>
					<div class="col-6 mb-3">
						<strong>Student ID:</strong><br />
						<span class="text-muted">{studentProfile.student_id}</span>
					</div>
					<div class="col-6 mb-3">
						<strong>Grade Level:</strong><br />
						<span class="text-muted">Grade {studentProfile.grade_level}</span>
					</div>
					<div class="col-6 mb-3">
						<strong>Vocabulary Size:</strong><br />
						<span class="text-muted">{studentProfile.vocabulary_size || 0} words</span>
					</div>
					<div class="col-6">
						<strong>Proficiency Score:</strong><br />
						<span class="text-muted">
							{studentProfile.proficiency_score?.toFixed(1) || '0.0'}/100
						</span>
					</div>
				</div>
			</div>
			<div class="col-md-7">
				<VocabularyChart
					vocabularyList={vocabularyList}
					currentVocabularySize={currentVocabularySize}
				/>
			</div>
		</div>
	</div>
</div>

