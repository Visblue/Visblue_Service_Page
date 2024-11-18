socket = io();
socket.on("connect", function (msg, chargeColor) {});

function add_reset_btn(key, dataplotter) {
	const form_reset = document.createElement("form");
	form_reset.id = `form-${key}`;
	form_reset.method = "POST"; // or GET depending on your needs
	form_reset.action = "/reset_battery"; // Replace with your actual reset endpoint
	// Create an input inside the form
	const input_reset = document.createElement("input");
	input_reset.type = "text";
	input_reset.name = "powerInput";

	//input_reset.value = msg[key]["Battery_ACPower"] || "N/A";  // Default value from the msg object
	// Create a submit button for the form
	const submitButton = document.createElement("button");
	submitButton.type = "submit";
	submitButton.textContent = "Submit";
	submitButton.classList.add("simple-button");

	// Append input and button to the form
	form_reset.appendChild(input_reset);
	form_reset.appendChild(submitButton);
	//form_reset.appendChild(dataplotterLink);
	return form_reset;
}

function add_dataplotter(key, dataplotter) {
	console.log("dataplotter: ", dataplotter);
	const dataplotterLink = document.createElement("a");
	dataplotterLink.href = dataplotter;
	dataplotterLink.target = "_blank";

	const pic = document.createElement("img");
	pic.src = "/static/Wago-logo.png";
	pic.style.height = "50px";
	pic.style.width = "50px";
	pic.style.display = "inline-block";
	pic.style.marginLeft = "10px";
	pic.style.marginRight = "10px";
	pic.style.borderRadius = "50%";
	pic.style.marginTop = "10px";

	dataplotterLink.appendChild(pic);
	return dataplotterLink;
}

function add_note_area(key) {
	noteBtn = document.createElement("textarea");
	noteBtn.type = "text";
	noteBtn.rows = 2;
	noteBtn.cols = 40;
	noteBtn.style.textAlign = "center";
	noteBtn.style.backgroundColor = "transparent";
	noteBtn.id = `input-${key}`;
	noteBtn.name = key;
	noteBtn.style.resize = "none";
	noteBtn.textAlign = "center";

	noteBtn.onchange = function () {
		save_note(this.name, this.value);
	};
	return noteBtn;
}
function save_note(key, value) {
	console.log(key, value);
	socket.emit("note", { key: key, value: value });
}

