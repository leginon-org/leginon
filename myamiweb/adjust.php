<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

$title = "Image Adjust";
if ($displayname=$_GET['displayname'])
	$title .=" - ".$displayname;

$defaultmax = 255;
if (!$min=$_GET['pmin'])
	$min=0;
if (!$max=$_GET['pmax'])
	$max=$defaultmax;
if (!$name=$_GET['name'])
	$name='v';
if (!$currentfilter=$_GET['filter'])
	$currentfilter='default';
if (!$currentbinning=$_GET['binning'])
	$currentbinning='auto';
if (!$currentfftbin=$_GET['fftbin'])
	$currentfftbin='b';
if (!$currentquality=$_GET['t'])
	$currentquality='80';
if (!$currentgradient=$_GET['gr'])
	$currentgradient='';
if ($min > $defaultmax)
	$min = $defaultmax;
if ($max > $defaultmax)
	$max = $defaultmax;
if (!$autoscale=$_GET['autoscale'])
	$autoscale=0;

if (!$loadfromjpg=$_GET['lj'])
	$loadfromjpg=0;

$state = ($loadfromjpg) ? "disabled" : "";
$disabledcolor="#AABBCC";

$arrayurl = explode("/", $_SERVER['PHP_SELF']);
array_pop($arrayurl);
$baseurl=implode("/",$arrayurl);

$def_stddev=3;
$def_permin=.01;
$def_permax=.999;
$sel_mnmx="";
$sel_std="checked";
$sel_ctf="";

$sel_auto = ($loadfromjpg==1) ? "checked" : "";
$sel_man = ($loadfromjpg==1) ? "" : "checked";


list($scaletype, $arg1, $arg2)=explode(';', $autoscale);

if ($GET['autoscale']==0) {
	$sel_mnmx="checked";
	$sel_std="";
	$sel_cdf="";
}
if ($scaletype=="s") {
  $def_stddev=$arg1;
	$sel_mnmx="";
  $sel_std="checked";
  $sel_cdf="";
} else if ($scaletype=="c") {
  $def_permin=$arg1;
  $def_permax=$arg2;
	$sel_mnmx="";
  $sel_std="";
  $sel_cdf="checked";
}
?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<?php
require "getgrad.php";
require "inc/filter.inc";

$filterdata = new filter();
$filtertypes = $filterdata->getFilterTypes();
$binningtypes = $filterdata->getBinningTypes();
$fftbintypes = $filterdata->getFFTBinTypes();

?>

<title><?=$title?></title>
<script type="text/javascript" src="js/viewer.js"></script>
<script type="text/javascript"><!--
<?php
echo"
var jsmaxgrad = 255
var jsminpix = $min
var jsmaxpix = $max
var jsmingradpix = 0
var jsmaxgradpix = $defaultmax
var jsbaseurl = '$baseurl/'
var jsviewname = '$name'
var jsfilter = '$currentfilter'
var jsfftbin = '$currentfftbin'
var jsbinning = '$currentbinning'
var jsquality = '$currentquality'
var jsautoscale = '$autoscale'
var jsloadfromjpg = '$loadfromjpg'
var jsgradient = '$currentgradient'
";
?>
var rminval=false
var rmaxval=false
var	jsdefaultborder="1px solid #AAAAAA"
var	jserrorborder="2px solid #ff0000"

function displayimginfo(minval, maxval, meanval, stdevval) {
	str='<ul style="padding: 0 0 0 0; margin: 0 0 0 0;">'
		+'<li style="display: inline">min:'+minval+'<\/li> '
		+'<li style="display: inline">max:'+maxval+'<\/li> '
		+'<li style="display: inline">mean:'+meanval+'<\/li> '
		+'<li style="display: inline">stdev:'+stdevval+'<\/li>'
		+'<\/ul>'
	return str
}

function getImageInfo() {
	jsimgId=parentwindow.jsimgId
	selpreset = eval("parentwindow.jspreset"+jsviewname)
	var url = 'getimagestat.php?id='+jsimgId+'&pr='+selpreset
	var xmlhttp = getXMLHttpRequest()
	xmlhttp.open('GET', url, true)
	xmlhttp.onreadystatechange = function() {
		if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
		var xmlDocument = xmlhttp.responseXML
		var minval = parseFloat(xmlDocument.getElementsByTagName('min').item(0).firstChild.data)
		var maxval = parseFloat(xmlDocument.getElementsByTagName('max').item(0).firstChild.data)
		var meanval = parseFloat(xmlDocument.getElementsByTagName('mean').item(0).firstChild.data)
		var stdevval = parseFloat(xmlDocument.getElementsByTagName('stdev').item(0).firstChild.data)
	if (infodiv=document.getElementById('imginfodiv')) {
		infodiv.innerHTML=displayimginfo(minval, maxval, meanval, stdevval)
	}
	normminval = meanval - 3*stdevval
	normmaxval = meanval + 3*stdevval
	rminval=minval
	rmaxval=maxval

	pnormminval = ((meanval - 3*stdevval)-minval)*100/(maxval-minval)
	pnormmaxval = ((meanval + 3*stdevval)-minval)*100/(maxval-minval)

	document.getElementById('pmin').value=Math.round(pnormminval)
	document.getElementById('pmax').value=Math.round(pnormmaxval)
	document.getElementById('pminrel').value=normminval.toFixed(1)
	document.getElementById('pmaxrel').value=normmaxval.toFixed(1)
		}
	}
	xmlhttp.send(null)
}

