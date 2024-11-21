socket = io();
socket.on("connect", function (msg, chargeColor) {});

function add_reset_btn(key, dataplotter) {
	const form_reset = document.createElement("form");
	form_reset.id = `form-${key_without_spaces}`;
	form_reset.method = "POST"; // or GET depending on your needs
	form_reset.action = "/reset"; // Replace with your actual reset endpoint
	// Create an input inside the form
	const input_reset = document.createElement("input");
	input_reset.id = `input_reset-${key_without_spaces}`;
	input_reset.type = "hidden";
	input_reset.name = "site";
	input_reset.value = key_without_spaces;
	//input_reset.value = msg[key]["Battery_ACPower"] || "N/A";  // Default value from the msg object
	// Create a submit button for the form
	const submitButton = document.createElement("button");
	submitButton.type = "submit";
	submitButton.style.width = "80%";
	submitButton.innerHTML = "<b style='font-size:15px'>" + key + "</b>";
	submitButton.classList.add("simple-button");

	// Optional: Prevent default form submission behavior
	submitButton.onclick = function (event) {
		const res = confirm(`Are you sure you want to restart ${key}?`);
		if (!res) {
			// Prevent form submission if the user cancels
			event.preventDefault();
			console.log("User cancelled the restart operation.");
		} else {
			console.log("Restart operation confirmed for key:", key);
		}
	};
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

function add_note_area(key, key_without_spaces, noteData) {
	noteBtn = document.createElement("textarea");
	noteBtn.type = "text";
	noteBtn.rows = 2;
	noteBtn.cols = 40;
	noteBtn.style.textAlign = "center";
	noteBtn.style.backgroundColor = "transparent";
	noteBtn.id = `noteBtn_td-${key_without_spaces}`;
	noteBtn.name = key;

	noteBtn.style.resize = "none";
	noteBtn.textAlign = "center";
	noteBtn.textContent = noteData;

	noteBtn.onchange = function () {
		save_note(this.name, this.value);
	};
	return noteBtn;
}
function save_note(key, value) {
	console.log(key, value);
	socket.emit("note", { key: key, value: value });
}

function check_status(bat_alarm, bat_state, PV_conn, EM_conn) {
	var status = null;
	var statusColor = "white";

	//status = (bat_state!= null)? bat_state : null;
	if (bat_alarm != 0) {
		status = bat_alarm;
		statusColor = "#f60f0f";
	}

	if (parseInt(bat_state) == 0) {
		if (status == null) {
			status = "Battery_Frozen";
		} else {
			status += ",BatteryFrozen";
		}
		statusColor = "#f60f0f";
	}
	if (PV_conn == -1) {
		if (status == null) {
			status = "PVConnRefused";
		} else {
			status += ",PVConnRefused";
		}
		statusColor = "#f60f0f";
	}
	if (EM_conn == -1) {
		if (status == null) {
			status = "EMConnRefused";
		} else {
			status += ",EMConnRefused";
		}
		statusColor = "#f60f0f";
	}
	if (status == null) {
		status = undefined;
		statusColor = undefined;
	}
	console.log("Status: ", status, "Color: ", statusColor);
	return { status: status, statusColor: statusColor };
}

function add_data(msg) {
	const table = document.getElementById("tables"); // Replace with your actual table's tbody ID

	// Iterate over each key in the msg object
	for (let key in msg) {
		//	console.log(key, msg[key]);
		key_without_spaces = key.replace(/\s+/g, "_"); // With spaces it will be hard for the js to find out which key is used.
		const newRow = document.createElement("tr");

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
		//const dataplotter_td = document.createElement("td");

		//	dataplotters = add_dataplotter(key, msg[key]["Dataplotter"]);

		form_reset = add_reset_btn(key, key_without_spaces);

		//reset_btn_td.style.width = "20%";
		note_btn_td.style.width = "10%";
		noteBtn = add_note_area(key, key_without_spaces, msg[key]["Note"]);

		var status = null;		
		var showStatus = undefined;
		status = check_status(msg[key]["Battery_Alarm_State"], msg[key]["Battery_state"], msg[key]["PV_connection_status"], msg[key]["Energy_meter_connection_status"]);
		if (status.status == undefined) {
			showStatus = "<b style='font-size:38px; color:#0fdc3c'; class='bi bi-check2'> </b>";
		} else {
			showStatus = "<b style='font-size:25; color:" + status.statusColor + "';> " + status.status + "</b> <i style='font-size:15px> [" + msg[key]["Alarm_registred"] + "] </i>";
		}
		
		var smartFlow = null;
		if (msg[key]["Battery_control"] == "Smartflow") {            
			smartFlow = "<p style='color:#37dc0f;'>" +  msg[key]["Battery_control"] + "</p>";
		}			
		else {            
			smartFlow = "<p style='color:white;'>" +  msg[key]["Battery_control"] + "</p>";    
        }
		if (msg[key]["Battery_control"] == undefined){
			smartFlow = "<p style='color:white;'></p>";    
		}
	
		// Create a form inside the reset_btn_td cell (for reset functionality)

		// Set a unique id for the row based on the unique key
		// Unique ID based on the key
		newRow.classList.add("textClass");
		// Populate other cells with data
		nr_td.innerHTML = msg[key]["Project_nr"] + "&nbsp; &nbsp;" || "99999 &nbsp; &nbsp;"; // Set the key (A, B, C, D)
		nr_td.style.textAlign = "right";
		nr_td.style.width = "3%";
		site_td.innerHTML = "&nbsp; " + key || "&nbsp; N/A "; // Assuming Site key exists in msg
		site_td.style.textAlign = "left";

		prio_td.style.textAlign = "right";
		prio_td.style.width = "3%";

		prio_td.innerHTML = "&nbsp; [" + msg[key]["Site_prioritet"] + "]" || "[9]"; // Set the priority value#0fdc3c

		statud_td.innerHTML = showStatus; // Set the status value
		statud_td.style.color = msg[key]["Battery_Alarm_Color"] || "white";
		//nr_td.textContent = msg[key]["Project_nr"] || "N/A";  // Set the TEST value
		power_td.innerHTML = msg[key]["Battery_ACPower"] || 0; // Set the POWER value

		soc_td.innerHTML = msg[key]["Battery_State_of_Charge"] || 0; // Set the SOC value

		control_td.innerHTML = smartFlow; //"<p style='color:#37dc0f;'>" +  msg[key]["Battery_control"] + "</p>" || 'Unknown'; // Set the SOC value

		signed_td.innerHTML = (msg[key]["Signed_date"] || "N/A") + "<br>" + (msg[key]["Signed_time"] + " days" || "N/A");

		DASA_td.innerHTML = (msg[key]["DA_nr"] || "") + " / " + (msg[key]["SA_nr"] || "");
		//reset_btn_td.colSpan = 4;
		// Set the signed date and time
		// Add id to each td (optional, based on your needs)

		newRow.id = `row-${key_without_spaces}`;
		site_td.id = `site_td-${key_without_spaces}`;
		prio_td.id = `prio_td-${key_without_spaces}`;
		nr_td.id = `nr_td-${key_without_spaces}`;
		statud_td.id = `statud_td-${key_without_spaces}`;
		power_td.id = `power_td-${key_without_spaces}`;
		soc_td.id = `soc_td-${key_without_spaces}`;
		control_td.id = `control_td-${key_without_spaces}`;
		signed_td.id = `signed_td-${key_without_spaces}`;
		DASA_td.id = `DASA_td-${key_without_spaces}`;
		planning_td.id = `planning_td-${key_without_spaces}`;

		// Check if the row already exists based on the key_without_spaces
		const existingRow = document.getElementById(`row-${key_without_spaces}`);
		//console.log(msg[key_without_spaces]["Battery_ACPower"], msg[key_without_spaces]["Battery_State_of_Charge"]);
		if (existingRow) {
			// If the row exists, update the cells
			existingRow.querySelector(`#power_td-${key_without_spaces}`).innerHTML = msg[key]["Battery_ACPower"] || 0;
			existingRow.querySelector(`#soc_td-${key_without_spaces}`).innerHTML = msg[key]["Battery_State_of_Charge"] || 0;
			existingRow.querySelector(`#statud_td-${key_without_spaces}`).innerHTML = showStatus; // Set the status value
			existingRow.querySelector(`#control_td-${key_without_spaces}`).innerHTML = smartFlow ; //"<p style='color:#37dc0f;'>" +  msg[key]["Battery_control"] + "</p>"|| "Unknwon Control";
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
			//dataplotter_td.appendChild(dataplotters);
			//newRow.appendChild(dataplotter_td);
			// Append the row to the table
			table.appendChild(newRow);
		}
	}
}

socket.on("table", function (msg) {
	console.log("Table data received: ", msg);
	// Add the received data to the table
	add_data(msg);
});
