<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

$title = "Image Adjust";
if ($displayname=$_REQUEST['displayname'])
	$title .=" - ".$displayname;

if (!$cmap = $_REQUEST['colormap'])
	$cmap = 0;
$defaultmax = ($cmap) ? 1274 : 255;
if (!$min=$_REQUEST['pmin'])
	$min=0;
if (!$max=$_REQUEST['pmax'])
	$max=$defaultmax;
if (!$name=$_REQUEST['name'])
	$name='v';
if (!$currentfilter=$_REQUEST['filter'])
	$currentfilter='default';
if (!$currentbinning=$_REQUEST['binning'])
	$currentbinning='auto';
if ($min > $defaultmax)
	$min = $defaultmax;
if ($max > $defaultmax)
	$max = $defaultmax;
$currentgradient='grad.php';


$arrayurl = explode("/", $_SERVER['PHP_SELF']);
array_pop($arrayurl);
$baseurl=implode("/",$arrayurl);
?>
<html>
<head>
<title><?=$title?></title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<link rel="stylesheet" type="text/css" href="css/view.css">

<script src="js/LibCrossBrowser.js"></script>
<script src="js/EventHandler.js"></script>
<script src="js/Bs_Slider.class.js"></script>
<script src="js/Bs_FormUtil.lib.js"></script>
<script src="js/viewiframe.js"></script>
<script><!--
<?



echo"
var jsminpix = $min;
var jsmaxpix = $max;
var jscolormap = $cmap;
var jsmingradpix = 0;
var jsmaxgradpix = $defaultmax;
var jsbaseurl = '$baseurl/';
var jsviewname = '$name';
var jsfilter = '$currentfilter';
var jsbinning = '$currentbinning';
var gradient = '/img/dfe/$currentgradient';
";
require('inc/filter.inc');
$filterdata = new filter();
$filtertypes = $filterdata->getFilterTypes();
$binningtypes = $filterdata->getBinningTypes();

?>
function update() {
//	if (eval("parentwindow.jsmin"+jsviewname))
//		eval("parentwindow.jsmin"+jsviewname+"="+jsminpix);
//	if (eval("parentwindow.jsmax"+jsviewname))
//		eval("parentwindow.jsmax"+jsviewname+"="+jsmaxpix);
	if (binninglist = document.adjustform.binning)
		jsbinning=binninglist.options[binninglist.selectedIndex].value;
	parentwindow.setbinning(jsviewname,jsbinning);

	if (filterlist = document.adjustform.filter)
		jsfilter=filterlist.options[filterlist.selectedIndex].value;
	parentwindow.setfilter(jsviewname,jsfilter);
	if (!eval("parentwindow."+jsviewname+"filter_bt_st"))
		if (jsfilter!="default")
			eval("parentwindow.toggleimage('"+jsviewname+"filter_bt', 'filter_bt')");
	parentwindow.setminmax(jsviewname,jsminpix,jsmaxpix);
	parentwindow.setcolormap(jsviewname,jscolormap);
	parentwindow.newfile(jsviewname);

}

function drawSliders() {

  minpix1 = new Bs_Slider();
  minpix1.objectName = 'minpix1';
  minpix1.attachOnChange(bsSliderChange1);
  minpix1.width         = 255;
  minpix1.height        = 8;
  minpix1.minVal        = 0;
  minpix1.maxVal        = <?=$defaultmax?>;
  minpix1.valueInterval = 1;
  minpix1.arrowAmount   = 1;
  minpix1.valueDefault  = <?=$min ?>;
  minpix1.imgBasePath   = 'img/';
  minpix1.setBackgroundImage('dfe/white.php', 'no-repeat');
  minpix1.setSliderIcon('dfe/cursor_min2.gif', 11, 8);
  minpix1.useInputField = 0;
  minpix1.draw('minpix1Div');
  
  maxpix1 = new Bs_Slider();
  maxpix1.objectName = 'maxpix1';
  maxpix1.attachOnChange(bsSliderChange2);
  maxpix1.width         = 255;
  maxpix1.height        = 8;
  maxpix1.minVal        = 0;
  maxpix1.maxVal        = <?=$defaultmax?>;
  maxpix1.valueInterval = 1;
  maxpix1.arrowAmount   = 1;
  maxpix1.valueDefault  = <?=$max ?>;
  maxpix1.imgBasePath   = 'img/';
  maxpix1.setBackgroundImage('dfe/white.php', 'no-repeat');
  maxpix1.setSliderIcon('dfe/cursor_max2.gif', 11, 8);
  maxpix1.useInputField = 0;
  maxpix1.draw('maxpix1Div');

}

function init(){
  parentwindow = window.opener;
  initCrossBrowserLib();
  drawSliders();
  jsminpix = minpix1.valueDefault;
  jsmaxpix = maxpix1.valueDefault;
  document.getElementById('gradientDiv').style.background = 'url('+jsbaseurl+gradient+'?colormap='+jscolormap+'&min='+jsminpix+'&max='+jsmaxpix+')'; 
  this.focus();
} 

 // --> 
</script> 

</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" bgcolor="#FFFFFF" onload="init();">
<form method="post" name="adjustform" id="adjust" >
<?   $cmapstr = ($cmap==1) ? "0" : "1";  ?>
<input type="hidden" name="colormap" value="<?=$cmapstr?>">
<div id="imagemap" style="z-index:99999;position:absolute;visibility:hidden;border:1px solid black"></div>
<div id="treedata" style="z-index:99999;position:absolute;visibility:hidden;border:1px solid black"></div>
<table border=0>
  <tr>
   <td>
	<button class="button" type="submit" value="">
	<img src="img/dfe/grad.php?w=15&h=15&colormap=<?=$cmapstr?>">
	</button>
   </td>
   <td>
	<label for="maxpix1Div">max</label><br>
	<label for="minpix1Div">min</label>
    </td>
   <td>
    <table border=0 cellspacing=0 cellpadding=0 >
   <tr>
    <td width="250" height=8>
      <div id="maxpix1Div"</div>
    </td>
   </tr>
   <tr>
    <td width="255" height=16>
      <div id="gradientDiv"><p></div>
    </td>
   </tr>
   <tr>
    <td width="250" height=0>
      <div id="minpix1Div"></div>
    </td>
  </tr>
 </table>
 </td>
 </tr>
 <tr>
	<td colspan="2">
		Filter
	</td>
	<td>
    <table border=0 cellspacing=0 cellpadding=0 >
	<tr>
	<td>
	<select name="filter">
	<?
	foreach ($filtertypes as $k=>$filter) {
		$sel = ($k==$currentfilter) ? 'selected' : '';
		echo '<option value="'.$k.'"'.$sel.'>'.$filter.'</option>'."\n";
	}
	?>
	</select>
	</td>
	<td>
		Binning
	</td>
	<td>
	<select name="binning">
	<?
	foreach ($binningtypes as $k=>$binning) {
		$sel = ($k==$currentbinning) ? 'selected' : '';
		echo '<option value="'.$k.'"'.$sel.'>'.$binning.'</option>'."\n";
	}
	?>
	</select>
	</td>
	</tr>
    </table>
  </td>
 </tr>
 <tr>
 <td>
	<input id="updatebutton" type="button" alt="Update Image" value="Update" onclick="update();">
 </td>
 </tr>
</table>
</form>
</body>
</html>
