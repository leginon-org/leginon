<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

$title = "Image Adjust";
if ($displayname=$_GET['displayname'])
	$title .=" - ".$displayname;
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
if (!$min=$_GET['pmin'])
	$min=0;
if (!$max=$_GET['pmax'])
	$max=255;
if (!$name=$_GET['name'])
	$name='v';

$arrayurl = explode("/", $PHP_SELF);
array_pop($arrayurl);
$baseurl=implode("/",$arrayurl);
echo"
var jsminpix = $min;
var jsmaxpix = $max;
var jsbaseurl = '$baseurl/';
var jsviewname = '$name';
";
?>
function update() {
//	if (eval("parentwindow.jsmin"+jsviewname))
//		eval("parentwindow.jsmin"+jsviewname+"="+jsminpix);
//	if (eval("parentwindow.jsmax"+jsviewname))
//		eval("parentwindow.jsmax"+jsviewname+"="+jsmaxpix);
	parentwindow.setminmax(jsviewname,jsminpix,jsmaxpix);
	parentwindow.newfile(jsviewname);
}

function drawSliders() {

  minpix1 = new Bs_Slider();
  minpix1.objectName = 'minpix1';
  minpix1.attachOnChange(bsSliderChange1);
  minpix1.width         = 255;
  minpix1.height        = 8;
  minpix1.minVal        = 0;
  minpix1.maxVal        = 255;
  minpix1.valueInterval = 1;
  minpix1.arrowAmount   = 1;
  minpix1.valueDefault  = <? echo $min ?>;
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
  maxpix1.maxVal        = 255;
  maxpix1.valueInterval = 1;
  maxpix1.arrowAmount   = 1;
  maxpix1.valueDefault  = <? echo $max ?>;
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
  document.getElementById('gradientDiv').style.background = 'url('+jsbaseurl+'img/dfe/grad.php?min='+jsminpix+'&max='+jsmaxpix+')'; 
  this.focus();
} 

 // --> 
</script> 

</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" bgcolor="#FFFFFF" onload="init();">
<form method="post" name="adjustform" id="adjust" >
<div id="imagemap" style="z-index:99999;position:absolute;visibility:hidden;border:1px solid black"></div>
<div id="treedata" style="z-index:99999;position:absolute;visibility:hidden;border:1px solid black"></div>
<table border=0>
  <tr>
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
 <td>
	<input id="updatebutton" type="button" alt="Update Image" value="Update" onclick="update();">
 </td>
 </tr>
</table>
</form>
</body>
</html>
