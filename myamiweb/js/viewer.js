/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

function setimgId() {
	if (obj=document.viewerform.imageId) {
	jsindex = obj.selectedIndex; 
	if (jsindex < 0) {
		jsindex=0; 
		obj.options[0].selected=true; 
	} 
	jsimgId = obj.options[jsindex].value; 
	}
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

function getviewindex(name) {
	index=0;
	for (var i in jsviews) {
		if (jsviews[i] == name) {
			index=i;
			break;
		}
	}
	return index;
}


var lastoptions = new Array();
function newfile(view){
	jssize = eval(view+"size");
	jsvfile = eval("jsvfile"+view);
	selpreset = "";
	vid = getviewindex(view);
	
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
	if ((cfilter = eval("jsfilter"+view)) && eval(view+"filter_bt_st")) flt="&flt="+cfilter; else flt="";

	options = "preset="+selpreset+
		"&session="+jsSessionId+
		"&id="+jsimgId+
		"&s="+jssize+"&t=80"+tg+sb+fft+np+xp+flt;

	if (options == lastoptions[vid])
		return;


	ni = "getparentimgtarget.php?"+options;
	nlink = "javascript:popUpMap('map.php?"+options+"')";
	ninfolink = "imgreport.php?id="+jsimgId+"&preset="+selpreset;

	if (img = document.images[eval("\"" +view+ "img\"")]) 
		img.src = ni;
	if (link = document.getElementById(view+"href"))
		link.href = nlink;
	if (infolink = document.getElementById("info"+view+"_bthref"))
		infolink.href = ninfolink;

	if (cif=eval("this."+view+"if")) {
		iflink = "getpreset.php?vf="+jsvfile+"&id="+jsimgId+"&preset="+selpreset;
		cif.document.location.replace(iflink);
	}

	lastoptions[vid] = options;

}

function setminmax(viewname, min,max) {
	eval("jsmin"+viewname+"="+min);
	eval("jsmax"+viewname+"="+max);
}

function setfilter(viewname, filter) {
	eval("jsfilter"+viewname+"='"+filter+"'");
}

function popUpMap(URL)
{
	window.open(URL, "map", "left=0,top=0,height=256,width=256,toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes");
}

function popUpAdjust(URL, view, param){
	min = eval("jsmin"+view);
	max = eval("jsmax"+view);
	filter = eval("jsfilter"+view);
	min = (min) ? "&pmin="+min : "";
	max = (max) ? "&pmax="+max : "";
	filter = (filter) ? "&filter="+filter : "";
	param = (param) ? param : "left=0,top=0,height=35,width=370";
	window.open(URL+min+max+filter, view+"adj", param+",toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes");
}