function add_data(msg) {
	const table = document.getElementById("tables"); // Replace with your actual table's tbody ID

	// Iterate over each key in the msg object
	for (let key in msg) {
		const newRow = document.createElement("tr");
		console.log(key, msg[key]);

		// Create new cells
		//const key_td = document.createElement("td");
		const prio_td = document.createElement("td");
		const site_td = document.createElement("td");
		const nr_td = document.createElement("td");
		const statud_td = document.createElement("td");
		const power_td = document.createElement("td");
		const soc_td = document.createElement("td");
		const control_td = document.createElement("td");
		const note_btn_td = document.createElement("td");
		const signed_td = document.createElement("td");
		const DASA_td = document.createElement("td");
		const planning_td = document.createElement("td");
		const reset_btn_td = document.createElement("td");
		const dataplotter_td = document.createElement("td");

		dataplotters = add_dataplotter(key, msg[key]["Dataplotter"]);
		form_reset = add_reset_btn(key);
		noteBtn = add_note_area(key);

		// Create a form inside the reset_btn_td cell (for reset functionality)

		// Set a unique id for the row based on the unique key
		newRow.id = `row-${key}`; // Unique ID based on the key
		newRow.classList.add("textClass");

		// Populate other cells with data
		nr_td.innerHTML = msg[key]["Project_nr"] + "&nbsp; &nbsp;" || "&nbsp; &nbsp; N/A"; // Set the key (A, B, C, D)
		nr_td.style.textAlign = "right";
		site_td.innerHTML = "&nbsp;" + key || "&nbsp; N/A "; // Assuming Site key exists in msg
		site_td.style.textAlign = "left";
		prio_td.style.textAlign = "right";
		prio_td.style.width = "40px";
		prio_td.textContent = "[" + msg[key]["Site_prioritet"] + "]" || "[9]"; // Set the priority value

		statud_td.textContent = msg[key]["Battery_Alarm_State"] || '<i class="bi bi-check2-square"></i>'; // Set the status value
		statud_td.style.color = msg[key]["Battery_Alarm_Color"] || "white";
		//nr_td.textContent = msg[key]["Project_nr"] || "N/A";  // Set the TEST value
		power_td.textContent = msg[key]["Battery_ACPower"] || 0; // Set the POWER value
		soc_td.textContent = msg[key]["Battery_State_of_Charge"] || 0; // Set the SOC value
		control_td.textContent = msg[key]["Battery_control"] || 0; // Set the SOC value
		signed_td.innerHTML = (msg[key]["Signed_date"] || "N/A") + "<br>" + (msg[key]["Signed_time"] + " days" || "N/A");
		DASA_td.textContent = (msg[key]["DA_nr"] || "") + (msg[key]["SA_nr"] || "");
		reset_btn_td.colSpan = 2;
		reset_btn_td.style.textAlign = "center";
		// Set the signed date and time
		// Add id to each td (optional, based on your needs)

		//  key_td.id = `key-${key}`;
		site_td.id = `site_td-${key}`;
		prio_td.id = `prio_td-${key}`;
		nr_td.id = `nr_td-${key}`;
		statud_td.id = `statud_td-${key}`;
		power_td.id = `power_td-${key}`;
		soc_td.id = `soc_td-${key}`;
		control_td.id = `control_td-${key}`;
		signed_td.id = `signed_td-${key}`;
		DASA_td.id = `DASA_td-${key}`;
		planning_td.id = `planning_td-${key}`;
		reset_btn_td.style.textAlign = "center";

		// Check if the row already exists based on the key
		const existingRow = document.getElementById(`row-${key}`);
		console.log(msg[key]["Battery_ACPower"], msg[key]["Battery_State_of_Charge"]);
		if (existingRow) {
			// If the row exists, update the cells
			const socTd = existingRow.querySelector(`#soc_td-${key}`);
			if (socTd) {
				socTd.innerHTML = msg[key]["Battery_State_of_Charge"] || 0;
			} else {
				console.error(`Cell #soc_td-${key} not found in existingRow ${key}`);
			}
			existingRow.querySelector(`#power_td-${key}`).textContent = msg[key]["Battery_ACPower"] || "N/A";
			existingRow.querySelector(`#soc_td-${key}`).textContent = msg[key]["Battery_State_of_Charge"] || "N/A";
			existingRow.querySelector(`#statud_td-${key}`).textContent = msg[key]["Battery_Alarm_State"] || "OK"; // Set the status value
			existingRow.querySelector(`#control_td-${key}`).textContent = msg[key]["Battery_control"];
		} else {
			// If the row doesn't exist, append the new row
			// adding projectnr + sitename
			newRow.appendChild(prio_td);
			newRow.appendChild(nr_td);
			newRow.appendChild(site_td);
			//adding battery status and battery power, soc and control
			newRow.appendChild(statud_td);
			newRow.appendChild(power_td);
			newRow.appendChild(soc_td);
			newRow.appendChild(control_td);

			//append note placeholder
			note_btn_td.appendChild(noteBtn);
			newRow.appendChild(note_btn_td);

			//adding signed date and time, SA and DA
			newRow.appendChild(signed_td);
			newRow.appendChild(DASA_td);

			// Append the reset button cell to the row
			reset_btn_td.appendChild(form_reset);
			newRow.appendChild(reset_btn_td);
			dataplotter_td.appendChild(dataplotters);
			newRow.appendChild(dataplotter_td);
			// Append the row to the table
			table.appendChild(newRow);
		}
	}
}

socket.on("table", function (msg) {
	console.log("Table data received: ", msg);
	add_data(msg);
});
