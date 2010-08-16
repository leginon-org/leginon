function GetDowStart() {return 0;}function GetDateFmt() {return "mmddyy";}function GetDateSep() {return "/";}
function ShowCalendar(eP,eD,eDP,dmin,dmax)
{
	SCal(eP,eD,eDP,dmin,dmax);
}
function ShowCalSimp(fm,eD,eDP,dmin,dmax){
 if(!dmin)dmin='3/1/2005';if(!dmax)dmax='1/25/2006';
 if(fm){SetNextFocus(objNext(fm,eD));SetPrevFocus(objPrev(fm,eD));}
 SCal(eD,eD,eDP,dmin,dmax);
}

var zz, zv, d, fTSR;
d = new Date();
fTSR=0;
zv = d.getTime();
zz = "&zz="+zv;

var gBF=false;
function GoTo(u){window.top.location = u + zz;}
function Go(u){window.top.location = u;} 

function BF(){gBF=true;}

function Foci(o){if(!gBF && IsVis(o)){o.focus();}}

function IsVis(o)
{
	if(!o || o.type=="hidden")
	return false;
	
	while(o && o.style && o.style.display!='none')
	{
	o = o.parentNode;	
	}
	return !o || !o.style;
}


function TEK(a,evt){	
	var keycode;
	if (window.event){ keycode = window.event.keyCode; evt = window.event;}
	else if(evt) {keycode = evt.which;}
	else {return true;}
	if(13==keycode){evt.cancelBubble = true; evt.returnValue = false; eval(a);}
	}

function getObj(objID)
	{
	if (document.getElementById) {return document.getElementById(objID);}
	else if (document.all) {return document.all[objID];}
	else if (document.layers) {return document.layers[objID];}
	}
	
function objNext(f,d)
{
	var fFnd=false,el=f.elements,i=0;
	for(;i < el.length;i++)
	{
	if('hidden'!=el[i].type && false==el[i].disabled && IsVis(el[i]) && fFnd)return el[i];
	if(d.id==el[i].id)fFnd=true;
	}
	return null;
}
function objPrev(f,d)
{
	var fFnd=false,el=f.elements,i=el.length - 1;
	for(;i >= 0;i--)
	{
	if('hidden'!=el[i].type && false==el[i].disabled && IsVis(el[i]) && fFnd)return el[i];
	if(d.id==el[i].id)fFnd=true;
	}
	return null;
}

function DoNothing() {return false;}
