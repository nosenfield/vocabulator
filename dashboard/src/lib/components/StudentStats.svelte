<script>
	export let studentProfile;
</script>

<div class="card mb-3">
	<div class="card-header bg-primary text-white">
		<h5 class="mb-0">Student Profile</h5>
	</div>
	<div class="card-body">
		<div class="row">
			<div class="col-md-3 mb-3 mb-md-0">
				<strong>Student ID:</strong><br />
				<span class="text-muted">{studentProfile.student_id}</span>
			</div>
			<div class="col-md-3 mb-3 mb-md-0">
				<strong>Grade Level:</strong><br />
				<span class="text-muted">Grade {studentProfile.grade_level}</span>
			</div>
			<div class="col-md-3 mb-3 mb-md-0">
				<strong>Vocabulary Size:</strong><br />
				<span class="text-muted">{studentProfile.vocabulary_size || 0} words</span>
			</div>
			<div class="col-md-3">
				<strong>Proficiency Score:</strong><br />
				<span class="text-muted">
					{studentProfile.proficiency_score?.toFixed(1) || '0.0'}/100
				</span>
			</div>
		</div>
	</div>
</div>

