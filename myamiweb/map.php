<?php
require('inc/leginon.inc');
// --- get image parameters from URL
$id=$_GET['id'];
if (!$imgscript=$_GET['imgsc'])
	$imgscript="getimg.php";
$preset=$_GET['preset'];
$session=$_GET['session'];
$tg = ($_GET['tg']) ? '&tg=1' : '';
$sb = ($_GET['sb']) ? '&sb=1' : '';
$minpix = ($_GET['np']) ? '&np='.$_GET['np'] : '';
$maxpix = ($_GET['xp']) ? '&xp='.$_GET['xp'] : '';
$fft = ($_GET['fft']) ? '&fft='.$_GET['fft'] : '';
$filter = ($_GET['flt']) ? '&flt='.$_GET['flt'] : '';
$binning = ($_GET['binning']) ? '&binning='.$_GET['binning'] : '';
$colormap = ($_GET['colormap']) ? '&colormap='.$_GET['colormap'] : '';
$autoscale = ($_GET['autoscale']) ? '&autoscale='.$_GET['autoscale'] : '';
$quality = ($_GET['t']) ? '&t='.$_GET['t']: '';
$psel = ($_GET['psel']) ? '&psel='.urlencode($_GET['psel']) : ''; 
$acepar = ($_GET['g']) ? '&g='.($_GET['g']) : ''; 

$options = $tg.$sb.$minpix.$maxpix.$fft.$filter.$colormap.$autoscale.$psel.$acepar;

$filenamewpath = $leginondata->getFilenameFromId($id,true);
$filename = end(explode("/",$filenamewpath));
$mrcinfo = mrcinfo($filenamewpath);

if (!$imgwidth = $mrcinfo['nx'])
	$imgwidth=1024;
if (!$imgheight= $mrcinfo['ny'])
	$imgheight=1024;

$imgbinning = $_GET['binning'];
if ($_GET['binning']=='auto')
	$imgbinning = ($imgwidth > 1024) ? (($imgwidth > 2048) ? 4 : 2 ) : 1;

// --- set image map size and binning
$imgmapsize=128;
$mapbinning = ($imgwidth> 1024) ? (($imgwidth> 2048) ? 16 : 8 ) : 4;

$ratio = $imgwidth/$imgbinning/$imgmapsize;

// --- window size 512 is set in viewer.js popUpMap(URL)
$areasize=512/$ratio;

// --- for colored images display area in black
$areacolor = ($_GET['colormap']==1) ? "#000000" : "#00FF00";

$imgmapsrc = $imgscript."?preset=".$preset."&session=".$session."&id=".$id."&t=75&s=$imgmapsize&binning=$mapbinning".$options;
$imgsrc = $imgscript."?preset=".$preset."&session=".$session."&id=".$id.$quality.$binning.$options;
?>
<html>
<head>
<title>
MAP: <?php echo $filename; ?>
</title>
<script language="javascript" src="js/draglayer.js"></script>
<script>
var filename="<?php echo $filename; ?>";
var ns6 = (document.getElementById&&!document.all) ? true:false;
var ie = (document.all)? true:false;

var mx=0;
var my=0;

var offsetX = 0;
var offsetY = 0;

var jsimgwidth=<?php echo $imgwidth; ?>;
var jsimgheight=<?php echo $imgheight; ?>;
var jsmapsize = <?php echo $imgmapsize; ?>;
var ratio=<?php echo $ratio; ?>;
var area;
var sbleft=0;
var sbtop=0;
var offsetmapX = 0;
var offsetmapY = 0;

var divmapdoDrag=false;
var doDrag=false;
var sldimgmoveleft;
var sldimgmovetop;

function init() {
	initarea();
	coords_layer = document.getElementById("divcoord");
	map = document.getElementById('divmap');
	d = document.getElementById('divimg');
	d.onscroll=updateArea;
	window.onresize=updateArea;
	this.focus();
}

function initarea() {
	area=document.getElementById("divarea");
}

function mousecoord(e) {
	if (ns6){var mouseX=e.pageX; var mouseY=e.pageY}
	if (ie) {var mouseX=event.x; var mouseY=event.y}
  mx = mouseX;
  my = mouseY;
}

function imgmousedown(e){
}

function imgmouseup(e){
}

function imgmousemove(e) {
  mousecoord(e);
	o=document.getElementById("divimg");
	mapmx=parseInt(o.scrollLeft)+mx;
	mapmy=parseInt(o.scrollTop)+my;
	displayCoord(mapmx+" "+mapmy);

}

function imgmapmousedown(e) {
	if (!e) {e = window.event}
	o=document.getElementById("divmap");
	sldLeft=getAbsLeft(o);
	sldTop=getAbsTop(o);
	sldMouseLeft=getAreaWidth()/2+sldLeft;
  sldMouseTop=getAreaHeight()/2+sldTop;
	setArea(e)
}

function mapmousemove(e) {
  mousecoord(e);
	n_mapx = (mx-offsetmapX)*ratio;
	n_mapy = (my-offsetmapY)*ratio;
	displayCoord(n_mapx+" "+n_mapy);

}

function imgmovemousedown(e)
{
	if (!e) {e = window.event}
	divmapdoDrag=true;
	sldimgmoveleft=e.clientX-offsetmapX;
  sldimgmovetop=e.clientY-offsetmapY;
}

