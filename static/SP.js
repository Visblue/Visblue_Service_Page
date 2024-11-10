socket = io();
socket.on("connect", function (msg, chargeColor) { });

let plans  = new Object
let notes   = new Object();
let currentDate = new Date();

setInterval(function() {
    location.reload();
}, 6000000); // 300000 millisekunder svarer til 5 minutter

	


setTimeout(function() {
	document.body.classList.add('blurred');
            // Start loading-animationen
        setTimeout(function() {
                // Efter 15 sekunder, fjern overlay og blur
                document.getElementById('overlay').classList.add('hidden');
                document.getElementById('content').classList.remove('hidden');
                document.body.classList.remove('blurred'); // Fjern blur-effekten
            }, 100); // 15000 ms = 15 sekunder
        }, 1000); // 2000 ms = 2 sekunder/ 15000 ms = 15 sekunder
function addLeadingZero(value) {
    return value < 10 ? '0' + value : value;
}

function offline_sites(msg){		
	document.getElementById(String(msg.Kunde) + "_battery_power").innerHTML 			= "";
	document.getElementById(String(msg.Kunde) + "_battery_soc").innerHTML				= "";
    document.getElementById(String(msg.Kunde) + "_battery_status").innerHTML = "<div style='color:red'> OFFLINE</div> "; 
	
    return
}


function online_sites(msg){
    showStatus		= ""
    ShowStatusColor = ""    
    showStatus		=	(msg.battery_status	!= 'OK') ? "<b style='color:red;'> Battery: "	+ msg.battery_status	+ "</b>" + "&nbsp;" +  "<i style='font-size:14px;'> ["+ msg.battery_alarm_detected	+ "]</i><br>" 	: "";
    showStatus		+=	(parseInt(msg.battery_notCharging)	>= 480 ) ? "<b style='color:red;'> Battery: TimeSinceLastChargeOrDischarge: "	+ msg.battery_notCharging	+ "</b>" + "&nbsp; <br>" : "";
	if (msg.grid_alarm_detected == ""){		
		showStatus		+=	(msg.grid_status 	!= 'OK') ? "<b style='color:red;'> Grid: "		+ msg.grid_status		+ "</b><br>"  : ""; // + "&nbsp;" +  "<i style='font-size:14px;'> ["+ msg.grid_alarm_detected 	+ "]</i><br>" 	: "";    
	}
	else{
    	showStatus		+=	(msg.grid_status 	!= 'OK') ? "<b style='color:red;'> Grid: "		+ msg.grid_status		+ "</b>" + "&nbsp;" +  "<i style='font-size:14px;'> ["+ msg.grid_alarm_detected 	+ "]</i><br>" 	: "";    
	}
    if (msg.tarifstyring_version == 'Wendeware control'){    
    		if (msg.pv_alarm_detected == ""){
    				showStatus	+= (msg.pv_status != 'OK')			? "<b style='color:red;'> PV: " 		+ msg.pv_status 			+ "</b> <br>" : ""; //+ "&nbsp;" +  "<i style='font-size:14px;'> ["+ msg.pv_alarm_detected 	+ "]</i><br>"	: ""; 
    		}
    		else{
    			showStatus	+= (msg.pv_status != 'OK')			? "<b style='color:red;'> PV: " 		+ msg.pv_status 			+ "</b>" + "&nbsp;" +  "<i style='font-size:14px;'> ["+ msg.pv_alarm_detected 	+ "]</i><br>"	: "";     			
    		}
        showStatus	+= (msg.total_consumption != 'OK')	? "<b style='color:red;'> Mypowergrid:" +  msg.total_consumption	+ "</b> <br>"	: "";      
    }      
//	if (msg.note.note != null){		
//		document.getElementById(String(msg.Kunde) + "_TextArea").innerHTML = msg.note["note"];
	//}	
	if (showStatus == ""){		
		document.getElementById(String(msg.Kunde) + "_battery_status").innerHTML ="<b class='bi bi-check-lg' style='color:#17da41; font-size:40px;' ></b> <br> ";
	}	
	else{		
		document.getElementById(String(msg.Kunde) + "_battery_status").innerHTML= showStatus;// + "<i style='color:white; font-size:16px; '> " + planstatus  + "</i>"
	}		
	//document.getElementById(String(msg.Kunde) + "_Projekt").innerHTML					= msg.ProjektNr;	
	document.getElementById(String(msg.Kunde) + "_battery_power").innerHTML	= msg.battery_power +	"W";
	document.getElementById(String(msg.Kunde) + "_battery_soc").innerHTML	= msg.battery_soc	+	" % ";	
}