function selectimgtype(name) {
	if (loadfromjpg = document.adjustform.loadfromjpg) {
		for (i=0; i<loadfromjpg.length; i++){
			imgtype=loadfromjpg[i].value
			loadfromjpg[i].checked=(imgtype==name) ? true : false
		}
	}
	setloadfromjpg()
}

function selectradio(name) {
		selectimgtype('0')
    scaletype = document.adjustform.scaletype
    for (i=0; i<scaletype.length; i++){
      scale=scaletype[i].value
      scaletype[i].checked=(scale==name) ? true : false
    }
}

function setscale() {
	scalepar=""
	scale=""
	auto=false
		scaletype = document.adjustform.scaletype
		for (i=0; i<scaletype.length; i++){
			if(scaletype[i].checked) {
			 scale=scaletype[i].value
			}
		}
		if (scale=="minmax") {
				objpmin=document.getElementById('pminrel')
				objpmax=document.getElementById('pmaxrel')
				jsminpix=objpmin.value
				jsmaxpix=objpmax.value
				objpmin.style.border=jsdefaultborder
				objpmax.style.border=jsdefaultborder
				if (isNaN(jsminpix)) {
					objpmin.style.border=jserrorborder
					return false;
				}
				if (isNaN(jsmaxpix)) {
					objpmin.style.border=jserrorborder
					return false;
				}
				jsminpix=(jsminpix-rminval)*255/(rmaxval-rminval)
				jsmaxpix=(jsmaxpix-rminval)*255/(rmaxval-rminval)
		} else if (scale=="stdev") {
				auto=true
				objnstdev=document.getElementById('nstdev')
				nstdev=objnstdev.value
				objnstdev.style.border=jsdefaultborder
				if (isNaN(nstdev) || nstdev<0 ) {
					objnstdev.style.border=jserrorborder
					return false;
				}
				scalepar="s;"+nstdev
		} else if (scale=="cdf") {
				auto=true
				objpermin=document.getElementById('permin')
				objpermax=document.getElementById('permax')
				permin=objpermin.value
				permax=objpermax.value
				objpermin.style.border=jsdefaultborder
				objpermax.style.border=jsdefaultborder
				if (isNaN(permin) || permin<0 || permin>1) {
					objpermin.style.border=jserrorborder
					return false;
				}
				if (isNaN(permax) || permax<0 || permax>1) {
					objpermax.style.border=jserrorborder
					return false;
				}
				scalepar="c;"+permin+";"+permax
	}
	jsautoscale = (auto==true) ? scalepar : 0;
	return true
}

function setloadfromjpg() {
	if (loadfromjpg = document.adjustform.loadauto) {
		for (i=0; i<loadfromjpg.length; i++){
			if(loadfromjpg[i].checked) {
				jsloadfromjpg=loadfromjpg[i].value
			}
		}
	}
}

function update() {
	if(!setscale()) {
		return false
	}
	if (binninglist = document.adjustform.binning)
		jsbinning=binninglist.options[binninglist.selectedIndex].value;
	parentwindow.setbinning(jsviewname,jsbinning);

	if (fftbinlist = document.adjustform.fftbin)
		jsfftbin=fftbinlist.options[fftbinlist.selectedIndex].value;
	parentwindow.setfftbin(jsviewname,jsfftbin);

	if (filterlist = document.adjustform.filter)
		jsfilter=filterlist.options[filterlist.selectedIndex].value;
	parentwindow.setfilter(jsviewname,jsfilter);
	if (!eval("parentwindow."+jsviewname+"filter_bt_st"))
		if (jsfilter!="default")
			eval("parentwindow.toggleButton('"+jsviewname+"filter_bt', 'filter_bt')");
	parentwindow.setminmax(jsviewname,jsminpix,jsmaxpix);
	parentwindow.setautoscale(jsviewname,jsautoscale);
	parentwindow.setloadfromjpg(jsviewname,jsloadfromjpg);
	if (qualitylist = document.adjustform.quality)
		jsquality=qualitylist.options[qualitylist.selectedIndex].value;
	parentwindow.setquality(jsviewname,jsquality);
	if (gradientlist = document.adjustform.gradientlist) {
		jsgradient=gradientlist.options[gradientlist.selectedIndex].value;
		parentwindow.setgradient(jsviewname,jsgradient);
	}
	parentwindow.newfile(jsviewname);
}

