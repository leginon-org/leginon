<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

?>
<html>
<head>
<title>Leginon Data Viewer</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<link rel="stylesheet" type="text/css" href="css/view.css">


<?
require ('inc/leginon.inc');
require ('inc/mrc.inc');
if ($viewtree=='on') {
	$state = 'checked';
	$treeframe=1;
} else {
	$state = '';
	$treeframe=0;
}
// --- View setup based on the browser and platform type --- //
if (browser('b') =='Netscape' && strstr(browser('p'), 'Win')) {
	$mvtextsize=15;
	$cvcols=15;
	$mvcols=31;
} else if (browser('b')=='MSIE') { 
	$cvcols=35;
	$mvtextsize=30;
	$mvcols=60;
} else if (!(browser('b') =='Netscape' && (browser('v')< 5))) {
	$cvcols=35;
	$mvtextsize=30;
	$mvcols=60;
} else { 
	$cvcols=25;
	$mvtextsize=35;
	$mvcols=42;
}

// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($expId)) ? $lastId : $expId;
$sessioninfo =  $leginondata->getSessionInfo($expId);

// --- Get all session and session Ids
$experiment = array();
$lexpId = array();
$sessions = $leginondata->getSessions('description');


// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($expId);
$def_label = $datatypes[0];

// --- Get current user preferences
$ftemplate='getparentimgtarget.php';

if ($mvsel=='' ) $l1=$def_label; else $l1=$mvsel;

$filenames = $leginondata->getFilenames($expId, $l1);


?>

<script src="js/LibCrossBrowser.js"></script>
<script src="js/EventHandler.js"></script>
<script src="js/Bs_Slider.class.js"></script>
<script src="js/Bs_FormUtil.lib.js"></script>
<script src="js/viewiframe.js"></script>
<script src="js/tree.js"></script>
<script><!--
<?
if (!$min=$_POST['pmin'])
	$min=0;
if (!$max=$_POST['pmax'])
	$max=255;
if (!$size=$_POST['s'])
	$size=512;
if (!$quality=$_POST['t'])
	$quality=80;

$arrayurl = explode("/", $PHP_SELF);
array_pop($arrayurl);
$baseurl=implode("/",$arrayurl);


echo"
var jsminpix = $min;
var jsmaxpix = $max;
var jssize = $size;
var jsquality = $quality;
var jsimgwidth = jssize;
var jsimgheight = jssize;
var jszoom=100;
var jsbaseurl = '$baseurl/';
";
?>
var ns4 = (document.layers)? true:false;
var ns6 = (document.getElementById&&!document.all) ? true:false;
var ie = (document.all)? true:false;

var vmap=true;
var vtree=true;
var newimg;
var dragapproved;
var tempx;
var tempy;
var imgmapoffsetx=2;
var imgmapoffsety=17;
var crossobj;
var treedata;

var coordx=0;
var coordy=0;
var mx=0;
var my=0;
var mapmx=0;
var mapmy=0;
var mapoffsetx;
var mapoffsety;
var initx=0;
var inity=0;
var cx=256;
var cy=256;
var jsmapsize = 256;
var ratiomap=jssize/jsmapsize;
var mapimg;
var hidestr="hide ";
var viewstr="view ";
var viewlink;
var viewtreelink;

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

  zoom1 = new Bs_Slider();
  zoom1.objectName = 'zoom1';
  zoom1.attachOnChange(bsSliderChange4);
  zoom1.width         = 226;
  zoom1.height        = 16;
  zoom1.minVal        = 10
  zoom1.maxVal        = 200;
  zoom1.valueInterval = 1;
  zoom1.valueDefault  = 100;
  zoom1.imgBasePath   = 'img/';
  zoom1.setBackgroundImage('dfe/slider_swing2.gif', 'no-repeat');
  zoom1.setSliderIcon('dfe/cursor_swing.gif', 15, 16);
  zoom1.useInputField = 1;
  zoom1.colorbar = new Object();
  zoom1.colorbar['color']           = 'cdefef';
  zoom1.colorbar['height']          = 3;
  zoom1.colorbar['widthDifference'] = 0;
  zoom1.colorbar['offsetLeft']      = 1;
  zoom1.colorbar['offsetTop']       = 6;
  zoom1.draw('zoom1Div');
}


  <?
  $imgmv = trim($ftemplate);
  echo "var jsprefId = \"$prefId\"; \n";
  echo "var jsName = \"$user\"; \n";
  echo "var jsexpId = \"".$expId."\"; \n";
  echo "var path = \"$path\"; \n";
  echo "var jsfileId;  \n";
  echo "var jsfile; \n";
  echo "var jsimgmv = \"".trim($ftemplate)."\"; \n";
  echo "var jsmvId   = \"".trim($mvId)."\"; \n";
  echo "var jspremv = \"".trim($mvsel)."\"; \n";

?>


