/* Highly customized sorting function for table. Three sorting options for a column, depending on  the argument special_sort:
   1. sortByDisplayName: 					 By the text of "a" tag in the second "div" tag (special_sort=sortByDisplayName")
   2. sortByPhotoTitle:  					 By the innerHTML of the second "div" tag    
   3. undefined or anything but (1) and (2): By the innerHTML of the "td" tag  
*/
function sortTable(columnIndex, special_sort) {
   var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementsByTagName("table")[0] /* targer the first table instead of table with id-- getElementById("myTable"); */
    switching = true;
    dir = "asc";
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
			      x = rows[i].getElementsByTagName("TD")[columnIndex];
            y = rows[i + 1].getElementsByTagName("TD")[columnIndex];
			
            if (special_sort == "sortByDisplayName"){
			         x =x.getElementsByTagName("DIV")[1].getElementsByTagName("a")[0].text; 
			         y =y.getElementsByTagName("DIV")[1].getElementsByTagName("a")[0].text; 
            }
			      else if (special_sort == "sortByPhotoTitle"){
			         x =x.getElementsByTagName("DIV")[1].innerHTML 
			         y =y.getElementsByTagName("DIV")[1].innerHTML 
            }
			else
			{
				x = x.innerHTML;
				y = y.innerHTML;		    		
			}
 		    if (x == "" && y != "" && dir == "asc"){
		        shouldSwitch = true;	
			    break;
		    }	  
		    if (y == "" && x != ""  && dir == "desc"){
		        shouldSwitch = true;
			    break;
		    }	           
		    var xContent = (isNaN(x))
                ? ((x.toLowerCase() === "-")? 0 : x.toLowerCase() )
                : parseFloat(x);
            var yContent = (isNaN(y))
                ? ((y.toLowerCase() === "-")? 0 : y.toLowerCase() )
                : parseFloat(y);			  
            if (dir == "asc") {
                if (xContent > yContent) {
                    shouldSwitch= true;
                    break;
                }
            } else if (dir == "desc") {
                if (xContent < yContent) {
                    shouldSwitch= true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount ++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
	    if (dir == "asc") {
		    document.getElementById("arrow-down-" + columnIndex ).style.display = "none";
		    document.getElementById("arrow-up-" + columnIndex ).style.display = "block";
	    }
	    else {
		    document.getElementById("arrow-up-" + columnIndex).style.display = "none";
		    document.getElementById("arrow-down-" + columnIndex).style.display = "block";	  
	    }
    }
	var num_cols = table.rows[0].cells.length;	
	for ( i=0; i < num_cols; i++) {
		if ( i != columnIndex) {
			document.getElementById("arrow-up-" + i).style.display = "block";
			document.getElementById("arrow-down-" + i).style.display = "block";				
		}
	}	   	   	
}