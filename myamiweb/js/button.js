/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

var path = 'img/';
close_bt_off=new Image();
close_bt_off.src=path+"close_bt_off.gif";
close_bt_over_off=new Image();
close_bt_over_off.src=path+"close_bt_over_off.gif";
close_bt_on=new Image();
close_bt_on.src=path+"close_bt_on.gif";
close_bt_over_on=new Image();
close_bt_over_on.src=path+"close_bt_over_on.gif";

target_bt_off=new Image();
target_bt_off.src=path+"target_bt_off.gif";
target_bt_over_off=new Image();
target_bt_over_off.src=path+"target_bt_over_off.gif";
target_bt_on=new Image();
target_bt_on.src=path+"target_bt_on.gif";
target_bt_over_on=new Image();
target_bt_over_on.src=path+"target_bt_over_on.gif";

scale_bt_off=new Image();
scale_bt_off.src=path+"scale_bt_off.gif";
scale_bt_on=new Image();
scale_bt_on.src=path+"scale_bt_on.gif";
scale_bt_over_off=new Image();
scale_bt_over_off.src=path+"scale_bt_over_off.gif";
scale_bt_over_on=new Image();
scale_bt_over_on.src=path+"scale_bt_over_on.gif";

fft_bt_off=new Image();
fft_bt_off.src=path+"fft_bt_off.gif";
fft_bt_on=new Image();
fft_bt_on.src=path+"fft_bt_on.gif";
fft_bt_over_off=new Image();
fft_bt_over_off.src=path+"fft_bt_over_off.gif";
fft_bt_over_on=new Image();
fft_bt_over_on.src=path+"fft_bt_over_on.gif";

filter_bt_off=new Image();
filter_bt_off.src=path+"filter_bt_off.gif";
filter_bt_on=new Image();
filter_bt_on.src=path+"filter_bt_on.gif";
filter_bt_over_off=new Image();
filter_bt_over_off.src=path+"filter_bt_over_off.gif";
filter_bt_over_on=new Image();
filter_bt_over_on.src=path+"filter_bt_over_on.gif";

function imageon(imagename, name, type) {
	document.images[eval("\"" + imagename + "\"")].src = eval(name+type+"_on.src");
	eval(imagename+"_st=true");
}

function imageoff(imagename, name, type) {
	document.images[eval("\"" + imagename + "\"")].src = eval(name+type+"_off.src");
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

function imageonfocus(imagename, name, type) {
	imagenamestr = document.images[eval("\"" + imagename + "\"")].src;
	if (imagenamestr.search("_on") != -1)
		imageon(imagename, name, type);
	else if (imagenamestr.search("_off") != -1)
		imageoff(imagename, name, type);
}
