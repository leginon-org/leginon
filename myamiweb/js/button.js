/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

var path = 'img/';

function imageon(imagename, name, type) {
	if (cimg=document.images[eval("\"" + imagename + "\"")])
		cimg.src = eval(name+type+"_on.src");
	eval(imagename+"_st=true");
}

function imageoff(imagename, name, type) {
	if (cimg=document.images[eval("\"" + imagename + "\"")])
		cimg.src = eval(name+type+"_off.src");
	eval(imagename+"_st=false");
}

function toggleimage(imagename, name) {
	var state=""; 	
	if (!document.images[eval("\"" + imagename + "\"")])  {
		eval(imagename+"_st=true");
		return "on";
	}
	imagenamestr = document.images[eval("\"" + imagename + "\"")].src;
	if (imagenamestr.search("_on") != -1) {
		imageoff(imagename, name, "");
		state="off"; 
	} else if (imagenamestr.search("_off") != -1) {
		imageon(imagename, name, "");
		state="on"; 
	}
	return state;
}

function setToggleButton(imagename, name, state) {
	if (state=="on") {
		imageon(imagename, name, "");
	}
	if (state=="off") {
		imageoff(imagename, name, "");
	}
}

function setstate(imagename, name) {
	st = eval(name + "_st");
	if (st) {
		imageoff(imagename, name, "");
		eval(name + "_st=false");
	} else {
		imageon(imagename, name, "");
		eval(name + "_st=true");
	}
}

function imageonfocus(imagename, name, type) {
	imagenamestr = document.images[eval("\"" + imagename + "\"")].src;
	if (imagenamestr.search("_on") != -1)
		imageon(imagename, name, type);
	else if (imagenamestr.search("_off") != -1)
		imageoff(imagename, name, type);
}