function init(){
  initCrossBrowserLib();
  drawSliders();
  jsminpix = minpix1.valueDefault;
  jsmaxpix = maxpix1.valueDefault;
  document.getElementById('gradientDiv').style.background = 'url('+jsbaseurl+'img/dfe/grad.php?min='+jsminpix+'&max='+jsmaxpix+')'; 

 if (document.listform.l_quality.length !=0) {
     for (var i = 0; i < document.listform.l_quality.length; i++) {
          if (document.listform.l_quality.options[i].value == jsquality) {
           document.listform.l_quality.options[i].selected=true;
          }
     }
 }
 if (document.listform.l_size.length !=0) {
     for (var i = 0; i < document.listform.l_size.length; i++) {
          if (document.listform.l_size.options[i].value == jssize) {
           document.listform.l_size.options[i].selected=true;
          }
     }
 }
     var currentfile="";
 if (document.listform.allfile.length !=0) {
     for (var i = 0; i < document.listform.allfile.length; i++) {
      if (document.listform.allfile.options[i].defaultSelected == true) {
          document.listform.allfile.options[i].selected=true;
          currentfile=document.listform.allfile.options[document.
          listform.allfile.selectedIndex].text;
      } 
     }
     if (currentfile=="") {
          currentfile=document.listform.allfile.options[0].text;
          document.listform.allfile.options[0].selected=true;
     }
     newfile();
<? if ($treeframe!=0) echo "getdata();"; ?>
 } 
} 

 // --> 
</script> 

</head>
<body bgcolor="#FFFFFF" onload="init();ir();initmap();inittree();">
<form method="post" name="listform" id="adjust" onsubmit="return sendForm('imageviewer.php', 'prefId')">
 <input type="hidden" name="ncfid" value="">
  <table border="0" cellpadding="1" cellspacing="1" height="600" >
      <tr>
	<td vAlign="bottom" height="25" width="150"><b>Session</b></td>
        <td vAlign="bottom" bgColor="#FFFFFF" height="10" >
		<select name="expId" onchange="newexp()">
			<?
			foreach ($sessions as $session) {
				if ($session[id]==$expId) $s='selected'; else $s='';
				echo '<option value='.$session[id].' '.$s.' >'.$session[name]; 
      			} 
			?>
		</select>
	</td>
	<td rowspan="4">
<div id="imagemap" style="z-index:99999;position:absolute;visibility:hidden;border:1px solid black"></div>
<div id="treedata" style="z-index:99999;position:absolute;visibility:hidden;border:1px solid black"></div>
	</td>
      </tr>
      <tr>
	<td valign="top">
	<b>Image Adjust</b>
	</td>
	<td>

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
 <td>
	<input id="updatebutton" type="button" alt="Update Image" value="Update" onclick="newfile();updatemap();">
 </td>
 <td>
	<a class=header href="javascript:void(0)" onclick="viewmap();" ><span id="viewlink">view map<span>&raquo;</a>
	<a class=header href="javascript:void(0)" onclick="viewtreediv();" ><span id="viewtreelink">view tree<span>&raquo;</a>
 </td>
 </tr>
  <tr>
   <td>
	<label for="zoom1Div">zoom</label>
    </td>
    <td width="250" valign="top">
      <div id="zoom1Div"></div>
    </td>
    <td>
	%
    </td>
  </tr>
</table>
<table>
  <tr>
    <td colspan="2">
      quality: <select id=list size="1" name="l_quality" 
		onchange = "newfile();" > 
		<option value="png">png
	<?
		$qualitymax=100;
		$qualitymin=50;
		$qualityincrement=5;
		for($q=$qualitymax; $q>=$qualitymin; $q-=$qualityincrement) 
			echo "<option value=$q $s>jpg $q \n";
	?>
	</select>
      size: <select id=list size="1" name="l_size"
		onchange = "newscale();" > 
		<option value="4096">4096x4096
		<option value="2048">2048x2048
		<option value="1024">1024x1024
		<option value="512">512x512
		<option value="256">256x256
	</select>
	<input id=coord type="text" name="tq" value="" >
    </td>
  </tr>
</table>



	
	</td>
      </tr>
      <tr>
	<td valign="top">
	<b>Filename</b></td>
	<td valign="top">
	 <iframe name="ifpmv" 
                        src="getpreset.php?vf=1&id=<?=$fileId[0]?>"
                        frameborder="0" width="400" height="35"
                        marginheight="1" marginwidth="5"
                        scrolling="no" ></iframe>
	</td>
      </tr>
      <tr vAlign="top">
	<td height="462" rowSpan="2" >
		<select name="allfile" onchange="newfile();updatemap();getdata();"
		 size="40">
			<?
		foreach ($filenames as $filename) {
			if ($filename[id]==$allfile ) $s='selected'; else $s='';
			$filestr = ereg_replace($sessioninfo[Name].'+_(.*)\.mrc', '\1', $filename[name]);
			$filestr = ereg_replace('00', '', $filestr);
			echo '<option value="'.$filename[id].'" '.$s.' >'.$filestr." \n"; 
		}
			?> 
		</select>
	</td>
	<td height="462" rowspan="2">
<?
 require('inc/ifmainview.inc');
?> 
	</td>
      </tr>
    </table>
</form>
</body>
</html>
<?


?>
