// handle_tables.js:
// toogle table visibility by clicking on the table description headline
// hide the un-important tables initially, at page load

// tables elements
var desc_table = document.getElementById("description")
var overview_table = document.getElementById("overview")
var top_photos_table = document.getElementById("top_photos")
var photos_unlisted_table = document.getElementById("photos_unlisted")
var photos_limited_access_table = document.getElementById("photos_limited_access")

// headline elements
var desc_headline = document.getElementById("desc_headline")
var overview_headline = document.getElementById("overview_headline")
var top_photos_header = document.getElementById("top_photos_headline")
var photos_unlisted_headline = document.getElementById("photos_unlisted_headline")
var photos_limited_access_headline = document.getElementById("photos_limited_access_headline")

// initially, hide unimportant tables
desc_table.style.display = "none";
if (overview_table != null) {
	overview_table.style.display = "none";
}
if (top_photos_table != null) {
	top_photos_table.style.display = "none";
}
if (photos_unlisted_table != null) {
	photos_unlisted_table.style.display = "none";
}
if (photos_limited_access_table != null) {
	photos_limited_access_table.style.display = "none";
}

// add Click event listener to headline elements
if (desc_headline != null) {
	desc_headline.addEventListener("click", function(){	toggle_table_visibility(desc_table, this)});
}
if (overview_headline != null) {
	overview_headline.addEventListener("click", function(){	toggle_table_visibility(overview_table, this)});
}
if (top_photos_header!= null) {
	top_photos_header.addEventListener("click", function(){	toggle_table_visibility(top_photos_table, this)});
}
if (photos_unlisted_headline != null) {
	photos_unlisted_headline.addEventListener("click", function(){	toggle_table_visibility(photos_unlisted_table, this)});
}
if (photos_limited_access_headline != null) {
	photos_limited_access_headline.addEventListener("click", function(){toggle_table_visibility(photos_limited_access_table, this)});
}

// show/hide the given table and change its headline direction arrow accordingly
function toggle_table_visibility(table_ele, header_ele){
    var curr_state = table_ele.style.display;
    if (curr_state === "none" ) {
		table_ele.style.display = "inline-block";
		header_ele.innerHTML = header_ele.innerHTML.replace("\u21E9","\u21E7" );
    }
	else{
		table_ele.style.display = "none";	   		
		header_ele.innerHTML = header_ele.innerHTML.replace("\u21E7", "\u21E9");		
	}
};

