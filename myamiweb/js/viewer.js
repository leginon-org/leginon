/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */


function setevents()
{
	if (obj=document.viewerform.imageId) {
	     obj.onkeyup   = checkevents;
	     obj.onkeydown = checkevents;
	     obj.onchange  = checkevents;
	}
} 

function checkevents(e)
{
	var code;
	if (!e) var e = window.event;
	if (e.keyCode) code = e.keyCode;
	else if (e.which) code = e.which;
	if (code == key_down_unicode || code == key_up_unicode)  {
		if (e.type == eventdown) {
			keydown=true;
			stopInterval();
		} else if (e.type == eventup) {
			startInterval();
			keydown=false;
		}
	} else if (e.type == eventchange && !keydown) {
			updateviews();
	}
}

function startInterval()
{
	begin = new Date();
	interval = window.setInterval("trigger()",10);
}

function stopInterval()
{
    window.clearInterval (interval);
    interval="";
}

function trigger()
{
	end = new Date();
	diff = end-begin;
	// --- if key released at least for 150ms
	// --- then triggered his action 
	if (diff > 150) {
		stopInterval();
		// --- action
		updateviews();
	}
	
}

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

function addComment() {
	name = document.viewerform.name.value;
	comment = document.viewerform.comment.value;
	url = "addcomment.php?sessionId="+jsSessionId+"&imageId="+jsimgId+"&name="+escape(name)+"&comment="+escape(comment);
	if (img = document.images[eval("\"commentimg\"")]) 
		img.src = url;

	if (commentdivstyle = document.getElementById("commentdiv").style) {
		commentdivstyle.visibility = 'visible';
		setTimeout("commentdivstyle.visibility = 'hidden'; img.src = 'addcomment.php'", 1500);
	}
}

var lastoptions = new Array();
function newfile(view){
	jssize = eval(view+"size");
	jsvfile = eval("jsvfile"+view);
	selpreset = eval("jspreset"+view);
	jsimagescriptcur = eval("jsimagescript"+view);
	jspresetscriptcur = eval("jspresetscript"+view);
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
	if (cbinning = eval("jsbinning"+view)) binning="&binning="+cbinning; else binning="";
	if (cquality = eval("jsquality"+view)) quality="&t="+cquality; else quality="";
	if (ccolormap= eval("jscolormap"+view)) colormap="&colormap="+ccolormap; else colormap="";

	options = "preset="+selpreset+
		"&session="+jsSessionId+
		"&id="+jsimgId+
		"&s="+jssize+quality+tg+sb+fft+np+xp+flt+binning+colormap;

	if (options == lastoptions[vid])
		return;


	ni = jsimagescriptcur+"?"+options;
	nlink = "javascript:popUpMap('map.php?"+options+"')";
	ninfolink = "imgreport.php?id="+jsimgId+"&preset="+selpreset;
	ndownloadlink = "download.php?id="+jsimgId+"&preset="+selpreset+fft;

	if (img = document.images[eval("\"" +view+ "img\"")]) 
		img.src = ni;
	if (link = document.getElementById(view+"href"))
		link.href = nlink;
	if (infolink = document.getElementById("info"+view+"_bthref"))
		infolink.href = ninfolink;
	if (downloadlink = document.getElementById("download"+view+"_bthref"))
		downloadlink.href = ndownloadlink;

	if (cif=eval("this."+view+"if")) {
		iflink = jspresetscriptcur+"?vf="+jsvfile+"&id="+jsimgId+"&preset="+selpreset;
		cif.document.location.replace(iflink);
	}

	lastoptions[vid] = options;
}

function toggleButton(imagename, name) {
	state = toggleimage(imagename, name);
	if (m = eval("document.viewerform."+imagename+"_st")) {
		m.value=state;
		displaydebug(m.value);
	}
	return state;
}

function setImageStatus(viewname) {
	if (ccolormap= eval("jscolormap"+viewname)) colormap="&colormap="+ccolormap; else colormap="";
	if (cmin = eval("jsmin"+viewname)) np="&min="+cmin; else np="";
	if (cmax = eval("jsmax"+viewname)) xp="&max="+cmax; else xp="";
	options = np+xp+colormap;
	if (img = document.images[eval("\"" +viewname+ "imgstatgrad\"")]) 
		img.src = 'img/dfe/grad.php?h=10&w=40'+options;
	filter = eval("jsfilter"+viewname);
	binning = eval("jsbinning"+viewname);
	quality = eval("jsquality"+viewname);
	quality = (isNaN(quality)) ? quality : "jpg"+quality;
	newstatus = " filter:"+filter+" bin:"+binning+" "+quality;
	if (imgstatus = document.getElementById(viewname+"imgstat")) {
		imgstatus.childNodes[0].nodeValue = newstatus;
	}
}

function setminmax(viewname, min,max) {
	eval("jsmin"+viewname+"="+min);
	eval("jsmax"+viewname+"="+max);
	if (m = eval("document.viewerform."+viewname+"minpix")) {
		m.value=min;
	}
	if (x = eval("document.viewerform."+viewname+"maxpix")) {
		x.value=max;
	}
}

function setcolormap(viewname, colormap) {
	eval("jscolormap"+viewname+"="+colormap);
	if (cm = eval("document.viewerform."+viewname+"cm")) {
		cm.value=colormap;
	}
}

function setquality(viewname, quality) {
	eval('jsquality'+viewname+'="'+quality+'"');
	if (q = eval("document.viewerform."+viewname+"q")) {
		q.value=quality;
	}
}

function displaydebug(string) {
	cur = document.viewerform.debug.value;
	document.viewerform.debug.value= cur+"\n"+string;
}



function setfilter(viewname, filter) {
	eval("jsfilter"+viewname+"='"+filter+"'");
	if (f = eval("document.viewerform."+viewname+"f")) {
		f.value=filter;
	}
}

function setbinning(viewname, binning) {
	eval("jsbinning"+viewname+"='"+binning+"'");
	if (b = eval("document.viewerform."+viewname+"b")) {
		b.value=binning;
	}
}

function popUpMap(URL)
{
	window.open(URL, "map", "left=0,top=0,height=256,width=256,toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes");
}

function popUpAdjust(URL, view, param){
	min = eval("jsmin"+view);
	max = eval("jsmax"+view);
	filter = eval("jsfilter"+view);
	binning = eval("jsbinning"+view);
	quality = eval("jsquality"+view);
	colormap = eval("jscolormap"+view);
	min = (min) ? "&pmin="+min : "";
	max = (max) ? "&pmax="+max : "";
	filter = (filter) ? "&filter="+filter : "";
	binning = (binning) ? "&binning="+binning : "";
	quality = (quality) ? "&t="+quality : "";
	colormap= (colormap) ? "&colormap="+colormap : "";
	param = (param) ? param : "left=0,top=0,height=35,width=370";
	window.open(URL+min+max+filter+binning+quality+colormap, view+"adj", param+",toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes");
}
