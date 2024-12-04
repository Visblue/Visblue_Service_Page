socket = io();
socket.on("connect", function (msg, chargeColor) {});



// newsfeed
function fetchData() {

	$.getJSON('/newsfeed', function (response) {
		data = response;
		data = data.split(",")
		//let splitData = data.split(/\s+/); // Split by spaces, tabs, newlines, etc.

// Join the split data with <br> to create line breaks in HTML
		data = data.join("<br>");
		document.getElementById("newsfeed").innerHTML = data;		

	});


}

// Funksjon for å vise popupen
function showPopup() {
    var popup = document.querySelector('.newsfeedContainer');
    popup.classList.add('show'); // Legger til 'show' for å vise popupen
    var popups = document.querySelector('.status');
    popups.classList.add('show'); // Legger til 'show
}


// Funksjon for å skjule popupen (på knappeklikk)
function rmNewsBoks() {
    var popup = document.querySelector('.newsfeedContainer');
    popup.classList.remove('show'); // Fjerner 'show' for å skjule popupen
}

function addTodo(event)
{

	event.preventDefault();
	 const todoInput = document.getElementById('todo').value;
        
        // You can add logic here to handle the todo item (e.g., display it, save it, etc.)
    console.log("Todo added:", todoInput);
        
        // Optionally clear the input field after adding the todo
    document.getElementById('todo').value = '';

	socket.emit("todo", { todo : todoInput });

}

// For å vise popupen etter en viss tid (f.eks. etter 2 sekunder)
setTimeout(showPopup, 500);

fetchData()






document.addEventListener("DOMContentLoaded", function () {
    const button = document.querySelector(".fancy-button");

    // Simulerer en animationstid (fx 3 sekunder)
    setTimeout(() => {
        button.classList.add("active"); // Gør knappen aktiv
        button.setAttribute("data-tooltip", "Klik for at se de nyeste fejl!");
    }, 3000); // Skift 3000 til den faktiske varighed af din animation
});

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
	noteBtn.style.fontSize  = "15px";
	noteBtn.textAlign = "center";
	noteBtn.textContent = noteData;

	noteBtn.onchange = function () {
		save_note(this.name, this.value);
	};
	return noteBtn;
}
function save_note(key, value) {
	
	socket.emit("note", { key: key, value: value });
}

