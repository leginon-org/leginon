
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

var path = "img/";
open_off=new Image();
open_off.src=path+"open_off.gif";
open_on=new Image();
open_on.src=path+"open_on.gif";

close_off=new Image();
close_off.src=path+"close_off.gif";
close_on=new Image();
close_on.src=path+"close_on.gif";

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

var v1target_bt=false;
var v2target_bt=false;
var mvtarget_bt=false;

var v1scale_bt=false;
var v2scale_bt=false;
var mvscale_bt=false;


function imageon(imagename, name, type) {
	document.images[eval("\"" + imagename + "\"")].src = eval(name+type+"_on.src");
	eval(imagename+'=true');
}

function imageoff(imagename, name, type) {
	document.images[eval("\"" + imagename + "\"")].src = eval(name+type+"_off.src");
	eval(imagename+'=false');
}

function toggleimage(imagename, name) {
	imagenamestr = document.images[eval("\"" + imagename + "\"")].src;
	if (imagenamestr.search('_on') != -1)
		imageoff(imagename, name, '');
	else if (imagenamestr.search('_off') != -1)
		imageon(imagename, name, '');
}

function imageonfocus(imagename, name, type) {
	imagenamestr = document.images[eval("\"" + imagename + "\"")].src;
	if (imagenamestr.search('_on') != -1)
		imageon(imagename, name, type);
	else if (imagenamestr.search('_off') != -1)
		imageoff(imagename, name, type);
}

function MsgBox (textstring) {
	alert (textstring)
}

function setlist()
{
	if (jsmvId.length != 0){
		var selm=document.listform.mlist.options[document.listform.mlist.selectedIndex].value;
		window.document.listform.mvsel.value=selm;
	} if (window.document.listform.v2view.value=='on') {
		var sel2=document.listform.v2list.options[document.listform.v2list.selectedIndex].value;
		window.document.listform.v2sel.value=sel2;
	} if (window.document.listform.v1view.value=='on') {
		var sel1=document.listform.v1list.options[document.listform.v1list.selectedIndex].value;
		window.document.listform.v1sel.value=sel1;
	}
}

function setview(view, state) {
	if (view=="v1")
		window.document.listform.v1view.value=state;
	if (view=="v2")
		window.document.listform.v2view.value=state;
}

function popUpMap(URL)
{
  window.open(URL, 'map', 'left=0,top=0,height=256,width=256,toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes');
}

function popUp(URL)
{
  window.open(URL, '', 'toolbar=0,scrollbars=1,location=0,statusbar=0,menubar=0,resizable=1');
}

function newexp()
{
    window.document.listform.submit(); 
    return true;
}

function newenterfile()
{
     var currentfile=window.document.listform.filename_text.value;
     for (var i = 0; i < document.listform.allfile.length; i++) {
      if (document.listform.allfile.options[i].text == currentfile) {
       var index=i;
      }
     }
       document.listform.allfile.options[index].selected=true;
}

function browser()
{
	var _b = "";
	var _ns_vers = parseInt(navigator.appVersion);
	var _info = navigator.userAgent; var _ns = false;
	var _ie = (_info.indexOf("MSIE") > 0 && _info.indexOf("Win") > 0 && _info.indexOf("Windows 3.1") < 0);
	var _ns = (navigator.appName.indexOf("Netscape") >= 0 && ((_info.indexOf("Win") > 0 && _info.indexOf("Win16") < 0 && java.lang.System.getProperty("os.version").indexOf("3.5") < 0) || (_info.indexOf("Sun") > 0) || (_info.indexOf("Linux") > 0)));
	var _ns6 = ( _ns && (_ns_vers >= 5));
	var _ns4 = ( _ns && (_ns_vers == 4));
	var _opera = (_info.indexOf("Opera") != -1);


	if (_ie == true) {
		_b = "ie";
	} else if (_ns4 == true) {
		_b = "ns4";
	} else if (_ns6 == true) {
		_b = "ns6";
	} else if (_opera == true) {
		_b = "opera";
	}
	return _b;
}

