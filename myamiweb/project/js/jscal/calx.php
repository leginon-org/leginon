<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3c.org/TR/1999/REC-html401-19991224/loose.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><head>



	<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
    <style>
	    * {margin:0;padding:0;font:8pt arial;}
	    a {color:#333399;}
	    a:link {color:#333399;}
	    a:hover {color:#FF6600;}
	    .pointer {cursor:pointer;cursor:hand;}
    	
	    #OutBdr {position:absolute; top:0px; left:0px; height:186px; overflow:hidden; background-color:#336699;}
	    #InBdr {position:absolute; top:1px; left:1px; height:184px; overflow:hidden; background-color:white;}
    	
	    .today {color:#FF0000;}
	    .invalid {color:#999999;cursor:default;}
	    .picked {background-color:#CCCCCC;}
	    #BotNav {position:absolute; top:161px; width:297px; text-align:center; overflow:hidden;}
	    #BotNav #Close {position:relative;top:1px;text-decoration:none; height:20px; line-height:20px;}

        .navControl {position:absolute;height:22px; width:19px; z-index:50; background-color:#7694bf;}
        .navImg {position:relative;top:2px;cursor:pointer;cursor:hand;}

	    #monthcontainer {position:absolute;width:288px;height:162px; overflow:hidden;background-color:white;}
	    #monthlist {position:relative;left:0px; top:0px; height:162px;}
	    .month {position:absolute;width:148px; height:166px; overflow:hidden;}
        .month .title {position:relative;width:148px;height:22px;overflow:hidden;color:white;text-align:center;line-height:22px; background:#7694bf;font-weight: bold;}
        .month .weekdays_top {width:148x;height:4px;overflow:hidden;}
        .month .body {width:140px;height:136px;overflow:hidden;padding-right:4px;padding-left:4px;}
        .month .weekdays {width:148px; height:16px; overflow:hidden;}
        .month .weekday {position:relative; float:left; top:-4px; width:20px; height:16px; overflow:hidden; text-align:center; font-weight:bold; line-height:20px; color:#336699;}
        .month .dates {width:148px; height:120px; overflow:hidden;}
        .month .bottom {width:148px; height:8px; overflow:hidden;}
	    .month .dates div {float:left; width:20px; height:20px; overflow:hidden; text-align:center; font-weight:bold; line-height:20px;}
	    .titleFill {height:22px;width:1px;background-color:#7694BF;}
	    .calendarFill {height:165px;width:1px;background-color:#D7DCE8;}
    </style>
	<meta content="MSHTML 6.00.2900.2873" name="GENERATOR"></head><body onload="DoLoad()" bgcolor="white" text="black">
<div style="width: 299px;" id="OutBdr">
<div style="width: 297px;" id="InBdr">
<div id="NavPrev" class="navControl">
    <img id="PImg" class="navImg" style="left: 4px; visibility: visible;" title="" onclick="handlePrev()" alt="Previous Month" src="bubble_left_onblue.gif">
</div>
<div style="left: 278px;" id="NavNext" class="navControl">
    <img id="NImg" class="navImg" style="left: 0px; visibility: visible;" title="" onclick="handleNext()" alt="Next Month" src="bubble_right_onblue.gif">
</div>
<div>
    <div style="width: 297px;" id="monthcontainer">
	    <div style="left: -298px; top: 0px;" id="monthlist"><div style="left: 297px; position: absolute;"><div style="height: 22px;" class="titleFill"></div><div style="height: 140px;" class="calendarFill"></div></div><div style="left: 298px;" class="month"><div class="title">April&nbsp;&nbsp;2008</div><div class="weekdays_top"></div><div class="body"><div class="weekdays"><div class="weekday">S</div><div class="weekday">M</div><div class="weekday">T</div><div class="weekday">W</div><div class="weekday">T</div><div class="weekday">F</div><div class="weekday">S</div></div><div class="dates"><div class="invalid"></div><div class="invalid"></div><div style="" class="pointer">1</div><div style="" class="pointer">2</div><div style="" class="pointer">3</div><div class="pointer">4</div><div class="pointer">5</div><div class="pointer">6</div><div class="pointer">7</div><div style="" class="pointer">8</div><div style="" class="pointer">9</div><div class="pointer">10</div><div class="pointer">11</div><div class="pointer">12</div><div class="pointer">13</div><div class="pointer">14</div><div class="pointer">15</div><div class="pointer">16</div><div class="pointer">17</div><div class="pointer">18</div><div class="pointer">19</div><div class="pointer">20</div><div class="pointer">21</div><div class="pointer">22</div><div class="pointer">23</div><div class="pointer">24</div><div class="pointer">25</div><div class="pointer">26</div><div class="pointer">27</div><div class="pointer">28</div><div class="pointer">29</div><div class="pointer">30</div></div></div><div class="bottom"></div></div><div style="left: 446px; position: absolute;"><div style="height: 22px;" class="titleFill"></div><div style="height: 140px;" class="calendarFill"></div></div><div style="left: 447px;" class="month"><div class="title">May&nbsp;&nbsp;2008</div><div class="weekdays_top"></div><div class="body"><div class="weekdays"><div class="weekday">S</div><div class="weekday">M</div><div class="weekday">T</div><div class="weekday">W</div><div class="weekday">T</div><div class="weekday">F</div><div class="weekday">S</div></div><div class="dates"><div class="invalid"></div><div class="invalid"></div><div class="invalid"></div><div class="invalid"></div><div class="pointer">1</div><div class="pointer">2</div><div class="pointer">3</div><div class="pointer">4</div><div class="pointer">5</div><div class="pointer">6</div><div class="pointer">7</div><div class="pointer">8</div><div class="pointer">9</div><div class="pointer">10</div><div class="pointer">11</div><div class="pointer">12</div><div class="pointer">13</div><div class="pointer">14</div><div class="pointer">15</div><div class="pointer">16</div><div class="pointer">17</div><div class="pointer">18</div><div class="pointer">19</div><div class="pointer">20</div><div class="pointer">21</div><div class="pointer">22</div><div class="pointer">23</div><div class="pointer">24</div><div class="pointer">25</div><div class="pointer">26</div><div class="pointer">27</div><div class="pointer">28</div><div class="pointer">29</div><div class="pointer">30</div><div class="pointer">31</div></div></div><div class="bottom"></div></div></div>
    </div>
</div>
<div id="BotNav" style="border-top: 1px solid rgb(215, 220, 232);"><a id="Close" href="javascript:CloseCal()">Close</a></div>
</div><!--"InBdr"-->
</div><!--"OutBdr"-->

<script type="text/javascript">
Function.prototype.bind = function(object) {
  var m_method = this;
  return function() {
    return m_method.apply(object, arguments);
  }
}

function atoi(a){var i=parseInt(a);return isNaN(i)?0:i;}

var g_calMonthList = null;

function calMonth(m,y,pObj,pxLeft,dtSelected)
{
	this.m_month = m;
	this.m_year = y;
	this.m_pxLeft = pxLeft;
	this.m_domElement = null;

	this.getMonth = function(){return this.m_month;}
	this.getYear = function(){return this.m_year;}
	this.getPxLeft = function(){return this.m_pxLeft;}
	this.getDomElement = function(){return this.m_domElement;}
    
	this.createDomElement = function(m,y,dtSelected)
	{
		var mty=DOW(1,m,y);
		var c=wp.GetMonthCount(m,y);
		
		// Draw current month?
		var fCur=(y==new Date().getFullYear()&&m==new Date().getMonth());
		
		// Draw selected month?
		var fSel=(dtSelected&&y==dtSelected.getFullYear()&&m==dtSelected.getMonth());
		
		var datesE=document.createElement('div');
		datesE.className="dates";

		var szDays="";
		var dayE=null;
		for(i=0;i<mty;i++)
		{
			dayE=document.createElement('div');
			dayE.className="invalid";
			datesE.appendChild(dayE);
		}
		for(i=1;i<c+1;i++)
		{
			var d=new Date(y,m,i);
			if((!g_dtMin||d>=g_dtMin)&&(!g_dtMax||d<=g_dtMax)) // Valid date?
			{
				var szClass="pointer";
				if(fSel && i==dtSelected.getDate())szClass+=" picked";
				if(fCur && i==new Date().getDate())szClass+=" today";
				
				dayE=document.createElement('div');
				dayE.className=szClass;
				dayE.y = y; dayE.m = m; dayE.i = i;
				dayE.onclick=DtClk;
				dayE.onmousemove=DtHvr;
				dayE.onmouseout=DtExt;
				
				dayE.appendChild(document.createTextNode(i));
				datesE.appendChild(dayE);
			}
			else
			{
				dayE=document.createElement('div');
				dayE.className="invalid";
				dayE.appendChild(document.createTextNode(i));
				datesE.appendChild(dayE);
			}
		}

		var titleE=document.createElement('div');
		titleE.className="title";
		titleE.appendChild(document.createTextNode(FmtTitle(m,y)));
		
		var monthTopE=document.createElement('div');
		monthTopE.className="weekdays_top";

		var weekdaysE=document.createElement('div');
		weekdaysE.className="weekdays";

		for(i=0;i<7;i++)
		{
			var weekdayE=document.createElement('div');
			weekdayE.className="weekday";
			weekdayE.appendChild(document.createTextNode(rW[(i+wp.GetDowStart())%7]));
			weekdaysE.appendChild(weekdayE);
		}

		var monthBodyE=document.createElement('div');
		monthBodyE.className="body";
		monthBodyE.appendChild(weekdaysE);
		monthBodyE.appendChild(datesE);
		
		var monthBotE=document.createElement('div');
		monthBotE.className="bottom";

		var monthE=document.createElement('div');
		monthE.className="month";

		monthE.appendChild(titleE);
		monthE.appendChild(monthTopE);
		monthE.appendChild(monthBodyE);
		monthE.appendChild(monthBotE);

		return monthE;
	}
    
    var verticalDiv = document.createElement('div');

    var tFill=document.createElement('div');    // title fill
    tFill.className="titleFill";
    tFill.style.height=22+"px";
    verticalDiv.appendChild(tFill);
    
    var cFill=document.createElement('div');     // calendar fill
    cFill.className="calendarFill";
    cFill.style.height=140+"px";
    verticalDiv.appendChild(cFill);

    verticalDiv.style.left=pxLeft - 1+"px";
    verticalDiv.style.position='absolute';
    pObj.appendChild(verticalDiv);

    this.m_domElement = this.createDomElement(this.m_month, this.m_year, dtSelected);
    
    // Position and insert	
	this.m_domElement.style.left = pxLeft+"px";
    pObj.appendChild(this.m_domElement);
    
	return this;
}
	
var g_cMonthSpacing=1;
var g_cMonthWidth=148;
function calMonthList(cM,m,y)
{
	this.m_pxLeft=0;
	this.m_pxLeftShift=g_cMonthWidth+g_cMonthSpacing;
	this.m_cMonths=cM; // # visible months
	this.m_rgcalMonths=new Array();
    this.m_bPrev=false;this.m_bNext=false;
    this.m_bReady=true;
    this.m_lowIndex=0;
    
	this.getFirstMonth = function(){return (this.m_rgcalMonths&&this.m_rgcalMonths.length>0)?this.m_rgcalMonths[0]:null;}
	this.getLastMonth = function(){return (this.m_rgcalMonths&&this.m_rgcalMonths.length>0)?this.m_rgcalMonths[this.m_rgcalMonths.length-1]:null;}
	
	this.init = function(m,y)
	{
		// Reset what we currently have
		this.m_pxLeft = 0;
		while( getObj("monthlist").childNodes.length ) getObj("monthlist").removeChild(getObj("monthlist").childNodes[0]);
		getObj("monthlist").style.left = this.m_pxLeft+"px";
		getObj("monthlist").style.top = "0px"; // set this so it can be accessed via script

        this.m_bPrev=false;this.m_bNext=false;	
        
		for(var i=0;i<this.m_cMonths;i++)
		{
			this.m_rgcalMonths[i] = new calMonth(m,y,getObj("monthlist"),(i*this.m_pxLeftShift),g_dtPick);
			
			// increment month
			y=y+(m==11?1:0);
			m=(m+1)%12;
		}
    }
	
	this.navPrev = function()
	{   
	    if(this.m_bReady)    this.m_bReady = false;
        else                 return null;	        
	    
		var cM=this.getFirstMonth().getMonth();
		var cY=this.getFirstMonth().getYear();
		var pY=cY-(cM==0?1:0);
		var pM=(cM+11)%12;

		// Create and draw the new month
		var cPxLeft = this.getFirstMonth().getPxLeft();
		var prevMonth = new calMonth(pM,pY,getObj("monthlist"),cPxLeft-this.m_pxLeftShift,g_dtPick);
		
		// Update visible month array
		for(var i=this.m_cMonths-1;i>0;i--) this.m_rgcalMonths[i]=this.m_rgcalMonths[i-1];
		this.m_rgcalMonths[i] = prevMonth;
				
		// Scroll the new month into view
		this.m_pxLeft += this.m_pxLeftShift;
		scrollAction(getObj("monthlist"), null, new position(this.m_pxLeft,null), null);
		this.m_bPrev = true;
    }

	this.navNext = function()
	{    
        if(this.m_bReady)    this.m_bReady = false;
        else                 return null;
	
		var cM=this.getLastMonth().getMonth();
		var cY=this.getLastMonth().getYear();
		var nY=cY+(cM==11?1:0);
		var nM=(cM+1)%12;

		// Create and draw the new month
		var cPxLeft = this.getLastMonth().getPxLeft();
		var nextMonth = new calMonth(nM,nY,getObj("monthlist"),cPxLeft+this.m_pxLeftShift,g_dtPick);
		
		// Update visible month array
		for(var i=0;i<this.m_cMonths-1;i++) this.m_rgcalMonths[i]=this.m_rgcalMonths[i+1];
		this.m_rgcalMonths[i] = nextMonth;
		
		// Scroll the new month into view
		this.m_pxLeft -= this.m_pxLeftShift;
		scrollAction(getObj("monthlist"), null, new position(this.m_pxLeft,null), null);
		this.m_bNext = true;
	}

    this.cleanList = function()
    {
        if(this.m_bPrev)
        {
            // remove month & fill
            if(this.m_lowIndex == 0)
            {
                getObj("monthlist").removeChild(getObj("monthlist").childNodes[2]);     
                getObj("monthlist").removeChild(getObj("monthlist").childNodes[2]);
            }
            else
            {   
                getObj("monthlist").removeChild(getObj("monthlist").firstChild);
                getObj("monthlist").removeChild(getObj("monthlist").firstChild);
            }
            this.m_lowIndex = 1;
            this.m_bPrev = false;
        }
        else if(this.m_bNext)
        {
            // remove month & fill
            if(this.m_lowIndex == 0)
            {
                getObj("monthlist").removeChild(getObj("monthlist").firstChild);
                getObj("monthlist").removeChild(getObj("monthlist").firstChild);
            }
            else
            {
                getObj("monthlist").removeChild(getObj("monthlist").childNodes[2]);
                getObj("monthlist").removeChild(getObj("monthlist").childNodes[2]);
            }
            this.m_lowIndex = 0;
            this.m_bNext = false;
        }        
        this.m_bReady = true;
    }
    
	this.init(m,y);
	return this;
}


function handlePrev()
{
	g_calMonthList.navPrev();
	UpdPrev();
	UpdNext();
}

function handleNext()
{
	g_calMonthList.navNext();
	UpdNext();
	UpdPrev();
}

function position(x,y)
{
	this.m_x=x;
	this.m_y=y;

	this.getX=function(){return this.m_x;}
	this.getY=function(){return this.m_y;}

	return this;
}

function scrollAction(domElement,startPos,endPos,duration,iterCount)
{   
	this.m_domElement = domElement;
	this.m_startPos = startPos;
	this.m_endPos = endPos;
	this.m_duration = duration;
	this.m_iterCount = iterCount;
	
	var eL=atoi(this.m_domElement.style.left);
	var eT=atoi(this.m_domElement.style.top);

	// Default startPos to current position
	if(null==this.m_startPos || (null==this.m_startPos.getX() && null==this.m_startPos.getY()))
		this.m_startPos = new position(eL,eT);
	else
	{
		if(null==this.m_startPos.getX()) this.m_startPos = new position(eL,this.m_startPos.getY());
		if(null==this.m_startPos.getY()) this.m_startPos = new position(this.m_startPos.getX(),eT);
	}

	// Default endPos to current position
	if(null==this.m_endPos) 
		this.m_endPos = new position(eL,eT);
	else
	{	
		if(null==this.m_endPos.getX()) this.m_endPos = new position(eL,this.m_endPos.getY());
		if(null==this.m_endPos.getY()) this.m_endPos = new position(this.m_endPos.getX(),eT);
	}
	
	if(null==this.m_duration) this.m_duration = 200;	// Default is 1/5 sec
	if(null==this.m_iterCount) this.m_iterCount = 10;	// Move element 10 times
	
	// Calc pixels/iteration
	this.m_incX = (this.m_endPos.getX()-this.m_startPos.getX())/this.m_iterCount;
	this.m_incY = (this.m_endPos.getY()-this.m_startPos.getY())/this.m_iterCount;
	
	this.nextIter = function()
	{
		this.m_iter++;
		this.m_domElement.style.left = (this.m_startPos.getX()+Math.floor(this.m_iter*this.m_incX))+"px";
		this.m_domElement.style.top = (this.m_startPos.getY()+Math.floor(this.m_iter*this.m_incY))+"px";
		if(this.m_iter<this.m_iterCount) setTimeout("this.nextIter();",this.m_duration/this.m_iterCount);
		else                             setTimeout("g_calMonthList.cleanList();",this.m_duration/this.m_iterCount);
	}
		
	this.m_iter = 0;
	this.nextIter();
	
	return this;
}
</script>

<script type="text/javascript">
var wp=window.parent;
var cf=null;
var g_fCL=false;
var g_eInp=0;
var g_dtMin,g_dtMax;
var g_dtPick;

function getObj(objID)
{
	if(document.getElementById){return document.getElementById(objID);}
	else if(document.all){return document.all[objID];}
	else if(document.layers){return document.layers[objID];}
}
function EvtObj(e){if(!e)e=window.event;return e;}
function stopBubble(e){e.cancelBubble=true;if(e.stopPropagation)e.stopPropagation();}
function EvtTgt(e)
{
	var el;
	if(e.target)el=e.target;
	else if(e.srcElement)el=e.srcElement;
	if(el.nodeType==3)el=el.parentNode; // defeat Safari bug
	return el;
}

function GetCF(){if (!cf)cf=wp.getObj('CalFrame');return cf;}
function DoLoad()
{
	g_fCL=true;
}

function DoCal(eD,eDP,dmin,dmax,cM)
{	  
	var dt=wp.GetInputDate(eD.value);
	if(null==dt&&null!=eDP){dt=wp.GetInputDate(eDP.value);}
	
	g_dtPick=dt;
	if(dmin&&""==dmin)dmin=null;
	if(dmax&&""==dmax)dmax=null;
	if(null==dt)
	{
		// Check for valid min date and use that, else use current
		dt=new Date();
		if(dmin&&dt<new Date(dmin))dt=new Date(dmin);
	}

	SetMinMax(dmin?new Date(dmin):null,dmax?new Date(dmax):null);
	
	if(null==cM)cM=2; // Default to 2 month display	
	UpdCal(cM,dt.getMonth(),dt.getFullYear());

    g_eInp=eD;

    // prevent Mozilla from flickering
	setTimeout("ShowCal()",1);
}

function ShowCal()
{
	if ("none"==GetCF().style.display) {GetCF().style.display="block";}// FF drawing bug
	GetCF().style.visibility="visible";
}

function UpdCal(cM,m,y)
{
	// Size the frame
	var pxSpacing = g_cMonthSpacing*(cM-1);
	getObj("OutBdr").style.width=((g_cMonthWidth*cM)+2+pxSpacing)+"px";
	getObj("InBdr").style.width=((g_cMonthWidth*cM)+pxSpacing)+"px";
	getObj("monthcontainer").style.width=((g_cMonthWidth*cM)+pxSpacing)+"px";
	getObj("NavNext").style.left = ((g_cMonthWidth*cM)+pxSpacing-19)+"px";
	GetCF().style.width=((g_cMonthWidth*cM)+2+pxSpacing)+"px";
	GetCF().style.height=186+"px";

	g_calMonthList = null;
	g_calMonthList = new calMonthList(cM,m,y);
			
	UpdNext();
	UpdPrev();
}

function UpdNext()
{
	var currMonth=g_calMonthList.getLastMonth();
	var nm=currMonth.getMonth();
	var ny=currMonth.getYear();

	var hd=(!g_dtMax||!(ny>g_dtMax.getFullYear()||(ny==g_dtMax.getFullYear()&&parseInt(nm)>=g_dtMax.getMonth())));
	getObj('NImg').style.visibility=hd?"visible":"hidden";
}

function UpdPrev()
{
	var currMonth=g_calMonthList.getFirstMonth();
	var pm=currMonth.getMonth();
	var py=currMonth.getYear();
	
	var hd=(!g_dtMin||!(py<g_dtMin.getFullYear()||(py==g_dtMin.getFullYear()&&parseInt(pm)<=g_dtMin.getMonth())));
	getObj('PImg').style.visibility=hd?"visible":"hidden";
}
function DtHvr(e){EvtTgt(EvtObj(e)).style.backgroundColor="#FFDD99";}
function DtExt(e){EvtTgt(EvtObj(e)).style.backgroundColor="";}
function DtClk(e)
{
    var element = EvtTgt(EvtObj(e))
    wp.CalDateSet(g_eInp,element.i,element.m+1,element.y);
    if(g_eInp.onblur){g_eInp.onblur();}
    GetCF().style.visibility="hidden";
    wp.SetCalShown(false);
    wp.CalendarCallback();
}
function CloseCal(){
    if(wp.getObj('CalDiv'))
    {
        wp.CalSetFocus(g_eInp);
        wp.getObj('CalDiv').style.visibility="hidden";
        GetCF().style.visibility="hidden";
        wp.SetCalShown(false);    
    }
    else
    {
        wp.CalSetFocus(g_eInp);
        GetCF().style.visibility="hidden";
        wp.SetCalShown(false);
    }
}
function SetMinMax(n,x){g_dtMin=n;g_dtMax=x;}
function FmtTitle(m,y){return rN[m]+"\u00a0\u00a0"+y.toString()}
// LOC Comment: Month name.
var rN=new Array(12);rN[0]="January";rN[1]="February";rN[2]="March";rN[3]="April";rN[4]="May";rN[5]="June";rN[6]="July";rN[7]="August";rN[8]="September";rN[9]="October";rN[10]="November";rN[11]="December";
// LOC Comment: Weekday abbrv.
var rW=new Array(7);rW[0]="S";rW[1]="M";rW[2]="T";rW[3]="W";rW[4]="T";rW[5]="F";rW[6]="S";
function DOW(d,m,y){var dt=new Date(y,m,d);return(dt.getDay()+(7-wp.GetDowStart()))%7;}
</script>
</body></html>
