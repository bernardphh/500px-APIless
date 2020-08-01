// dynamic_menu_template.js.
// The python script will generate a js similar to this, with the name dynamic_menu_[user name].js
// It will fill in the result html file name when a task is done.
// This js is used on  the main html file that hosts all the result html files.
jQuery(document).ready(function() {
    var active_html_file = ""
    var active_menu_item = ""
	"
    var main_container_ele = document.getElementById("div_main_content")
    // associate menu items (csv_type.name) with html files by using an array of objects
    // this js file is generated when the user wants to update the main html file
    var menu_items =[
		{ "item" : "user_summary",
		  "file" : ""
		},
		{ "item" : "photos_public",
		  "file" : ""
		},
		{ "item" : "followers",
		  "file" : ""
		},
		{ "item" : "followings",
		  "file" : ""
		},
		{ "item" : "reciprocal",
		  "file" : ""
		},
		{ "item" : "not_follow",
		  "file" : ""
		},
		{ "item" : "following",
		  "file" : ""
		},
		{ "item" : "all_users",
		  "file" : ""
		},
		{ "item" : "like_actors",
		  "file" : ""
		},
		{ "item" : "notifications",
		  "file" : ""
		},
		{ "item" : "unique_users",
		  "file" : ""
		},
		{ "item" : "all_notifications",
		  "file" : ""
		},
		{ "item" : "all_unique_users",
		  "file" : ""
		}
	]
	menu_items.forEach(add_listeners);
	
	//--------------------------------------------------------------------------
	//for dynamic menu items: gray out text of un-available menu items, add click event listener
	function add_listeners(menu_item) {
		var ele = document.getElementById(menu_item.item)
		if (menu_item.file == ""){
			// add css class to change text color (gray out)
			ele.classList += " inactive_menu" ;
		}
		else{
			// remove class to restore the normal text color
			ele.classList.remove("inactive_menu");	
		    // add event listener 
		    ele.addEventListener("click", function(){
			    switch_page(menu_item.file, menu_item.item, main_container_ele)
		    });				
	    }				
    }
	//--------------------------------------------------------------------------   
	// assign class to elements (identified by tag names), depending on its indexes
	// this means to set background colors for different menu items depending on its group	
    function reset_default_menu_bg_colors(tag_name){
		var li_eles = document.getElementsByTagName(tag_name);
		var i;
		for (i = 0; i < li_eles.length; i++) {
			if (i >= 2 && i <= 7){
				li_eles[i].classList += ' users_group';				
			}
			else if ( i >= 9 && i <= 12 ){
				li_eles[i].classList += ' notifications_group';				
			}
			else{
				li_eles[i].classList += ' other_group';	
			}
		}	
	}	
	//--------------------------------------------------------------------------    
    // set main html object, handle menu items background colors and update global variables	
	function switch_page(active_html_file, active_menu_item, main_container_ele){
		// replace the main html object
        if (active_html_file != ""){ 
		    new_inner_HTML = `<object type="text/html" data="${active_html_file}" width="100%" height="100%" "></object>`
		    main_container_ele.innerHTML = new_inner_HTML;
        }		
		reset_default_menu_bg_colors('li');
		
		// set the background of the active item 
		var ele = document.getElementById(active_menu_item);		
		ele.className = '';		
		ele.classList += ' active_menu'
		
		// update the global variables
		window.active_html_file = active_html_file;
		window.active_menu_item = active_menu_item;
	};	
	//--------------------------------------------------------------------------
	// load the main object on page load or on refresh
    if (active_html_file != "" &&  active_menu_item != ""){
	    switch_page(active_html_file, active_menu_item, main_container_ele)	
    }	
}); 