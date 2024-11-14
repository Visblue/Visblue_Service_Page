socket = io();
socket.on("connect", function (msg, chargeColor) { });


function add_reset_btn(key) {
    const form_reset = document.createElement("form");
    form_reset.id = `form-${key}`;
    form_reset.method = "POST";  // or GET depending on your needs
    form_reset.action = "/reset_battery";  // Replace with your actual reset endpoint
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
    return form_reset

}



function add_note_area(key) {
    noteBtn = document.createElement("input");
    noteBtn.type = "text";            
    noteBtn.rows = 2;
    noteBtn.cols = 500;
    noteBtn.style.color = "black";
    noteBtn.id = `input-${key}`;
    noteBtn.name = key
    noteBtn.onchange  = function() {
        save_plan(this.name, this.value);
    }
    return noteBtn
}   
function  save_plan(key, value) {
    console.log(key, value);
}

function add_data(msg) {
    const table = document.getElementById("tables"); // Replace with your actual table's tbody ID

    // Iterate over each key in the msg object
    for (let key in msg) {
        const newRow = document.createElement("tr");
        console.log(key, msg[key]);

        // Create new cells
      //  const key_td = document.createElement("td");
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




        form_reset =  add_reset_btn(key)
        noteBtn     = add_note_area(key)
  
        // Create a form inside the reset_btn_td cell (for reset functionality)
  
        // Set a unique id for the row based on the unique key
        newRow.id = `row-${key}`;  // Unique ID based on the key
        newRow.classList.add("textClass")
        
        // Populate other cells with data
        nr_td.textContent = msg[key]["Project_nr"] + " "  || "N/A";  // Set the key (A, B, C, D)
        nr_td.style.textAlign = "right";
        site_td.textContent = key || "N/A";  // Assuming Site key exists in msg
        site_td.style.textAlign = "left";
        statud_td.textContent = msg[key]['Battery_Alarm_State'] || "OK";  // Set the status value
        //nr_td.textContent = msg[key]["Project_nr"] || "N/A";  // Set the TEST value
        power_td.textContent = msg[key]["Battery_ACPower"] || 0;  // Set the POWER value
        soc_td.textContent = msg[key]["Battery_State_of_Charge"] || 0;  // Set the SOC value
        control_td.textContent = msg[key]["Battery_control"] || 0;  // Set the SOC value
        signed_td.textContent = msg[key]['Signed_date']  || "N/A" + "|" + msg[key]['Signed_time'] || "N/A";        
        DASA_td.textContent = msg[key]['DA_nr'] || '' && msg[key]['SA_nr'] || '';
        
        // Set the signed date and time    
        // Add id to each td (optional, based on your needs)        
        
      //  key_td.id = `key-${key}`;
        site_td.id = `site_td-${key}`;
        nr_td.id = `nr_td-${key}`;
        statud_td.id = `statud_td-${key}`;
        power_td.id = `power_td-${key}`;
        soc_td.id = `soc_td-${key}`;
        control_td.id = `control_td-${key}`
        signed_td.id = `signed_td-${key}`;
        DASA_td.id = `DASA_td-${key}`;
        planning_td.id = `planning_td-${key}`;
        //reset_btn_td.id = `reset_btn_td-${key}`;

        // Check if the row already exists based on the key
        const existingRow = document.getElementById(`row-${key}`);
        console.log(msg[key]["Battery_ACPower"], msg[key]["Battery_State_of_Charge"]);
        if (existingRow) {
            // If the row exists, update the cells
            existingRow.querySelector(`#power_td-${key}`).textContent = msg[key]["Battery_ACPower"] || "N/A";
            existingRow.querySelector(`#soc_td-${key}`).textContent = msg[key]["Battery_State_of_Charge"] || "N/A";
            existingRow.querySelector(`#statud_td-${key}`).textContent = msg[key]['Battery_Alarm_State'] || "OK";  // Set the status value
            existingRow.querySelector(`#control_td-${key}`).textContent = msg[key]['Battery_control'];

        } else {
            // If the row doesn't exist, append the new row           
           // adding projectnr + sitename 
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
            

            // Append the row to the table
            table.appendChild(newRow);
        }
    }
}

function add_datas(msg) {

    const table = document.getElementById("tables"); // Replace with your actual table's tbody ID

    // Iterate over each key in the msg object
    for (let key in msg) {
        const newRow = document.createElement("tr");
        console.log(key, msg[key]);
        // Create new cells
        const key_td = document.createElement("td");
        const site_td = document.createElement("td");
        const nr_td = document.createElement("td");
        const power_td = document.createElement("td");
        const soc_td = document.createElement("td");

        // Set a unique id for the row based on the unique key
        newRow.id = `row-${key}`;  // Unique ID based on the key

        // Populate cells with data
        site_td.textContent = key || "N/A";  // Set the key (A, B, C, D)
        nr_td.textContent = msg[key]["Project_nr"] || "N/A";  // Set the TEST value
        power_td.textContent = msg[key]["Battery_ACPower"] || 0;  // Set the POWER value
        soc_td.textContent = msg[key]["Battery_State_of_Charge"] || 0;  // Set the SOC value

        
        
        // Add id to each td (optional, based on your needs)
        key_td.id = `key-${key}`;
        site_td.id = `site_td-${key}`;
        nr_td.id = `nr_td-${key}`;
        power_td.id = `power_td-${key}`;
        soc_td.id = `soc_td-${key}`;
     
        // Check if the row already exists based on the key
        const existingRow = document.getElementById(`row-${key}`);
        console.log(msg[key]["Battery_ACPower"] ,msg[key]["Battery_State_of_Charge"])
        if (existingRow) {
            // If the row exists, update the cells
            //existingRow.querySelector(`#test-${key}`).textContent = msg[key]["TEST "] || "N/A";
           // existingRow.querySelector(`#site_td-${key}`).textContent = key || "non"; //msg[key]["TEST "] || "N/A";
           //existingRow.querySelector(`#nr_td-${key}`).textContent = msg[key]["TEST "] || "N/A";
            existingRow.querySelector(`#power_td-${key}`).textContent = msg[key]["Battery_ACPower"] || 0;
            existingRow.querySelector(`#soc_td-${key}`).textContent = msg[key]["Battery_State_of_Charge"];// || "N/A";
        } else {
            // If the row doesn't exist, append the new row
            newRow.appendChild(key_td);
            newRow.appendChild(site_td);
            newRow.appendChild(nr_td);
            newRow.appendChild(power_td);
            newRow.appendChild(soc_td);
            

            // Append the row to the table
            table.appendChild(newRow);
        }
    }
}










socket.on("table", function(msg){	
    console.log("Table data received: ", msg);
    add_data(msg);
});