function updatePreset(file)
{
	if (browser() == "ns4") {	
	var i = 0;
	var datafile = window.location.href.substring(0, window.location.href.lastIndexOf("/") + 1) + file;
	var url = new java.net.URL(datafile);
	var connect = url.openConnection();
	var input = new java.io.BufferedReader( new java.io.InputStreamReader(connect.getInputStream()));
	var row = "";
	var data = "";
	while((row = input.readLine()) != null) {
		data += row;
	}
	return data;
	}
}

function GetPresets()
{
	jsfexp=	document.listform.allfile.options[document.
		listform.allfile.selectedIndex].value;

	if (browser() == "ns4") {	
		if (jspremv == 1){
		var presets = updatePreset('getpreset.php?fileId='+jsfexp+'&p='+jsprefId+'&f='+jstmv);
		window.document.listform.Premv.value=presets;
		}
		if (jsprev1 == 1){
		var presets = updatePreset('getpreset.php?fileId='+jsfexp+'&p='+jsprefId+'&f='+jstv1+'&v=1');
		window.document.listform.Prev1.value=presets;
		}
		if (jsprev2 == 1){
		var presets = updatePreset('getpreset.php?fileId='+jsfexp+'&p='+jsprefId+'&f='+jstv2+'&v=2');
		window.document.listform.Prev2.value=presets;
		}

	} else {
		if (jspremv == 1){
		var mvpre=document.listform.mlist.options[document.listform.mlist.selectedIndex].value;
		var URL = 'getpreset.php?id='+jsfexp+'&preset='+mvpre;
		ifmv.document.location.replace(URL);
		}
		if (jsprev1 == 1){
		var v1pre=document.listform.v1list.options[document.listform.v1list.selectedIndex].value;
		var URL = 'getpreset.php?id='+jsfexp+'&preset='+v1pre+'&vf=1';
		ifv1.document.location.replace(URL);
		}
		if (jsprev2 == 1){
		var v2pre=document.listform.v2list.options[document.listform.v2list.selectedIndex].value;
		var URL = 'getpreset.php?id='+jsfexp+'&preset='+v2pre+'&vf=1';
		ifv2.document.location.replace(URL);
		}
	}
}

function FocFile()
{
     window.document.listform.filename_text.focus();
}

function GetComment()
{
    jsIndex=document.listform.allfile.options.selectedIndex;

    window.document.listform.Comment.value = jsComment[jsIndex]; 
    if (jsCType[jsIndex]=="") {
      window.document.listform.Type[0].checked=false 
      window.document.listform.Type[1].checked=false 
      window.document.listform.Type[2].checked=false 
    }
    else if (jsCType[jsIndex]==1) {
      window.document.listform.Type[0].checked=true 
    }
    else if (jsCType[jsIndex]==2) {
      window.document.listform.Type[1].checked=true 
    }
    else if (jsCType[jsIndex]==3) {
      window.document.listform.Type[2].checked=true 
    }
 
}

function GetLinkId(lk) {
	var Id = -1;
	for (var i=0; i<document.links.length; i++) {
		if(document.links[i].toString().search(lk) != -1){ 
			Id = i;
		}
	}
	return Id;
}

function downloadfile()
{
	jsfexp=document.listform.allfile.options[document.
		listform.allfile.selectedIndex].value
	window.location="download.php?sessionId="+jsexpId+"&fileId="+jsfexp+"&r=1"; 
}

function newfilefil() 
    { 
     currentfile=document.listform.allfile.options[document.
     listform.allfile.selectedIndex].text
     window.document.listform.filename_text.value=currentfile; 
     jsfexp=document.listform.allfile.options[document.
     listform.allfile.selectedIndex].value
     document.newimg1.src=jsimgmv+"?table=AcquisitionImageData&expId="+jsexpId+"&fileId="+jsfexp+"&s=256"; 
     document.links[1].href="javascript:popUp('nw.php?tmpl="+jsimgmv+"&expId="+jsexpId+"&fileId="+jsfexp+"&r=1&s="+jssession+"')"; 
}

