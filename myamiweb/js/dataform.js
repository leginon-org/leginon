/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

function update_userdata() {
	document.f_userdata.bt_action.value="get";
	submit_userdata();
}

function check_name() {
	document.f_userdata.bt_action.value="";
	document.f_userdata.submit();
}

function confirm_update() {
	document.f_userdata.bt_action.value="save";
	document.f_userdata.submit();
}
function confirm_delete() {
	document.f_userdata.bt_action.value="remove";
	document.f_userdata.submit();
}

function submit_userdata() {
	document.f_userdata.submit();
}

function getStyleObject(objectId) {
    // cross-browser function to get an object's style object given its
    if(document.getElementById && document.getElementById(objectId)) {
        // W3C DOM
        return document.getElementById(objectId).style;
    } else if (document.all && document.all(objectId)) {
        // MSIE 4 DOM
        return document.all(objectId).style;
    } else if (document.layers && document.layers[objectId]) {
        // NN 4 DOM.. note: this won't find nested layers
        return document.layers[objectId];
    } else {
        return false;
    }
}
