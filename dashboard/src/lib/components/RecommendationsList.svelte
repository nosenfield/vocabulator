<script>
	import { getDifficultyColor } from '$lib/utils';

	export let recommendations = [];

	let expandedWords = new Set();

	function toggleWord(word) {
		if (expandedWords.has(word)) {
			expandedWords.delete(word);
		} else {
			expandedWords.add(word);
		}
		expandedWords = expandedWords; // Trigger reactivity
	}
</script>

<div class="card mb-3">
	<div class="card-header bg-primary text-white">
		<h5 class="mb-0">Recommended Vocabulary Words</h5>
	</div>
	<div class="card-body">
		{#if recommendations.length === 0}
			<p class="text-muted">
				No recommendations yet. Upload an assignment to generate recommendations.
			</p>
		{:else}
			<div class="list-group">
				{#each recommendations as rec}
					{@const difficulty = rec.difficulty_score || 0}
					{@const colorClass = getDifficultyColor(difficulty)}
					<div class="list-group-item">
						<div class="d-flex justify-content-between align-items-start">
							<div class="flex-grow-1">
								<h6 class="mb-1">{rec.word}</h6>
								<p class="mb-1">{rec.definition || 'No definition available'}</p>
								<small class="text-muted">
									Difficulty: <span
										class="badge"
										class:bg-success={colorClass === 'success'}
										class:bg-warning={colorClass === 'warning'}
										class:bg-danger={colorClass === 'danger'}
									>
										{Math.round(difficulty * 10)}/10
									</span>
								</small>
							</div>
							<button
								class="btn btn-sm btn-outline-primary ms-2"
								on:click={() => toggleWord(rec.word)}
								type="button"
							>
								{expandedWords.has(rec.word) ? 'Hide' : 'Show'} Details
							</button>
						</div>

						{#if expandedWords.has(rec.word)}
							<div class="mt-3">
								{#if rec.rationale}
									<div class="mb-2">
										<strong>Rationale:</strong>
										<p class="mb-0">{rec.rationale}</p>
									</div>
								{/if}
								{#if rec.example_sentences && rec.example_sentences.length > 0}
									<div>
										<strong>Example Sentences:</strong>
										<ul class="mb-0">
											{#each rec.example_sentences as sentence}
												<li>{sentence}</li>
											{/each}
										</ul>
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