function comingSoon(msg){
	document.getElementById(String(msg.Kunde) + "_battery_status").innerHTML			= "<i style='color:grey;'>" + msg.battery_status;		+ "</i>";
	document.getElementById(String(msg.Kunde)).innerHTML								= "<i style='color:grey;'>" + msg.Kunde 				+ "</i>" ;   //'<a href="' + String(msg.google) + '"target="' + msg.google +'" style="color:grey; font-size:28px;  text-decoration:none;">  &#127757' + "</a>" + "&nbsp;" + msg.Kunde;
	document.getElementById(String(msg.Kunde) + "_Projekt").innerHTML					= "<i style='color:grey;'>[" + 9 + "] &nbsp;" +  msg.ProjektNr 			+ "</i>";
	document.getElementById(String(msg.Kunde) + "_TarifstyringVersion").innerHTML		= "<i style='color:grey;'>" + msg.tarifstyring_version	+ "</i>";
	document.getElementById(String(msg.Kunde) + "_Drift").innerHTML						= "<i style='color:grey;'>" + (msg.drift == null || msg.drift == "" ) ? "" : msg.drift  + "/" + (msg.sa == null || msg.sa == "" ) ? "" : msg.sa +"</i>";	
	document.getElementById(String(msg.Kunde) + "_Deadline").innerHTML					= "<i style='color:grey;'>" + (msg.deadline == "-" ? "": msg.deadline) + "<br>" + msg.days_left +  "</i>";
	//document.getElementById(String(msg.Kunde) + "_Save").disabled = true;
	//document.getElementById(String(msg.Kunde) + "_plans").disabled = true;
	
	
}


socket.on("table", function(msg){	
	//console.log(msg)
  	resetBtn = document.getElementById(String(msg.Kunde) + "_resBtn").name = msg.Kunde
	 if (msg.battery_status == "Coming soon"){
    	comingSoon(msg);
    	return}
    priColor = msg.prioritet == 1 ? "red" : "white";
	daysleft  = (parseInt(msg.days_left) < 0 ? msg.days_left : msg.days_left);
    //daysleftColor = (parseInt(msg.days_left) < 0 ? 'red' : "#17da41")
	prio =	( msg.prioritet == "") ? "":  "<b style='color:" + priColor + ";'>[" + msg.prioritet + "]&nbsp;</b>" 
	//document.getElementById(String(msg.Kunde)).innerHTML = document.getElementById(String(msg.Kunde)).innerHTML =  '<a href="' + String(msg.google) + '"target="' + msg.google +'" style="color:white; font-size:28px;  text-decoration:none;">  &#127757' + "</a>" + "&nbsp;" + msg.Kunde +"&nbsp;<a href='" + msg.kunde_site + "' target=''><i class='bi bi-laptop' style='font-size: 2em; '></i></a>" ;
	//document.getElementById(String(msg.Kunde)).innerHTML = '<a href="' + String(msg.google) + '" target="' + msg.google + '" style="color:white; font-size:28px; text-decoration:none;">&#127757' +  "</a>" + "&nbsp;" + msg.Kunde + "&nbsp;" +  "<a href='" + msg.kunde_site + "' target=''>" + "<i class='bi bi-laptop' style='font-size: 2em;' onmouseover='showTooltip(event)' onmouseout='hideTooltip(event)'></i>" +  "</a>" + "<span class='tooltip-text' style='display:none; position:absolute; background-color:black; color:white; padding:5px; border-radius:5px;'>Dette er en bsbar computer</span>"; 
	if (msg.note.note != null){		
		document.getElementById(String(msg.Kunde) + "_TextArea").innerHTML = msg.note["note"];}
	document.getElementById(String(msg.Kunde)).innerHTML = " &nbsp; <a href='" + msg.kunde_site + "' target=''>" + "<i class='bi bi-laptop' style='color:white; font-size: 2em;' onmouseover='showTooltip(event)' onmouseout='hideTooltip(event)'></i>" +  "</a>" + "<span class='tooltip-text' style='display:none; position:relative; background-color:black; color:white; padding:5px; border-radius:5px;'>Dette er en bsbar computer</span>"   + "&nbsp; &nbsp;"+ msg.Kunde ;
	document.getElementById(String(msg.Kunde) + "_Projekt").innerHTML					=    prio +" " + msg.ProjektNr ;
	document.getElementById(String(msg.Kunde) + "_TarifstyringVersion").innerHTML		=  msg.tarifstyring_version;
	document.getElementById(String(msg.Kunde) + "_Drift").innerHTML						=  ((msg.drift == null ) ? "": msg.drift ) + "/" + ((msg.sa == null ) ? "": msg.sa );	
	document.getElementById(String(msg.Kunde) + "_Deadline").innerHTML					=  (msg.deadline == "-" ? "": msg.deadline) + "<br>" + "<i style='color:"+ "white" + "';>" + daysleft + " days" ;
//	document.getElementById(String(msg.Kunde) + "_Save").disabled = true;
//	document.getElementById(String(msg.Kunde) + "_plans").disabled = true;    
	//console.log("PLAN: ", msg.plan.date)
	add_plan(msg)
    msg.battery_status == 'Offline' ? offline_sites(msg):  online_sites(msg)
 
}); 