function imgmovemouseup(e)
{
	divmapdoDrag=false;
}

function imgmovemousemove(e)
{
	if (!e) {e = window.event}

	if (divmapdoDrag)
	{
		nx = e.clientX-sldimgmoveleft;
		ny = e.clientY-sldimgmovetop;
		o=document.getElementById("divmap")
		setPosition(o, nx, ny);
		offsetmapX = getAbsLeft(o);
		offsetmapY = getAbsTop(o);
	}
}

function areamousedown(e)
{
	if (!e) {e = window.event}
	doDrag=true;
	o=document.getElementById("divarea");
	sldLeft=getAbsLeft(o);
	sldTop=getAbsTop(o);
	sldMouseLeft=e.clientX-sldLeft+offsetmapX;
  sldMouseTop=e.clientY-sldTop+offsetmapY;
}

function areamouseup(e)
{
	doDrag=false
}

function areamousemove(e)
{
	if (!e) {e = window.event}
	mapmousemove(e);

	if (doDrag)
	{
		setArea(e)
	}
}

function setArea(e) {
		aw = getAreaWidth()
		ah = getAreaHeight()
		maxw = jsmapsize-aw
		maxh = jsmapsize-ah
		nx = e.clientX-sldMouseLeft;
		ny = e.clientY-sldMouseTop;
		nx = (nx>maxw)? maxw : nx
		ny = (ny>maxh)? maxh : ny
		nx = (nx<0)? 0 : nx
		ny = (ny<0)? 0 : ny
		o=document.getElementById("divarea")
		setPosition(o, nx, ny)
		newLocation()
}

function updateArea() {
  ww = ie ? window.document.body.clientWidth : window.innerWidth;
  wh = ie ? window.document.body.clientHeight : window.innerHeight;

	if (o=document.getElementById("divimg")) {
	sbleft=parseInt(o.scrollLeft);
	sbtop=parseInt(o.scrollTop);

  setAreaWidth(ww/ratio);
  setAreaHeight(wh/ratio);
	setAreaTop(sbtop/ratio);
	setAreaLeft(sbleft/ratio);
	}
}

function displayCoord(val) {
	if (coords_layer = document.getElementById("divcoord")) {
		coords_layer.innerHTML = val
	}
}

function newLocation() {
  mapmx = parseInt(getAreaLeft()*ratio);
  mapmy = parseInt(getAreaTop()*ratio);
	o=document.getElementById("divimg");
	o.scrollLeft=mapmx;
	o.scrollTop=mapmy;
}


function getAreaWidth() {
	if (area=getArea())
		return parseInt(area.style.width);
}

function getAreaHeight() {
	if (area=getArea())
     return parseInt(area.style.height);
}

function getAreaLeft() {
	if (area=getArea())
     return parseInt(area.style.left);
}
function getAreaTop() {
	if (area=getArea())
     return parseInt(area.style.top);
}

function setAreaLeft(val) {
  area.style.left= parseInt(val);
}

function setAreaTop(val) {
  area.style.top= parseInt(val);
}

function setAreaWidth(val) {
  area.style.width= parseInt(val);
}

function setAreaHeight(val) {
  area.style.height= parseInt(val);
}

function getArea() {
	if (area=document.getElementById("divarea"))
		return area
	return false
}


	</script>
</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" onload="init();" >
<div id="divmap" 
		style="z-index:2; position:absolute; left:0px; top:0px; background-color:rgb(0,0,0); border: 1px solid #000000;" > 
	<div
		id="divarea"
		style="z-index:99;position:absolute;visibility:visible;width: <?php echo $areasize?>px; height:<?php echo $areasize?>px;border:1px dashed <?php echo $areacolor?>;cursor:move;background-color:transparent;background-image: none"
		onmousedown	= "areamousedown(event)"
		onmouseup		= "areamouseup(event)"
		onmousemove = "areamousemove(event)"
		onmouseout	= "areamouseup(event)"
	></div>
	<img id="imgmap" src="<?php echo $imgmapsrc; ?>"
		onmousemove = "areamousemove(event)"
		onmousedown	= "imgmapmousedown(event)"
	><br>
	<div	id="divcoord"
				style="position:absolute;padding:0px; margin:0px; width:112px; height:15px; background-color:rgb(255,255,200); font-size:12px;"></div>
	<div id="divimgmove" style="position:relative; padding:0px; margin;0px; left:113px; width:15px; height:15px;cursor:move;background:url(img/imgmove.gif) no-repeat; font-size:12px;"
		onmousedown	= "imgmovemousedown(event)"
		onmouseup		= "imgmovemouseup(event)"
		onmousemove = "imgmovemousemove(event)"
		onmouseout	= "imgmovemouseup(event)"
	></div> 
</div>
<div id="divimg" style="z-index:1; position:absolute; width:100%; height:100%; overflow:auto; ">
<img id="img" hspace="0" vspace="0" border="0" src="<?php echo $imgsrc; ?>"
	onmousemove	=	"imgmousemove(event)";
	onmousedown	=	"imgmousedown(event)";
	onmouseup		=	"imgmouseup(event)";
>
</div>
</body>
</html>
