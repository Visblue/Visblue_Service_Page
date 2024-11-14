socket = io();
socket.on("connect", function (msg, chargeColor) { });


socket.on("table", function(msg){	
    console.log("Table data received: ", msg);
    const table = document.getElementById("tables"); // Replace with your actual table's tbody ID
    const newRow = document.createElement("tr");

    // Create a new cell for battery power
    const tdBatteryPower = document.createElement("td");
    tdBatteryPower.style.textAlign = "center";
    tdBatteryPower.id = `test_battery_power`;

    // Populate the cell with data from `msg`
    tdBatteryPower.textContent = msg.batteryPower || "N/A";  // Use 'N/A' if no batteryPower in the message

    // Append the cell to the row
    newRow.appendChild(tdBatteryPower);

    // Append the row to the table
    table.appendChild(newRow);
});