function showTooltip(event) {
    const tooltip = event.target.nextElementSibling;
    tooltip.style.display = 'block';
    tooltip.style.left = event.pageX + 'px';
    tooltip.style.top = (event.pageY - 30) + 'px'; // Justér placeringen om nødvendigt
}

function hideTooltip(event) {
    const tooltip = event.target.nextElementSibling;
    tooltip.style.display = 'none';
}
function add_plan(msg){	
	
	planstatus = ""	
	var dateInput = document.getElementById(String(msg.Kunde) + "_plans");	
	var writePlan = document.getElementById(String(msg.Kunde) + "_plan_placeholder");
    if (msg.plan.date != null){    	    
    		planstatus +=  msg.plan.date + " - " + msg.plan.sName   ;     	    				   
            dateInput.style.visibility = "hidden";          
            document.getElementById(String(msg.Kunde) + "_plan_placeholder").innerHTML			= planstatus;//_plan_placeholder               
    		document.getElementById(String(msg.Kunde) + "_Save").value							= 'Delete'
    		document.getElementById(String(msg.Kunde) + "_plan_placeholder").style.fontSize 	= "17px";
			document.getElementById(String(msg.Kunde) + "_plan_placeholder").style.textAlign	= "left";
    		document.getElementById(String(msg.Kunde) + "_Save").disabled				= false;
	}
    else{         
            writePlan.innerHTML 		= "";
            dateInput.style.visibility	= "visible";            
    		document.getElementById(String(msg.Kunde) + "_Save").value			= 'Save'
    		document.getElementById(String(msg.Kunde) + "_Save").disabled		= false;	
    		document.getElementById(String(msg.Kunde) + "_plans").disabled		= false;
    		}   
    }
    
function saveNote (data){
	site = data.id.split('_TextArea')[0] 
	note = data.value
	socket.emit('saveNote', {'site' : site, 'note': note});}

function Plan(customers) {
    btn = document.getElementById(String(customers) + "_Save")
    if (btn.value == 'Delete'){
    	ans = confirm("Are you sure?")
    	if (ans){
    		
    	socket.emit("resetPlan", {"site" : customers})}    	
    	return
	}        
	else {
        if (document.getElementById(customers + "_plans").value == null || document.getElementById(customers + "_plans").value == "") { 
        	alert("Try again! "); 
        	return; 
        	}
        ServiceName = prompt("Name")
        if (!isNaN(ServiceName)) {
            alert("Only letters!");
            return;
        }
        ServiceNote = prompt("Note")
        if (ServiceName == 'yes' || ServiceName == 'Yes' || ServiceName == 'asda' || ServiceName == "qqq") {
        	alert("Try again"); 
        	}
        else {        
            socket.emit("plan", { name: customers, date: document.getElementById(customers + "_plans").value, Sname: ServiceName, Note: ServiceNote })
        }
    }
}


