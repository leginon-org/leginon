<?php
require 'inc/leginon.inc';
// --- get image parameters from URL
$id=$_GET['id'];
if (!$imgscript=$_GET['imgsc'])
	$imgscript="getimg.php";
$preset=$_GET['preset'];
$session=$_GET['session'];
$tg = ($_GET['tg']) ? '&tg=1' : '';
$sb = ($_GET['sb']) ? '&sb=1' : '';
$sb='';
$minpix = ($_GET['np']) ? '&np='.$_GET['np'] : '';
$maxpix = ($_GET['xp']) ? '&xp='.$_GET['xp'] : '';
$fft = ($_GET['fft']) ? '&fft='.$_GET['fft'] : '';
$filter = ($_GET['flt']) ? '&flt='.$_GET['flt'] : '';
$binning = ($_GET['binning']) ? '&binning='.$_GET['binning'] : '';
$autoscale = ($_GET['autoscale']) ? '&autoscale='.$_GET['autoscale'] : '';
$quality = ($_GET['t']) ? '&t='.$_GET['t']: '';
$psel = ($_GET['psel']) ? '&psel='.urlencode($_GET['psel']) : ''; 
$nptcl = ($_GET['nptcl']) ? '&nptcl='.$_GET['nptcl'] : '';
$acepar = ($_GET['g']) ? '&g='.($_GET['g']) : ''; 
$gradient= ($_GET['gr']) ? '&gr='.$_GET['gr'] : '';
$autoscale = ($_GET['autoscale']) ? '&autoscale='.$_GET['autoscale'] : '';

$options = $tg.$sb.$minpix.$maxpix.$fft.$filter.$colormap.$autoscale.$psel.$acepar.$gradient.$autoscale.$nptcl;

$nimgId = $leginondata->findImage($id, $preset);
$imginfo = $leginondata->getImageInfo($nimgId['id']);

if (!$imgwidth = $imginfo['dimx'])
	$imgwidth=1024;
if (!$imgheight= $imginfo['dimy'])
	$imgheight=1024;

$imgbinning = $_GET['binning'];
if ($_GET['binning']=='auto')
	$imgbinning = ($imgwidth > 1024) ? (($imgwidth > 2048) ? 4 : 2 ) : 1;

// --- set image map size and binning
$imgmapsize=128;
$mapbinning = ($imgwidth> 1024) ? (($imgwidth> 2048) ? 16 : 8 ) : 4;

$ratio = $imgwidth/$imgbinning/$imgmapsize;

// --- for colored images display area in black
$areacolor = ($_GET['colormap']==1) ? "#000000" : "#00FF00";

// --- set scale
$imgsize = ($imgbinning) ? $imgwidth/$imgbinning : $imgwidth;
if (!$imgsize)
	$imgsize=1;
$imgratio = $imgwidth/$imgsize ;
$pixelsize = $imginfo['pixelsize']*$imginfo['binning']*$imgratio;
$filename = $imginfo['filename'];

$imgmapsrc = $imgscript."?preset=".$preset."&session=".$session."&id=".$id."&t=75&s=$imgmapsize&binning=$mapbinning".$options;
$imgsrc = $imgscript."?preset=".$preset."&session=".$session."&id=".$id.$quality.$binning.$options;

?>
<html>
<head>
<title>
MAP: <?php echo $filename; ?>
</title>
<script language="javascript" src="js/draglayer.js"></script>
<script language="javascript" src="js/cross.js"></script>
<script language="javascript" src="js/scale.js"></script>
<script>
var filename="<?=$filename; ?>"
var pixsize ="<?=$pixelsize; ?>"
var jsimgwidth=<?=$imgwidth; ?>

var jssize=<?=$imgsize; ?>

var jsimgheight=<?=$imgheight; ?>

var jsmapsize = <?=$imgmapsize; ?>

var ratio=<?=$ratio; ?>

var mx=0
var my=0
var offsetX=0
var offsetY=0
var sbleft=0
var sbtop=0
var offsetmapX=0
var offsetmapY=0
var pixmeasure=0

var divmapdoDrag=false
var startmeasure=false
var bt_ruler_state=false
var doDrag=false
var sldimgmoveleft
var sldimgmovetop
var markstart
var markstop
var btruler
var area
var map
var img
var scale
var scalebarlabel
var coords_layer
var targets_layer
var divpix

var ns6 = (document.getElementById && !document.all) ? true:false
var ie = (document.all)? true:false

