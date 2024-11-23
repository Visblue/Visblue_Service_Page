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
	if (bat_alarm == 'ComingSoon'){
		return { status: "ComingSoon", statusColor: "grey" , 'opacity' : 0.1, };
	}
	//status = (bat_state!= null)? bat_state : null;
	if (bat_alarm != 0) {
		status = bat_alarm;
		statusColor = "#f60f0f";
	}

	if (parseInt(bat_state) == 0) {
		if (status == null) {
			status = "FrozenState";
		} else {
			status += ",FrozenState";
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
	return { status: status, statusColor: statusColor,  'opacity' : 1, };
}


function add_datas(msg) {
    const table = document.getElementById("tables"); // Replace with your actual table's tbody ID

    // Iterate over each key in the msg object
    for (let key in msg) {
        key_without_spaces = key.replace(/\s+/g, "_"); // With spaces it will be hard for the js to find out which key is used.
        const newRow = document.createElement("tr");

        // Create new cells
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

        form_reset = add_reset_btn(key, key_without_spaces);
        noteBtn = add_note_area(key, key_without_spaces, msg[key]["Note"]);

        var status = check_status(msg[key]["Battery_Alarm_State"], msg[key]["Battery_state"], msg[key]["PV_connection_status"], msg[key]["Energy_meter_connection_status"]);
        var showStatus = status.status == undefined ? "<b style='font-size:38px; color:#0fdc3c'; class='bi bi-check2'> </b>" : "<b style='font-size:25; color:" + status.statusColor + "';> " + status.status + " <i style='font-size:14px; color:white; opacity:" + status.opacity + ";'>[" + msg[key]["Alarm_registred"] + "] </i>";
        
        var smartFlow = msg[key]["Battery_control"] == "Smartflow" ? "<p style='color:white;' >" + msg[key]["Battery_control"] + " <i style='color:#37dc0f;' class='fa fa-leaf'></i>" + " </p>" : "<p style='color:white;'>" + msg[key]["Battery_control"] + "</p>";

        var showPrioritet = msg[key]["Site_prioritet"] == 1 ? "<b style='color:red;'>&nbsp; [" +  msg[key]["Site_prioritet"] + "]</b>" : "<b style='color:white;'>&nbsp; [" +  (msg[key]["Site_prioritet"] || 9) + "]</b>";
        
        var showProjectNr = (msg[key]["Project_nr"] == undefined || msg[key]["Project_nr"] == null || msg[key]["Project_nr"] == "-") ? 99999 : msg[key]["Project_nr"];

        newRow.classList.add("textClass");

        nr_td.innerHTML = showProjectNr;
        nr_td.style.textAlign = "right";
        site_td.innerHTML = "&nbsp; " + key || "&nbsp; N/A ";
        prio_td.innerHTML = showPrioritet;
        statud_td.innerHTML = showStatus;
        power_td.innerHTML = msg[key]["Battery_ACPower"] || 0;
        soc_td.innerHTML = msg[key]["Battery_State_of_Charge"] || 0;
        control_td.innerHTML = smartFlow;
        signed_td.innerHTML = (msg[key]["Signed_date"] || "N/A") + "<br>" + (msg[key]["Signed_time"] || "N/A");
        DASA_td.innerHTML = (msg[key]["DA_nr"] || "") + " / " + (msg[key]["SA_nr"] || "");
		prio_td.classList.add("prio_td"); // Tilføj denne linje i din add_data-funktion

        nr_td.style.opacity = status.opacity;
        site_td.style.opacity = status.opacity;
        prio_td.style.opacity = status.opacity;
        signed_td.style.opacity = status.opacity;
        DASA_td.style.opacity = status.opacity;
        planning_td.style.opacity = status.opacity;
        control_td.style.opacity = status.opacity;
        power_td.style.opacity = status.opacity;
        soc_td.style.opacity = status.opacity;
        reset_btn_td.style.opacity = status.opacity;

        // Append the new row to the table
        newRow.appendChild(prio_td);
        newRow.appendChild(nr_td);
        newRow.appendChild(site_td);
        newRow.appendChild(statud_td);
        newRow.appendChild(power_td);
        newRow.appendChild(soc_td);
        newRow.appendChild(control_td);
        note_btn_td.appendChild(noteBtn);
        newRow.appendChild(note_btn_td);
        newRow.appendChild(signed_td);
        newRow.appendChild(DASA_td);
        reset_btn_td.appendChild(form_reset);
        newRow.appendChild(reset_btn_td);

        table.appendChild(newRow);
    }
}


function sortTable(n) {
	var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
	table = document.getElementById("tables");
	switching = true;
	// Set the sorting direction to ascending:
	dir = "asc";
	/* Make a loop that will continue until
	no switching has been done: */
	while (switching) {
	  // Start by saying: no switching is done:
	  switching = false;
	  rows = table.rows;
	  /* Loop through all table rows (except the
	  first, which contains table headers): */
	  for (i = 1; i < (rows.length - 1); i++) {
		// Start by saying there should be no switching:
		shouldSwitch = false;
		/* Get the two elements you want to compare,
		one from current row and one from the next: */
		x = rows[i].getElementsByTagName("TD")[n];
		y = rows[i + 1].getElementsByTagName("TD")[n];
		/* Check if the two rows should switch place,
		based on the direction, asc or desc: */
		if (dir == "asc") {
		  if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
			// If so, mark as a switch and break the loop:
			shouldSwitch = true;
			break;
		  }
		} else if (dir == "desc") {
		  if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
			// If so, mark as a switch and break the loop:
			shouldSwitch = true;
			break;
		  }
		}
	  }
	  if (shouldSwitch) {
		/* If a switch has been marked, make the switch
		and mark that a switch has been done: */
		rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
		switching = true;
		// Each time a switch is done, increase this count by 1:
		switchcount ++;
	  } else {
		/* If no switching has been done AND the direction is "asc",
		set the direction to "desc" and run the while loop again. */
		if (switchcount == 0 && dir == "asc") {
		  dir = "desc";
		  switching = true;
		}
	  }
	}
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
			console.log("STATUS: ", msg[key]["Alarm_registred"] )
			showStatus = "<b style='font-size:25; color:" + status.statusColor + "';> " + status.status + " <i style='font-size:14px; color:white; opacity:" + status.opacity + ";'>[" + msg[key]["Alarm_registred"] + "] </i>";// +"</b> <i style='font-size:15px> [" + msg[key]["Alarm_registred"] + "] </i>";
		}
		
		var smartFlow = null;
		if (msg[key]["Battery_control"] == "Smartflow") {  			
			smartFlow = "<p style='color:white;' >" +  msg[key]["Battery_control"] + " <i style='color:#37dc0f;' class='fa fa-leaf'></i>" +  " </p>";
		}			
		else {            
			smartFlow = "<p style='color:white;'>" +  msg[key]["Battery_control"] + "</p>";    
        }
		if (msg[key]["Battery_control"] == undefined){
			smartFlow = "<p style='color:white;'></p>";    
		}
		
		showPrioritet = null
		if (msg[key]["Site_prioritet"] == 1){
            showPrioritet = "<b style='color:red;'>&nbsp; [" +  msg[key]["Site_prioritet"] + "]</b>";    
        }
		else{			
			if (msg[key]["Site_prioritet"]  != null){
				showPrioritet = "<b style='color:white;'>&nbsp; [" +  msg[key]["Site_prioritet"] + "]</b>";   				
			}
			else{			
				showPrioritet = "<b style='color:white;'>&nbsp; [" +  9 + "]</b>";    
			}
        
		}

		showProjectNr = null
		console.log("Project_nr: ", msg[key]["Project_nr"])
		if (msg[key]["Project_nr"] == undefined || msg[key]["Project_nr"] == null || msg[key]["Project_nr"] == "-"){
			showProjectNr = 99999
		}else{
			showProjectNr = msg[key]["Project_nr"]
		}
		// Create a form inside the reset_btn_td cell (for reset functionality)

		// Set a unique id for the row based on the unique key
		// Unique ID based on the key
		newRow.classList.add("textClass");
		// Populate other cells with data
		nr_td.innerHTML = showProjectNr; // msg[key]["Project_nr"] + "&nbsp; &nbsp;" || "99999 &nbsp; &nbsp;"; // Set the key (A, B, C, D)
		nr_td.style.textAlign = "right";
		nr_td.style.width = "3%";
		site_td.innerHTML = "&nbsp; " + key || "&nbsp; N/A "; // Assuming Site key exists in msg
		site_td.style.textAlign = "left";

		prio_td.style.textAlign = "right";
		prio_td.style.width = "3%";

		
		prio_td.innerHTML = showPrioritet;//"&nbsp; [" + msg[key]["Site_prioritet"] + "]" || "[9]"; // Set the priority value#0fdc3c

		statud_td.innerHTML = showStatus; // Set the status value		
		//nr_td.textContent = msg[key]["Project_nr"] || "N/A";  // Set the TEST value
		power_td.innerHTML = msg[key]["Battery_ACPower"] || 0; // Set the POWER value

		soc_td.innerHTML = msg[key]["Battery_State_of_Charge"] || 0; // Set the SOC value

		control_td.innerHTML = smartFlow; //"<p style='color:#37dc0f;'>" +  msg[key]["Battery_control"] + "</p>" || 'Unknown'; // Set the SOC value

		signed_td.innerHTML = (msg[key]["Signed_date"] || "N/A") + "<br>" + (msg[key]["Signed_time"] + " days" || "N/A");

		DASA_td.innerHTML = (msg[key]["DA_nr"] || "") + " / " + (msg[key]["SA_nr"] || "");
		//reset_btn_td.colSpan = 4;
		// Set the signed date and time
		// Add id to each td (optional, based on your needs)


		//  'opacity' : 1, 
		nr_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		site_td.style.opacity = status.opacity; // Set the opacity of the
		prio_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		signed_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		DASA_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		planning_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		control_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		power_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		soc_td.style.opacity = status.opacity; // Set the opacity of the cell to 1 for visibility
		reset_btn_td.style.opacity = status.opacity; //
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
			try {
			existingRow.querySelector(`#power_td-${key_without_spaces}`).innerHTML = msg[key]["Battery_ACPower"] || 0;
			existingRow.querySelector(`#soc_td-${key_without_spaces}`).innerHTML = msg[key]["Battery_State_of_Charge"] || 0;
			existingRow.querySelector(`#statud_td-${key_without_spaces}`).innerHTML = showStatus; // Set the status value
			existingRow.querySelector(`#control_td-${key_without_spaces}`).innerHTML = smartFlow ; //"<p style='color:#37dc0f;'>" +  msg[key]["Battery_control"] + "</p>"|| "Unknwon Control";
		}	catch (error) {
			console.error(error, key);
			}
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


