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

function imageon(imagename, name, type) {
	document.images[eval("\"" + imagename + "\"")].src = eval(name+type+"_on.src");
	eval(imagename+"_st=true");
}

function imageoff(imagename, name, type) {
	document.images[eval("\"" + imagename + "\"")].src = eval(name+type+"_off.src");
	eval(imagename+"_st=false");
}

function toggleimage(imagename, name) {
	var state=""; 	imagenamestr = document.images[eval("\"" + imagename + "\"")].src;
	if (imagenamestr.search("_on") != -1) {
		imageoff(imagename, name, "");
		state="off"; 
	} else if (imagenamestr.search("_off") != -1) {
		imageon(imagename, name, "");
		state="on"; 
	}
	return state;
}

function setimgId() {
	jsindex = document.viewerform.imageId.selectedIndex; 
	if (jsindex < 0) {
		jsindex=0; 
		document.viewerform.imageId.options[0].selected=true; 
	} 
	jsimgId = document.viewerform.imageId.options[jsindex].value; 
}

function imageonfocus(imagename, name, type) {
	imagenamestr = document.images[eval("\"" + imagename + "\"")].src;
	if (imagenamestr.search("_on") != -1)
		imageon(imagename, name, type);
	else if (imagenamestr.search("_off") != -1)
		imageoff(imagename, name, type);
}

function setview(view, state) {
	if (state=="on") 
		state="off"; 
	else 
		state="on"; 
	eval("window.document.viewerform."+view+".value=state");
}

function newexp() {
    window.document.viewerform.submit(); 
    return true;
}

function newfile(view){
	jssize = eval(view+"size");
	jsvfile = eval("jsvfile"+view);
	selpreset = "";
	
	if (list = eval("document.viewerform."+view+"pre"))
		selpreset=list.options[list.selectedIndex].value;

	if (prem = eval("document.viewerform."+view+"prem"))
		if (list)
			prem.value = selpreset;

	if (eval(view+"fft_bt_st")) fft="&fft=1"; else fft="";
	if (eval(view+"scale_bt_st")) sb="&sb=1"; else sb="";
	if (eval(view+"target_bt_st")) tg="&tg=1"; else tg="";
	if (cmin = eval("jsmin"+view)) np="&np="+cmin; else np="";
	if (cmax = eval("jsmax"+view)) xp="&xp="+cmax; else xp="";

	options = "preset="+selpreset+
		"&session="+jsSessionId+
		"&id="+jsimgId+
		"&s="+jssize+"&t=80"+tg+sb+fft+np+xp;

	ni = "getparentimgtarget.php?"+options;
	nlink = "javascript:popUpMap('map.php?"+options+"')";

	if (img = document.images[eval("\"" +view+ "img\"")]) 
		img.src = ni;
	if (link = document.getElementById(view+"href"))
		link.href = nlink;

	if (cif=eval("this."+view+"if")) {
		iflink = "getpreset.php?vf="+jsvfile+"&id="+jsimgId+"preset="+selpreset;
		cif.document.location.replace(iflink);
	}

}

function setminmax(viewname, min,max) {
	eval("jsmin"+viewname+"="+min);
	eval("jsmax"+viewname+"="+max);
}

function popUpMap(URL)
{
	window.open(URL, "map", "left=0,top=0,height=256,width=256,toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes");
}

function popUpAdjust(URL, view, param){
	min = eval("jsmin"+view);
	max = eval("jsmax"+view);
	min = (min) ? "&pmin="+min : "";
	max = (max) ? "&pmax="+max : "";
	param = (param) ? param : "left=0,top=0,height=35,width=370";
	window.open(URL+min+max, view+"adj", param+",toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes");
}