function init(){
  parentwindow = window.opener
	getImageInfo()
	setgrad()
	f(jsloadfromjpg)
  this.focus()
} 

function f(state) {
	if (state==0) {
		state=false
	}
	o=document.getElementById('adjust')
	setGroup(o, state)
}

function setGroup(groupRef, state) {
	var inputs = groupRef.getElementsByTagName("input");
	for (var i=0;i<inputs.length;i++) {
		inputs[i].disabled = state;
	}
	var inputs = groupRef.getElementsByTagName("select");
		for (var i=0;i<inputs.length;i++) {
		inputs[i].disabled = state;
	}
	var inputs = groupRef.getElementsByTagName("span");
		for (var i=0;i<inputs.length;i++) {
		inputs[i].style.color= (state) ? "<?=$disabledcolor?>" : "";
	}
	var inputs = groupRef.getElementsByTagName("li");
		for (var i=0;i<inputs.length;i++) {
		inputs[i].style.color= (state) ? "<?=$disabledcolor?>" : "";
	}
}

function setpminrel() {
	if (o=document.getElementById('pmin')) {
		m=o.value
		o.style.border=jsdefaultborder
		if (isNaN(m)) {
			o.style.border=jserrorborder
			return false;
		}
		if (m>100) {
			m=100
		}
		if (m<0) {
			m=0
		}
		o.value=m
		if (po=document.getElementById('pminrel')) {
			m=m*(rmaxval-rminval)/100 + rminval
			m=(m>rmaxval) ? rmaxval  : m
			po.value=m.toFixed(1)
		}
	}
	update()
}

function setpmaxrel() {
	if (o=document.getElementById('pmax')) {
		m=o.value
		o.style.border=jsdefaultborder
		if (isNaN(m)) {
			o.style.border=jserrorborder
			return false;
		}
		if (m>100) {
			m=100
		}
		if (m<0) {
			m=0
		}
		o.value=m
		if (po=document.getElementById('pmaxrel')) {
			m=m*(rmaxval-rminval)/100 + rminval
			m=(m<rminval) ? rminval  : m
			po.value=m.toFixed(1)
		}
	}
	update()
}

function setpmin() {
	if (o=document.getElementById('pminrel')) {
		m=o.value
		o.style.border=jsdefaultborder
		if (isNaN(m)) {
			o.style.border=jserrorborder
			return false;
		}
		if (m<rminval) {
			m=rminval
		}
		if (m>rmaxval) {
			m=rmaxval
		}
		o.value=m
		if (po=document.getElementById('pmin')) {
			m=(m-rminval)*100/(rmaxval-rminval)
			m=(m<0) ? 0 : m
			po.value=m.toFixed(1)
		}
	}
	update()
}

function setpmax() {
	if (o=document.getElementById('pmaxrel')) {
		m=o.value
		if (isNaN(m)) {
			o.style.border=jserrorborder
			return false;
		}
		if (m<rminval) {
			m=rminval
		}
		if (m>rmaxval) {
			m=rmaxval
		}
		o.value=m
		if (po=document.getElementById('pmax')) {
			m=(m-rminval)*100/(rmaxval-rminval)
			m=(m>100) ? 100 : m
			po.value=m.toFixed(1)
		}
	}
	update()
}

 // --> 
</script>
<style type="text/css">
span, ul, li {
	font-family: Arial;
	font-size: 12px;
	padding:0;
	margin:3px 0px;
}
ul {
	list-style-type: none;
}
.d li {
display:inline;
background-color:#eee;
border:1px solid;
border-color:#f3f3f3 #bbb #bbb #f3f3f3;
margin:0;
padding:.5em .3em .3em .3em;
} 

.r li {
display:block;
background-color:#eee;
border:1px solid;
border-color:#f3f3f3 #bbb #bbb #f3f3f3;
margin:0;
padding:.2em;
} 

.e li {
display:block;
}

.b {
	border: 1px solid #AAAAAA;
}

</style>

</head><body onload="init();" bgcolor="#ffffff" >
<form action="(EmptyReference!)" name="adjustform" >
<ul class="d">
<li>
<span style="font-weight: bold"><?=$title?></span>
		<input name="loadauto" value="1" <?=$sel_auto?> onclick="f(true); setloadfromjpg(); update()" type="radio">auto
	<input name="loadauto" value="0" <?=$sel_man?> onclick="f(false); setloadfromjpg(); update()" type="radio">
	manual
