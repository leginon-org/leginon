var cF=null;var cW=null;var g_tid=0;var g_cP,g_eD,g_eDP,g_dmin,g_dmax;
var nextFocus;var g_fNoCal=false;

function getEventObj(e){if(!e)e=window.event;return e;}

function stopBubble(e){e=getEventObj(e);e.cancelBubble=true;if(e.stopPropagation)e.stopPropagation();}

function CB(){stopBubble(event);}

function SCal(cP,eD,eDP,dmin,dmax){
 clearTimeout(g_tid);
 if(g_fNoCal){g_fNoCal=false;return;}
	if(g_calShown && eD==g_eD)return;
	g_calShown = true;
	g_calCB = null;
 g_cP=cP;
 g_eD=eD;
 g_eDP=eDP;
 g_dmin=dmin;
 g_dmax=dmax;
 WaitCal();}
function CancelCal(){clearTimeout(g_tid);if(!cF)cF=getObj('CalFrame');cF.style.visibility="hidden";g_calShown=false;}
function WaitCal()
{ 
 if(!cW)cW=frames['CalFrame'];

 if(null==cW||null==cW.g_fCL||false==cW.g_fCL){
	g_tid=setTimeout("WaitCal()", 200);
	}
 else{
 if(!cF)cF=getObj('CalFrame');
	cF.style.visibility="hidden";
	setTimeout("DoCal()",1);
	}
}
function DoCal(){PosCal(g_cP);
if(!cW)cW=frames['CalFrame'];
cW.DoCal(g_eD,g_eDP,g_dmin,g_dmax);}

function getScrollTop()
{
	if(document.documentElement.scrollTop) return document.documentElement.scrollTop;
	if(document.body.scrollTop) return document.body.scrollTop;
	if(window.pageYOffset) return window.pageYOffset;
	return 0;
}

function getWinHeight()
{
	if(window.innerHeight) return window.innerHeight;
	if(document.documentElement.clientHeight) return document.documentElement.clientHeight;
	if(document.body.clientHeight) return document.body.clientHeight;
	return 0;
}

function PosCal(cP)
{
	var dB=document.body;var eL=0;var eT=0;
 if(!cF)cF=getObj('CalFrame');
	for(var p=cP;p&&p.tagName!='BODY';p=p.offsetParent){eL+=p.offsetLeft;eT+=p.offsetTop;}
	var eH=cP.offsetHeight;var dH=parseInt(cF.style.height);var sT=getScrollTop();
	if(eT-dH>=sT&&eT+eH+dH>getWinHeight()+sT)eT-=dH;else eT+=eH;
	cF.style.left=eL+'px';cF.style.top=eT+'px';
}

function SetNextFocus(e){nextFocus=e;if(nextFocus)nextFocus.onfocus=CancelCal;}
function SetPrevFocus(e){if(e)e.onfocus=CancelCal;}

function FGoNextFocus(){if(nextFocus){nextFocus.focus();return true;}return false;}

function CalSetFocus(e){if(e){g_fNoCal=true;e.focus();setTimeout("EndCalFocus()", 200);}}
function EndCalFocus(){g_fNoCal=false;}

function CalDateSet(eInp,d,m,y,giveFocus)
{
	var ds=GetDateSep();
	var fmt=GetDateFmt();

	if(fmt=="mmddyy")eInp.value=m+ds+d+ds+y;
	else if(fmt=="ddmmyy")eInp.value=d+ds+m+ds+y;
	else eInp.value=y+ds+m+ds+d;
	if(!giveFocus)
	CalSetFocus(eInp);
}

var g_calShown = false;
function SetCalShown(fcshown){g_calShown=fcshown;}

var g_calCB;
function CalendarCallback(){if(g_calCB)g_calCB();}
function SetCalendarCallback(cb){g_calCB=cb;}


function GetInputDate(t)
{
	if(!t.length) return null;
	t=t.replace(/\s+/g,"");
	if(t.match(/[^-|\d|\.|\/]/)) return null;
	var rgt=t.split(/-|\.|\//);
	for(var i=0;i<rgt.length;i++) rgt[i]=parseInt(rgt[i],10);
	if(!rgt[1]) return null;
	var m,d,y;
	var fmt=GetDateFmt();
	if(fmt=="yymmdd")
	{
	if(!rgt[2]) return null;
	m=rgt[1];d=rgt[2];y=rgt[0];
	}
	else
	{
	if(fmt=="mmddyy"){m=rgt[0];d=rgt[1];}
	else{m=rgt[1];d=rgt[0];}//fmt=="ddmmyy"
	if(rgt[2])y=rgt[2];
	else y=DefYr(m-1,d);
	}
	m-=1;if(y<100)y+=2000;
	if(y<1601||y>4500||m<0||m>11||d<1||d>GetMonthCount(m,y))return null;
	return new Date(y,m,d);
}

var rM=new Array(12);rM[0]=rM[2]=rM[4]=rM[6]=rM[7]=rM[9]=rM[11]=31;rM[3]=rM[5]=rM[8]=rM[10]=30;rM[1]=28;
function GetMonthCount(m,y){var c=rM[m];if((1==m)&&IsLY(y))c++;return c;}
function IsLY(y){if(0==y%4&&((y%100!=0)||(y%400==0)))return true;else return false;}
function DefYr(m,d){var dt=new Date();var yC=(dt.getYear()<1000)?1900+dt.getYear():dt.getYear();if(m<dt.getMonth()||(m==dt.getMonth()&&d<dt.getDate()))yC++;return yC;}