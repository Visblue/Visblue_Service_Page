<!DOCTYPE html>
<html lang="en">

<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Project Overview</title>
	<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css">
	<style>
		body {
			background-color: #1a1a2e;
			color: white;
			font-family: Arial, sans-serif;
		}

		.container {
			margin-top: 50px;
		}

		table {
			background-color: #2e2e3e;
			border-radius: 8px;
			overflow: hidden;
		}

		th {
			cursor: pointer;
			background-color: #00a86b;
			color: white;
		}

		.filter-box {
			background-color: #2e2e3e;
			padding: 15px;
			border-radius: 8px;
			margin-top: 15px;
		}
	</style>
</head>

<body>
	<div class="container">
		<h1 class="text-center">System Status</h1>
		<p class="text-center" style="font-size: 18px; ">Number of errors: <span id="error-count"
				style="font-size: 20px; font-weight: bold; ">0</span> | Online: <span id="latest-online"
				style="font-size: 20px; font-weight: bold; ">0</span> | Offline <span id="latest-offline"
				style="font-size: 20px; font-weight: bold; ">0</span>
			<br> Latest error detected at: <span id="latest-errorTime"
				style="font-size: 20px; font-weight: bold; ">None</span> &ensp;|&ensp;Latest error: <span
				id="latest-error" style="font-size: 20px; font-weight: bold; ">None</span> &ensp;|&ensp; System: <span
				id="latest-name" style="font-size: 20px; font-weight: bold; ">None</span>
		</p>
		<table class="table table-striped table-dark text-center">
			<thead>
				<tr>
					<th onclick="sortTable(0)">Prioritet</th>
					<th onclick="sortTable(1)">Project Number</th>
					<th onclick="sortTable(2)">Site</th>
					<th onclick="sortTable(3)">Error</th>
					<th onclick="sortTable(4)">Time</th>
				</tr>
			</thead>
			<tbody id="data-table">
				<!-- Data will be dynamically added here -->
			</tbody>
		</table>

		<div class="filter-box">
			<h5>Filter options:</h5>
			<label><input type="checkbox" class="filter-checkbox" value="_Grid" checked> Grid</label>
			<label><input type="checkbox" class="filter-checkbox" value="_PV" checked> PV</label>
			<label><input type="checkbox" class="filter-checkbox" value="Battery" checked> Battery</label>
			<button class="btn btn-success" onclick="applyFilters()">Opdater filtrering</button>
		</div>
	</div>

	<script>
		let data = [];

		function fetchData() {
			$.getJSON('/get_data', function (response) {
				data = response;
				console.log(data)
				renderTable(data);
			});
		}

		// Automatisk opdatering hver 10. minut (600.000 ms)
		setInterval(fetchData, 600000);

		// Frste datahentning
		fetchData();


		// Render data in the table
		function renderTable(data) {
			const tableBody = $('#data-table');
			tableBody.empty();

			let latestError = null;
			var offlineCount = 0
			var onlineCount = 0

			data.forEach((row, index) => {
				if (row.Battery_status == 'OK') {
					onlineCount += 1
					return
				}
				if (row.Battery_status== 'Offline') {
					offlineCount += 1
				}
				const tableRow = `<tr>
        	<td>${row.Prioritet}</td>
            <td>${row.ProjectNr}</td>
            <td>${row.Kunde}</td>
            <td>${row.Battery_status}</td>
            <td>${row.Time}</td>
        </tr>`;
				tableBody.append(tableRow);



				// Find seneste fejl baseret p dato
				if (!latestError || new Date(parseDate(row.Time)) > new Date(parseDate(latestError.Time))) {
					latestError = row

				}
				console.log("LatesteError: ", row)
			});

			// Opdater stats
			$('#error-count').text(data.length);
			$('#latest-errorTime').text(latestError ? latestError.Time : "Ingen fejl");
			$('#latest-error').text(latestError ? latestError.Battery_status : "Ingen fejl");
			$('#latest-name').text(latestError ? latestError.Kunde : "Ingen");
			$('#latest-offline').text(offlineCount ? offlineCount : "Ingen");
			$('#latest-online').text(onlineCount ? onlineCount : "Ingen");
		}

		function parseDate2(dateString) {

			console.log("Date:", dateString)
			// Hvis datoen er i formatet "DD-MM-YYYY HH:MM"
			const parts = dateString.split(/[\s-]+/);
			const [day, month, year] = parts[0].split('-');
			const [hours, minutes] = parts[1].split(':');

			console.log(new Date(year, month - 1, day, hours, minutes));
			// Returner datoobjektet

			return new Date(year, month - 1, day, hours, minutes);
		}
		function parseDate(dateString) {
			const parts = dateString.split(/[\s-]+/);
			const [day, month, year, time] = parts
			const [hours, minutes] = time.split(":");
			console.log(new Date(year, month - 1, day, hours, minutes));
			return new Date(year, month - 1, day, hours, minutes);
		}

		// Sort table
		// Sort table
		function sortTable(columnIndex) {
			data.sort((a, b) => {
				let valueA, valueB;

				// Sortér efter tid, hvis det er kolonne 3
				if (columnIndex === 4) {
					valueA = parseDate(a['Time']);
					valueB = parseDate(b['Time']);
				}
				else if (columnIndex === 0) {
					valueA = a['Prioritet'];
					valueB = b['Prioritet'];
				}
				// Sortér efter ProjectNr, hvis det er kolonne 0
				else if (columnIndex === 1) {
					valueA = a['ProjectNr'];
					valueB = b['ProjectNr'];
				}

				else if (columnIndex === 2) {

					valueA = a['Kunde'];
					valueB = b['Kunde'];
					console.log("here: ", valueA, valueB)
				}
				else if (columnIndex === 3) {
					valueA = a['Battery_status'];
					valueB = b['Battery_status'];
				}

				// Generisk tilgang til andre kolonner
				else {
					valueA = Object.values(a)[columnIndex + 1];
					valueB = Object.values(b)[columnIndex + 1];
				}

				// Sammenlign værdier
				if (valueA < valueB) return -1;
				if (valueA > valueB) return 1;
				return 0;
			});

			renderTable(data); // Opdater tabellen
		}




		// Apply filters
		function applyFilters() {
			const filters = $('.filter-checkbox:checked').map(function () {
				return $(this).val();
			}).get();
			var filteredData = null
			console.log("Filters: ", filters[0], filters, data,)
			if (filters[0] == "Battery") {
				console.log("here")
				filteredData = data.filter(row => !row.Kunde.includes(["_Grid"], ['_PV'])); //filters.includes(row.Kunde));
			}
			else {
				filteredData = data.filter(row => row.Kunde.includes(filters)); //filters.includes(row.Kunde));
			}


			renderTable(filteredData);
		}

		// Initial fetch
		fetchData();
	</script>
</body>

</html>