</li>
</ul>
<ul>
<li>
<div id="imginfodiv" style="font-family: Arial; font-size: 12px; border: 1px solid rgb(0, 0, 0); margin-top: 6px; padding-left:2px; background: rgb(255, 255, 200) none repeat scroll 0% 0%; position: relative; width: 265px; ">
<ul><li>min:	max:	mean:	stdev:</li></ul>
</div>
</li>
</ul>
<div id="adjust">
<ul>
<li>
<span style="font-weight: bold">Image Contrast</span>
</li>
<li>
	<ul class="r" style="width: 250px;">
	<li>
	<div>
	<div style="position:relative; margin:0px; padding:0px">
	<p style="margin:0px 0px 0px 0px; padding:0">
	<input name="scaletype" value="minmax" type="radio"  <?=$state?> <?=$sel_mnmx?> onclick="update()" >
	<span style="margin-left:10px">min</span>
	<span style="margin-left:25px">max</span>
	</p>
	<p style="margin:0px 0px 0px 25px; padding:0">
	<input class="b" id="pminrel" size="3" value="<?=$min?>" type="text"  <?=$state?> onclick="selectradio('minmax')" onchange="setpmin()" ><span style="margin-left:8px">&nbsp;</span>
  <input class="b" id="pmaxrel" size="3" value="<?=$max?>" type="text"  <?=$state?> onclick="selectradio('minmax')" onchange="setpmax()" > 
	image value</p>
	<p style="margin:1px 0px 0px 25px; padding:0">
	<input class="b" id="pmin" size="3" value="<?=$min?>" type="text"  <?=$state?> onclick="selectradio('minmax')" onchange="setpminrel()" >%
  <input class="b" id="pmax" size="3" value="<?=$max?>" type="text"  <?=$state?> onclick="selectradio('minmax')" onchange="setpmaxrel()" >% 
	relative value</p>
	</div>
	</div>
	<li>
	<input name="scaletype" value="stdev" type="radio"  <?=$state?> <?=$sel_std?> onclick="update()" >
	norm +/- <input class="b" id="nstdev" size="2" value="<?=$def_stddev?>" type="text"  <?=$state?> onclick="selectradio('stdev')" onchange="update()" > std dev
	</li>
	<li>
	<input name="scaletype" value="cdf" type="radio"  <?=$state?> <?=$sel_cdf?> onclick="update()" >
	CDF
	<input class="b" id="permin" size="2" value="<?=$def_permin?>" type="text"  <?=$state?> onclick="selectradio('cdf')" onchange="update()" > to
	<input class="b" id="permax" size="2" value="<?=$def_permax?>" type="text"  <?=$state?> onclick="selectradio('cdf')" onchange="update()" > 
	</li>
<?php
displaygrad($options, $imgsrc);
?>
	</ul>
</li>

</ul>
<span style="font-weight: bold">Filtering</span>
<ul class="r" style="width: 250px" >
<li>
		Filter
	<select name="filter"  <?=$state?> onchange="update()" >
	<?php
	foreach ($filtertypes as $k=>$filter) {
		$sel = ($k==$currentfilter) ? 'selected' : '';
		echo '<option value="'.$k.'" '.$sel.'>'.$filter.'</option>'."\n";
	}
	?>
	</select>
</li>
<li>
		Binning
	<select name="binning"  <?=$state?> onchange="update()" >
	<?php
	foreach ($binningtypes as $k=>$binning) {
		$sel = ($k==$currentbinning) ? 'selected' : '';
		echo '<option value="'.$k.'" '.$sel.'>'.$binning.'</option>'."\n";
	}
	?>
	</select>
	Quality
	<select name="quality"  <?=$state?> onchange="update()" >
		<option value="png">png</option>
	<?php
		foreach(array(100,90,80,70,60,50) as $q) {
		$sel = ($q==$currentquality) ? 'selected' : '';
		echo '		<option value="'.$q.'" '.$sel.'>jpeg '.$q.'</option>'."\n";
		}
	?>
	</select>
</li>
<li>
		Bin image
	<select name="fftbin"  <?=$state?> onchange="update()" >
	<?php
	foreach ($fftbintypes as $k=>$fftbin) {
		$sel = ($k==$currentfftbin) ? 'selected' : '';
		echo '<option value="'.$k.'" '.$sel.'>'.$fftbin.'</option>'."\n";
	}
	?>
	</select>
		calculating fft
</li>		
</ul>
</div>
</form>
</body>
</html>