function init() {
	area=document.getElementById("divarea")
	coords_layer=document.getElementById("divcoord")
	map=document.getElementById('divmap')
	targets_layer=document.getElementById('targets')
	img=document.getElementById('divimg')
	btruler=document.getElementById("btruler")
	divpix=document.getElementById("divpix")
	img.onscroll=updateArea
	window.onresize=updateArea
	this.focus()
	area.style.visibility="visible"
	setScalebar() 
	updateArea()
}

function setScalebar() {
	scalebardata=findScale(jssize, pixsize)
	if (scale=document.getElementById("divscale")) {
		scale.style.width=scalebardata[0]
		scalebarlabel=document.getElementById("divscalebarlabel")
		scalebarlabel.innerHTML=textshadow(scalebardata[1])
		scale.style.visibility="visible"
	}
}

function textshadow(text) {
	return '<span style="display: block; line-height: 1em; color: #000; background-color: transparent; white-space: nowrap;" >'+text+'<span style="display: block; margin-top: -1.05em; margin-left: -0.1ex; color: #fff; background-color: transparent;">'+text+'</span></span>'

}

function setruler() {
	bg = (bt_ruler_state) ? "#C8D0D4" : "#00BABB"
	btruler.style.backgroundColor=bg
	if (bt_ruler_state) {
		bt_ruler_state=false
	} else {
		bt_ruler_state=true
	}
}

function mousecoord(e) {
	if (ns6){var mouseX=e.pageX; var mouseY=e.pageY}
	if (ie) {var mouseX=event.x; var mouseY=event.y}
  mx = mouseX;
  my = mouseY;
}

function imgmousedown(e){
	if (!bt_ruler_state)
		return
	if (!startmeasure) {
		startmeasure=true;
			targets_layer.innerHTML = drawcross(mapmx, mapmy, 16, "#00FF00", 'markstart', '')
			markstart = document.getElementById("markstart");
		} else {
			startmeasure=false;
			targets_layer.innerHTML += drawcross(mapmx, mapmy, 16, "#00FF00", 'markstop', '')
			markstop = document.getElementById("markstop");
			pixmeasure = getDistance();
			displayCoord(mapmx+" "+mapmy)
	}
}

function imgmouseup(e){
}

function imgmousemove(e) {
  mousecoord(e);
	if (img) {
		mapmx=parseInt(img.scrollLeft)+mx;
		mapmy=parseInt(img.scrollTop)+my;
		displayCoord(mapmx+" "+mapmy);
	}

}

function imgmapmousedown(e) {
	if (!e) {e = window.event}
	sldLeft=getAbsLeft(map);
	sldTop=getAbsTop(map);
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
		setPosition(map, nx, ny);
		offsetmapX = getAbsLeft(map);
		offsetmapY = getAbsTop(map);
	}
}

function areamousedown(e)
{
	if (!e) {e = window.event}
	doDrag=true;
	sldLeft=getAbsLeft(area);
	sldTop=getAbsTop(area);
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
		maxw = jsmapsize-aw-1
		maxh = jsmapsize-ah-1
		nx = e.clientX-sldMouseLeft
		ny = e.clientY-sldMouseTop
		nx = (nx>maxw)? maxw : nx
		ny = (ny>maxh)? maxh : ny
		nx = (nx<0)? 0 : nx
		ny = (ny<0)? 0 : ny
		setPosition(area, nx, ny)
		newLocation()
}

function updateArea() {
  ww = ie ? window.document.body.clientWidth : window.innerWidth
  wh = ie ? window.document.body.clientHeight : window.innerHeight
	ww-=25
	wh-=25

	scale.style.top=wh-50

	sbleft=parseInt(img.scrollLeft);
	sbtop=parseInt(img.scrollTop);

	aw = Math.round(ww/ratio)
	ah = Math.round(wh/ratio)
	maxw = jsmapsize-2
	maxh = jsmapsize-2
	aw = (aw>maxw) ? maxw : aw
	ah = (ah>maxh) ? maxh : ah
  setAreaWidth(aw)
  setAreaHeight(ah)
	setAreaTop(sbtop/ratio);
	setAreaLeft(sbleft/ratio);
}

function displayCoord(val) {
	if (coords_layer) { 
		if (pixmeasure) {
				val += " pix: "+pixmeasure;
				divpix.innerHTML = formatpixsize(pixmeasure)
		}
		coords_layer.innerHTML = val
	}
}

function formatpixsize(val) {
		ps = parseFloat(pixsize)
		val *= ps
		val /= 1e-9
		return val.toFixed(2)+" nm"
}

