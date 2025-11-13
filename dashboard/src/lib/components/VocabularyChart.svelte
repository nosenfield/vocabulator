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
			date.setHours(0, 0, 0, 0); // Normalize to start of day
			days.push(date);
		}

		// Parse all vocabulary entries with first_seen dates
		const vocabularyEntries = [];
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
					const firstSeenDate = new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate());
					firstSeenDate.setHours(0, 0, 0, 0);
					vocabularyEntries.push({ firstSeen: firstSeenDate });
				}
			});
		}

		// Calculate cumulative vocabulary size for each day
		// For each day, count how many words were first seen on or before that day
		const labels = days.map((d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
		const data = [];

		days.forEach((day) => {
			// Count words that were first seen on or before this day
			const wordsKnownByThisDay = vocabularyEntries.filter(
				(entry) => entry.firstSeen <= day
			).length;
			data.push(wordsKnownByThisDay);
		});

		// Ensure the last data point matches current vocabulary size
		// This handles cases where vocabulary_size might differ slightly due to timing
		if (currentVocabularySize > 0 && data.length > 0) {
			const lastIndex = data.length - 1;
			// Use the larger value to ensure we show the current state
			data[lastIndex] = Math.max(data[lastIndex], currentVocabularySize);
		}

		// Calculate max value for y-axis (add 20 for padding)
		const maxDataValue = data.length > 0 ? Math.max(...data) : 0;
		const yAxisMax = maxDataValue > 0 ? maxDataValue + 20 : 20;

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
			],
			yAxisMax: yAxisMax // Store for use in chart options
		};
	}

	onMount(() => {
		if (!chartCanvas) return;

		const ctx = chartCanvas.getContext('2d');
		const chartData = prepareChartData(vocabularyList, currentVocabularySize);
		const yAxisMax = chartData.yAxisMax || 20;

		chart = new Chart(ctx, {
			type: 'line',
			data: {
				labels: chartData.labels,
				datasets: chartData.datasets
			},
			options: {
				responsive: true,
				maintainAspectRatio: true,
				scales: {
					y: {
						beginAtZero: true,
						max: yAxisMax,
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
	// Extract values to ensure Svelte detects changes to nested properties
	$: vocabularyListLength = vocabularyList?.length || 0;
	$: watchedVocabularySize = currentVocabularySize || 0;
	
	// Use the extracted values in the condition to ensure reactivity
	$: if (chart && (vocabularyListLength > 0 || watchedVocabularySize > 0 || vocabularyList || currentVocabularySize !== undefined)) {
		const chartData = prepareChartData(vocabularyList, currentVocabularySize);
		const yAxisMax = chartData.yAxisMax || 20;
		chart.data = {
			labels: chartData.labels,
			datasets: chartData.datasets
		};
		chart.options.scales.y.max = yAxisMax;
		chart.update();
	}
</script>

<div>
	<h6 class="mb-3">Vocabulary Growth (Last {CHART_DAYS} Days)</h6>
	<div style="position: relative; height: 300px;">
		<canvas bind:this={chartCanvas}></canvas>
	</div>
	{#if (!vocabularyList || vocabularyList.length === 0)}
		<p class="text-muted text-center mt-2">
			No vocabulary data available. Submit assignments to see vocabulary growth.
		</p>
	{/if}
</div>

