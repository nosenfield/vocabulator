<script>
	import { onMount, onDestroy } from 'svelte';
	import Chart from 'chart.js/auto';

	export let assignments = [];

	let chartCanvas;
	let chart;

	const CHART_DAYS = 30;
	const AVG_WORDS_PER_ASSIGNMENT = 10;

	function prepareChartData(assignments) {
		// Generate last 30 days
		const today = new Date();
		const days = [];
		for (let i = CHART_DAYS - 1; i >= 0; i--) {
			const date = new Date(today);
			date.setDate(date.getDate() - i);
			days.push(date);
		}

		// Group assignments by date
		const assignmentsByDate = {};
		assignments.forEach((assignment) => {
			if (assignment.date) {
				// Validate date before using
				const dateObj = new Date(assignment.date);
				if (isNaN(dateObj.getTime())) {
					// Skip invalid dates and log warning for debugging
					console.warn('Invalid assignment date:', assignment.date);
					return;
				}
				const dateKey = dateObj.toDateString();
				if (!assignmentsByDate[dateKey]) {
					assignmentsByDate[dateKey] = [];
				}
				assignmentsByDate[dateKey].push(assignment);
			}
		});

		// Calculate vocabulary size for each day
		// For demo purposes, we'll simulate growth based on assignment count
		// In real implementation, this would come from student profile history
		const labels = days.map((d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
		const data = [];
		let cumulativeVocab = 0;

		days.forEach((day) => {
			const dateKey = day.toDateString();
			if (assignmentsByDate[dateKey] && assignmentsByDate[dateKey].length > 0) {
				// Simulate vocabulary growth: each assignment adds words
				const wordsAdded = assignmentsByDate[dateKey].length * AVG_WORDS_PER_ASSIGNMENT;
				cumulativeVocab += wordsAdded;
			}
			data.push(cumulativeVocab || null);
		});

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
		const chartData = prepareChartData(assignments);

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

	// Update chart when assignments change
	$: if (chart && assignments) {
		const chartData = prepareChartData(assignments);
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
		{#if assignments.length === 0}
			<p class="text-muted text-center mt-2">
				No assignment data available. Submit assignments to see vocabulary growth.
			</p>
		{/if}
	</div>
</div>