function newLocation() {
  mapmx = parseInt(getAreaLeft()*ratio)
  mapmy = parseInt(getAreaTop()*ratio)
	img.scrollLeft=mapmx
	img.scrollTop=mapmy
	displayCoord(img.scrollLeft+' '+img.scrollTop)
}


function getAreaWidth() {
	if (area)
		return parseInt(area.style.width)
}

function getAreaHeight() {
	if (area)
     return parseInt(area.style.height)
}

function getAreaLeft() {
	if (area)
     return parseInt(area.style.left)
}
function getAreaTop() {
	if (area)
     return parseInt(area.style.top)
}

function setAreaLeft(val) {
  area.style.left=parseInt(val)
}

function setAreaTop(val) {
  area.style.top=parseInt(val)
}

function setAreaWidth(val) {
  area.style.width=parseInt(val)
}

function setAreaHeight(val) {
  area.style.height=parseInt(val)
}

function getDistance() {
		x = parseInt(markstop.style.left) - parseInt(markstart.style.left);
		y = parseInt(markstop.style.top) - parseInt(markstart.style.top);
		return Math.round(Math.sqrt(x*x + y*y));
}


</script>
</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" onload="init();" >
<div id="divscale" style="border: 1px solid rgb(0, 0, 0); z-index: 2; position: absolute; visibility:hidden; width:0px; height:3px; left: 10px; color: white; background-color: rgb(0, 0, 0);"><div style="border: 1px solid white;"></div><div id="divscalebarlabel" style="position: absolute; padding-left:5px; padding-top:2px; font-family:Arial; padding-right:5px;"></div></div>
<div id="divmap" 
		style="z-index:2; position:absolute; left:0px; top:0px; background-color:rgb(0,0,0); border: 1px solid #000000;" > 
	<div
		id="divarea"
		style="z-index:99;position:absolute;visibility:hidden;width:0px; height:0px;border:1px dashed <?=$areacolor?>;cursor:move;background-color:transparent;background:url(img/un.gif)"
		onmousedown	= "areamousedown(event)"
		onmouseup		= "areamouseup(event)"
		onmousemove = "areamousemove(event)"
		onmouseout	= "areamouseup(event)"
	></div>
	<div id="imgmap" style="position:relative; height:<?=$imgmapsize?>px; width:<?=$imgmapsize?>px; background:url('<?=$imgmapsrc?>')"
		onmousemove = "areamousemove(event)"
		onmousedown	= "imgmapmousedown(event)" ></div>
	<div	id="divcoord"
				style="position:relative;padding:0px; margin:0px; width:128px; height:15px; background-color:rgb(255,255,200); font-family:Arial; font-size:12px;"></div>
<div style="position:relative; border:1px solid #000000; padding:0px; margin:0px; left: -1px; height: 19px; width: 15px;">
<button style="padding:0px; margin:0px; background-color:#C8D0D4; border:0px solid #F0F0F0; width:22px; height:20px;" id="btruler" type="button" onClick="setruler()"><img style="padding:0px; margin:0px; border:0px" hspace="0" vspace="0" border="0" src="img/ruler.png"></button>
	<div	id="divpix"
				style="position:absolute;padding-left:3px; margin:0px; border:0px solid #000000; top:0px; left:23px; width:85px; height:20px; background-color:rgb(255,255,200); font-family:Arial; font-size:12px;"></div>
	<div id="divimgmove" style="position:absolute; background-color:rgb(225,225,225); padding:0px; margin;0px; top:0px; left:108px; width:20px; height:20px;cursor:move; font-family:Arial; font-size:12px;"
		onmousedown	= "imgmovemousedown(event)"
		onmouseup		= "imgmovemouseup(event)"
		onmousemove = "imgmovemousemove(event)"
		onmouseout= "imgmovemousemove(event)"
	><div style="position:relative; padding:0px; margin;0px; top:2px; left:3px; width:15px; height:15px; background:url(img/imgmove.gif) no-repeat"></div></div>
</div>
</div>
<div id="divimg" style="z-index:1; position:absolute; width:100%; height:100%; overflow:auto;cursor:crosshair; ">
<div id="img" style="position:absolute; top:0px; left:0px; width:<?=$imgsize;?>px; height:<?=$imgsize;?>; background:url('<?php echo $imgsrc; ?>')"
	onmousemove	=	"imgmousemove(event)";
	onmousedown	=	"imgmousedown(event)";
	onmouseup		=	"imgmouseup(event)";
></div>
<div id="targets" style="z-index:2;border:0px;" ></div>
</div>
</body>
</html>