function Reset(value) {
        document.getElementById(value).getAttribute("disabled");
        res = prompt("Pinkode");
        if (!isNaN(res)) {
            alert("Try again!");
            return;
        }
        if (res.length > 3) {
            socket.emit("Pinkode", { Kunde: value, Kode: res });
            document.getElementById("ResetRes").innerHTML = "Wait for response";
        }
        else {
            alert('Try again!');
        }
    }
    var intervals;
    socket.on("PinkodeRes", function (msg) {
        var respons = document.getElementById("ResetRes");
        if (msg.Kode == "Accepted") {
            alert(String(msg.Kunde) + " - Restarted!");
        }
        if (msg.Kode == "Failed") {
            alert("Wrong password try again!");
        }
        if (msg.Kode == "ConnectionFailed") {
            alert(String(msg.Kunde) + "- Modbus connection refused");
        }
        intervals = setInterval(resetResText, 3000);
    });
/*
function sortTable(n) {
    var table, rows, switching, i, x, y, shouldSwitch, dir,
        switchcount = 0;
    table = document.getElementById("tables");
    switching = true;
    dir = "asc";
    while (switching) {
        //start by saying: no switching is done:
        switching = false;
      
        rows = table.rows;
    	
      
        console.log(rows.length)
        for (i = 1; i < rows.length - 1; i++) {
            //start by saying there should be no switching:
            shouldSwitch = false;
   
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            //console.log( x.textContent.split(" ", 15)[3])//.replace("w", ""))//.split(";", 16)[4])
            //break;
            //#break
            
            
            if (n ==  3 ) {
         
                if (dir == "asc") {
                    if (parseFloat(x.innerHTML.replace("w", "")) > parseFloat(y.innerHTML.replace("w", ""))) {
                        shouldSwitch = true;
                        break;
                    }
                } else if (dir == "desc") {
                    if (parseFloat(x.innerHTML.replace("w", "")) < parseFloat(y.innerHTML.replace("w", ""))) {
                        //if so, mark as a switch and break the loop:
                        shouldSwitch = true;
                        break;
                    }
                }
            }
        /*    else if (n > 4 && n < 7) {
                if (dir == "asc") {
                    if (parseInt(x.innerHTML.split(";", 10)[4]) > parseInt(y.innerHTML.split(";", 10)[4])) {
                        shouldSwitch = true;
                        break;
                    }

                } else if (dir == "desc") {
                    if (parseInt(x.innerHTML.split(";", 10)[4]) < parseInt(Y.innerHTML.split(";", 10)[4])) {
                        //if so, mark as a switch and break the loop:
                        shouldSwitch = true;
                        break;
                    }
                }
            }
            else {
            	try{
	            		x_text = x.textContent.split(" ", 15)[3]
	            		y_text = y.textContent.split(" ", 15)[3]
	                if (dir == "asc") {
	                    if (x_text.toLowerCase() > y_text.toLowerCase()) {
	                        shouldSwitch = true;
	                        break;
	                    }
	
	                } else if (dir == "desc") {
	                    if (x_text.toLowerCase() < y_text.toLowerCase()) {
	                        shouldSwitch = true;
	                        break;
	                    }
	                }}
	                catch (error) {
	                	alert("Please wait for all sites are loaded");
	                	break;}
	                	
	                	
	               	
            }
        }

        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            //Each time a switch is done, increase this count by 1:
            switchcount++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}*/

function sortTable(columnIndex) {
  const table = document.getElementById("tables");
  let rows, switching, i, x, y, shouldSwitch, direction, switchCount = 0;
  switching = true;
  direction = "asc"; // Set the sorting direction to ascending by default

  while (switching) {
    switching = false;
    rows = table.rows;
    for (i = 1; i < (rows.length - 1); i++) {
      shouldSwitch = false;
      // Use textContent to get the text of the <td> elements
      x = rows[i].getElementsByTagName("TD")[columnIndex].textContent.trim();
      y = rows[i + 1].getElementsByTagName("TD")[columnIndex].textContent.trim();

      // Check if the two rows should switch place, based on the direction
      if (direction === "asc") {
        if (x.toLowerCase() > y.toLowerCase()) {
          shouldSwitch = true;
          break;
        }
      } else if (direction === "desc") {
        if (x.toLowerCase() < y.toLowerCase()) {
          shouldSwitch = true;
          break;
        }
      }
    }

    if (shouldSwitch) {
      // Perform the switch and mark switching as true to continue looping
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      switchCount++;
    } else {
      // If no switch was made and direction is "asc", switch to "desc" and repeat
      if (switchCount === 0 && direction === "asc") {
        direction = "desc";
        switching = true;
      }
    }
  }
}