function check_status(bat_alarm, bat_state,bat_smartflow, bat_control, PV_conn, EM_conn) {	
   // console.log("BAT: " + bat_alarm, bat_state);
	var Battery_status  = null	
	var Energymeter_status = null		
	var PV_Status = null		
	//Battery_status   = bat_alarm == 0 ? null: bat_alarm;
    if (bat_alarm != 0){
        Battery_status = bat_alarm;
    }
    if (bat_state == 0) {
        if (Battery_status == null) {
		Battery_status          = "ReadyForStartup";
		
        }
        else{
            Battery_status = "," + bat_state
        }		
	}
	
	/*if (bat_control == "Smartflow"){
		if (bat_smartflow != 0)
		{
	        if (Battery_status == null) {
			Battery_status  = "SmartflowError";
			
	        }
	        else{
	            Battery_status = ",SmartflowError" 
	        }
		}
	}*/

	/*if (PV_conn == -1){
		PV_Status =  "ConnRefused"
	}
	else { // if (PV_conn == -2){
		PV_Status = null
	}
	*/
	PV_Status               = PV_conn   == -1   ? "ConnRefused" : null;
    Energymeter_status      = EM_conn   == -1   ? "ConnRefused"       : null;
  
    return {Battery : Battery_status, EM : Energymeter_status, PV : PV_Status}
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
		if (key == 'SystemStat'){
			 document.getElementById('TotalSystems').innerHTML = msg[key]['TotalSystems']
			 document.getElementById('TotalOnline').innerHTML = msg[key]['TotalOnline'] 
			 document.getElementById('TotalOffline').innerHTML = msg[key]['TotalOffline'] 
			 document.getElementById('TotalError').innerHTML = msg[key]['TotalError'] 
			 document.getElementById('TotalNoneError').innerHTML = msg[key]['TotalNoneError'] 
		
			 
		}
		form_reset = add_reset_btn(key, key_without_spaces);
		
		//reset_btn_td.style.width = "20%";
		note_btn_td.style.width = "10%";
		noteBtn = add_note_area(key, key_without_spaces, msg[key]["Note"]);

		var status = null;		
		var showStatus = undefined;
        var showOpacity = 1;
       

		try{
				data = msg[key]['Todo'];

			let output = "";
			counter = 0
			data.forEach(item => {
				counter += 1
			    output += counter + ": " + item + "<br>";  // Append each item followed by a <br> tag
			});
			document.getElementById("Todos").innerHTML = output;
		//let splitData = data.split(/\s+/); // Split by spaces, tabs, newlines, etc.
		}
		catch(error) {
		
		
			
		}
// Join the split data with <br> to create line breaks in HTML


		status = check_status(msg[key]["Battery_Alarm_State"], msg[key]["Battery_state"],msg[key]["Battery_Smartflow"], msg[key]["Battery_control"], msg[key]["PV_connection_status"], msg[key]["Energy_meter_connection_status"]);         
		StatusColor = 'red';
    
       // console.log("Battery: ",status.Battery,  msg[key]["Battery_Alarm_State"], msg[key]["Battery_state"], msg[key]["PV_connection_status"], msg[key]["Energy_meter_connection_status"])
        if (status.Battery == 'ComingSoon') {
            showOpacity = 0.2;
            StatusColor = 'grey';
        }
        
        
        
        icon_ = "<b style='font-size:30px; color:#0fdc3c'; class='bi bi-check2'> </b>";

		if (status.Battery == null && status.PV == null && status.EM == null) {
			showStatus = "<b style='font-size:38px; color:#0fdc3c'; class='bi bi-check2'> </b>";        
		} else {			
            showAlarm = "";
            if (msg[key]["Alarm_registred"]){
                showAlarm = "<br><i style='color:white; font-size: 13px;'> Alarm registered: " + msg[key]["Alarm_registred"] + "</b> </i>";
    		}                     
            if (status.Battery == 'ComingSoon') {            
            
              showStatus 	= status.Battery	== null ?	""	:	("<b style='font-size:15px; color:grey;'>Battery: "		+ status.Battery	+	"</b>") + "<br>"
    		 }else {
            status.Battery = status.Battery ||null;       
            Battery_Status_ 	= status.Battery	== null ?	""	:	("<b style='font-size:15px; color:red;'>Battery: "		+ status.Battery	+	"</b>") + "<br>"
			EM_Status_			= status.EM			== null ?	""	:	("<b style='font-size:15px; color:red;'>EM:	"		+ status.EM 			+	"</b>") + "<br>"
			PV_Status_			= status.PV			== null ?	""	:	("<b style='font-size:15px; color:red;'>PV: "		+ status.PV 			+	"</b>") + "<br>"
						
			showStatus = Battery_Status_ + EM_Status_ + PV_Status_
    	
			//console.log("Battery_Status_: ", Battery_Status_)
			//console.log("EM_Status_: ", EM_Status_)
			//console.log("PV_Status_: ", PV_Status_)
			
		}
		}
		
		var smartFlow = null;
		//console.log(msg[key]["Battery_control"] == "Smartflow", msg[key]["Battery_control"])
		if (msg[key]["Battery_control"] == "Smartflow") {			
			smartFlow = "<p style='color:32f60f;'>"  +  msg[key]["Battery_control"] +  " </p>";
		}			
		else  {            
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
		nr_td.style.opacity         = showOpacity; // Set the opacity of the cell to 1 for visibility
		site_td.style.opacity       = showOpacity; // Set the opacity of the
		prio_td.style.opacity       = showOpacity; // Set the opacity of the cell to 1 for visibility
		signed_td.style.opacity     = showOpacity; // Set the opacity of the cell to 1 for visibility
		DASA_td.style.opacity       = showOpacity; // Set the opacity of the cell to 1 for visibility
		planning_td.style.opacity   = showOpacity; // Set the opacity of the cell to 1 for visibility
		control_td.style.opacity    = showOpacity; // Set the opacity of the cell to 1 for visibility
		power_td.style.opacity      = showOpacity; // Set the opacity of the cell to 1 for visibility
		soc_td.style.opacity        = showOpacity; // Set the opacity of the cell to 1 for visibility
		reset_btn_td.style.opacity  = showOpacity; //
        note_btn_td.style.opacity = 1; // Set the opacity of the
        statud_td.style.opacity = showOpacity; // Set the opacity of the
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
	console.log(msg)
	//console.log("Table data received: ", msg);
	// Add the received data to the table
try{
		add_data(msg);
}catch(error){
	console.log("ERROR: ", error)}
	
});