function newfile() 
    { 
     currentfile=document.listform.allfile.options[document.
     listform.allfile.selectedIndex].text
     window.document.listform.filename_text.value=currentfile; 
     jsfexp=document.listform.allfile.options[document.
     listform.allfile.selectedIndex].value
	var lId;
	if (jsmvId.length != 0){
		if (mvscale_bt) mvsb="&sb=1"; else mvsb="";
		if (mvtarget_bt) mvtg="&tg=1"; else mvtg="";
		var mvpre=document.listform.mlist.options[document.listform.mlist.selectedIndex].value;
		document.newimgmv.src=jsimgmv+"?Lmv=1&preset="+mvpre+"&session="+jsexpId+"&id="+jsfexp+"&s=512&t=80"+mvtg+mvsb; 
		
		lId=GetLinkId('Lmv');
		if ((lId=GetLinkId('Lmv')) != -1 ) {
		document.links[lId].href="javascript:popUpMap('map.php?Lmv=1&preset="+mvpre+"&session="+jsexpId+"&id="+jsfexp+mvtg+mvsb+"')"; 
		}
	} if (window.document.listform.v1view.value=='on') {
		if (v1scale_bt) v1sb="&sb=1"; else v1sb="";
		if (v1target_bt) v1tg="&tg=1"; else v1tg="";
		var v1pre=document.listform.v1list.options[document.listform.v1list.selectedIndex].value;
		document.newimgview1.src=jsimgv1+"?Lv1=1&preset="+v1pre+"&session="+jsexpId+"&id="+jsfexp+"&s=256&t=80"+v1tg+v1sb; 
		if ((lId=GetLinkId('Lv1')) != -1 ) {
		document.links[lId].href="javascript:popUpMap('map.php?Lv1=1&preset="+v1pre+"&session="+jsexpId+"&id="+jsfexp+v1tg+v1sb+"')"; 
		}
	} if (window.document.listform.v2view.value=='on') {
		if (v2scale_bt) v2sb="&sb=1"; else v2sb="";
		if (v2target_bt) v2tg="&tg=1"; else v2tg="";
		var v2pre=document.listform.v2list.options[document.listform.v2list.selectedIndex].value;
		document.newimgview2.src=jsimgv2+"?Lv2=1&preset="+v2pre+"&session="+jsexpId+"&id="+jsfexp+"&s=256&t=80"+v2tg+v2sb; 
		if ((lId=GetLinkId('Lv2')) != -1 ) {
		document.links[lId].href="javascript:popUpMap('map.php?Lv2=1&preset="+v2pre+"&session="+jsexpId+"&id="+jsfexp+v2tg+v2sb+"')"; 
		}
	}
}

function sendForm(name, pID) {
    jsfexp=document.listform.allfile.options[document.
    listform.allfile.selectedIndex].value;
    document.listform.action = name+"?"+pID+"="+jsprefId;
    return true;
}

function checkData() {
	if (jsName.length == 0) {
		alert("Enter a Name");
		return false;
	} else {
    		jsfexp=document.listform.allfile.options[document.
    		listform.allfile.selectedIndex].value;
		document.listform.ncfid.value=jsfexp;
		window.document.listform.submit(); 
		return true;
	}
}
  
function incIndex(){
 if (document.listform.allfile.length !=0) {
     for (var i = 0; i < document.listform.allfile.length; i++) {
      if (document.listform.allfile.options[i].selected == true) {
       index=i  
      } 
     }
     if (index == document.listform.allfile.length - 1) {
 	index = index-1
     }	
     document.listform.allfile.options[index+1].selected=true;
 }
}


function decIndex(){
 if (document.listform.allfile.length !=0) {
     for (var i = 0; i < document.listform.allfile.length; i++) {
      if (document.listform.allfile.options[i].selected == true) {
       index=i  
      } 
     }
     if (index == 0) {
 	index = index+1
     }	
     document.listform.allfile.options[(index-1)].selected=true;
 }
}
