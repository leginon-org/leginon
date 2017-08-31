/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

function update_data() {
	document.data.bt_action.value="get";
	submit_data();
}

function check_name() {
	document.data.bt_action.value="";
	document.data.submit();
}

function confirm_add() {
	document.data.bt_action.value="add";
	document.data.submit();
}

function confirm_update() {
	document.data.bt_action.value="save";
	document.data.submit();
}

function confirm_delete() {
	document.data.bt_action.value="remove";
	document.data.submit();
}

function submit_data() {
	document.data.submit();
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
