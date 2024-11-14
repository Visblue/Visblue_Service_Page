socket = io();
socket.on("connect", function (msg, chargeColor) { });
function add_data(msg) {
    const table = document.getElementById("tables"); // Replace with your actual table's tbody ID

    // Iterate over each key in the msg object
    for (let key in msg) {
        const newRow = document.createElement("tr");

        // Create new cells
        const key_td = document.createElement("td");
        const test_td = document.createElement("td");

        // Set a unique id for the row based on the unique key
        newRow.id = `row-${key}`;  // Unique ID based on the key

        // Populate cells with data
        site_td.textContent = key || "N/A";  // Set the key (A, B, C, D)
        nr_td.textContent = msg[key]["Nr"] || "N/A";  // Set the TEST value
        power_td.textContent = msg[key]["Battery_ACPower"] || "N/A";  // Set the POWER value
        soc_td.textContent = msg[key]["Battery_State_of_Charge"] || "N/A";  // Set the SOC value
        
        
        // Add id to each td (optional, based on your needs)
        key_td.id = `key-${key}`;
        test_td.id = `test-${key}`;

            self.data['Battery_ACPower']                    
    self.data['Battery_Charge_Setpoint']            
    self.data['Battery_Discharge_Setpoint']         
    self.data['Battery_State_of_Charge']            
    self.data['Battery_Alarm_State']                
    self.data['Battery_Temperature']                
    self.data['Battery_frozen']                     
    self.data['Battery_Setpoint_error']             
        // Check if the row already exists based on the key
        const existingRow = document.getElementById(`row-${key}`);

        if (existingRow) {
            // If the row exists, update the cells
            existingRow.querySelector(`#test-${key}`).textContent = msg[key]["TEST "] || "N/A";
        } else {
            // If the row doesn't exist, append the new row
            newRow.appendChild(key_td);
            newRow.appendChild(test_td);

            // Append the row to the table
            table.appendChild(newRow);
        }
    }
}










socket.on("table", function(msg){	
    console.log("Table data received: ", msg);
    add_data(msg);
});