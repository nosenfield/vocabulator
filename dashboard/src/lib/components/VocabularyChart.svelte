<script>
	import { onMount, onDestroy } from 'svelte';
	import Chart from 'chart.js/auto';

	export let assignments = [];
	export let vocabularyList = []; // Vocabulary entries from student profile
	export let currentVocabularySize = 0; // Current vocabulary size from profile

	let chartCanvas;
	let chart;

	const CHART_DAYS = 30;

	function prepareChartData(vocabularyList, currentVocabularySize) {
		// Generate last 30 days
		const today = new Date();
		today.setHours(0, 0, 0, 0); // Normalize to start of day
		const days = [];
		for (let i = CHART_DAYS - 1; i >= 0; i--) {
			const date = new Date(today);
			date.setDate(date.getDate() - i);
			days.push(date);
		}

		// Group vocabulary words by first_seen date
		const wordsByDate = {};
		if (vocabularyList && Array.isArray(vocabularyList)) {
			vocabularyList.forEach((entry) => {
				if (entry.first_seen) {
					// Parse first_seen date (ISO format from API)
					const dateObj = new Date(entry.first_seen);
					if (isNaN(dateObj.getTime())) {
						console.warn('Invalid first_seen date:', entry.first_seen);
						return;
					}
					// Normalize to date (remove time component)
					const dateKey = new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate()).toDateString();
					if (!wordsByDate[dateKey]) {
						wordsByDate[dateKey] = 0;
					}
					wordsByDate[dateKey] += 1;
				}
			});
		}

		// Calculate cumulative vocabulary size for each day
		const labels = days.map((d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
		const data = [];
		let cumulativeVocab = 0;

		days.forEach((day) => {
			const dateKey = day.toDateString();
			// Add words that were first seen on this day
			if (wordsByDate[dateKey]) {
				cumulativeVocab += wordsByDate[dateKey];
			}
			// For days in the future or beyond the last word, use current vocabulary size
			if (day > today || (day.getTime() === today.getTime() && cumulativeVocab === 0)) {
				// If we have a current vocabulary size and haven't reached it yet, use it
				if (currentVocabularySize > 0 && cumulativeVocab < currentVocabularySize) {
					data.push(currentVocabularySize);
				} else {
					data.push(cumulativeVocab || null);
				}
			} else {
				data.push(cumulativeVocab || null);
			}
		});

		// Ensure the last data point matches current vocabulary size
		if (currentVocabularySize > 0 && data.length > 0) {
			const lastIndex = data.length - 1;
			if (data[lastIndex] !== currentVocabularySize) {
				data[lastIndex] = currentVocabularySize;
			}
		}

		return {
			labels,
			datasets: [
				{
					label: 'Vocabulary Size',
					data: data,
					borderColor: 'rgb(75, 192, 192)',
					backgroundColor: 'rgba(75, 192, 192, 0.2)',
					tension: 0.1,
					pointRadius: 4,
					pointHoverRadius: 6
				}
			]
		};
	}

	onMount(() => {
		if (!chartCanvas) return;

		const ctx = chartCanvas.getContext('2d');
		const chartData = prepareChartData(vocabularyList, currentVocabularySize);

		chart = new Chart(ctx, {
			type: 'line',
			data: chartData,
			options: {
				responsive: true,
				maintainAspectRatio: true,
				scales: {
					y: {
						beginAtZero: true,
						title: {
							display: true,
							text: 'Vocabulary Size'
						}
					},
					x: {
						title: {
							display: true,
							text: 'Date'
						}
					}
				},
				plugins: {
					legend: {
						display: true,
						position: 'top'
					},
					tooltip: {
						mode: 'index',
						intersect: false
					}
				}
			}
		});
	});

	onDestroy(() => {
		if (chart) {
			chart.destroy();
		}
	});

	// Update chart when vocabulary data changes
	$: if (chart && (vocabularyList || currentVocabularySize !== undefined)) {
		const chartData = prepareChartData(vocabularyList, currentVocabularySize);
		chart.data = chartData;
		chart.update();
	}
</script>

<div class="card mb-3">
	<div class="card-header bg-primary text-white">
		<h5 class="mb-0">Vocabulary Growth (Last {CHART_DAYS} Days)</h5>
	</div>
	<div class="card-body">
		<div style="position: relative; height: 300px;">
			<canvas bind:this={chartCanvas}></canvas>
		</div>
		{#if (!vocabularyList || vocabularyList.length === 0)}
			<p class="text-muted text-center mt-2">
				No vocabulary data available. Submit assignments to see vocabulary growth.
			</p>
		{/if}
	</div>
</div>

