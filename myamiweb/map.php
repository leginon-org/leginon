<?
require('inc/leginon.inc');
$id=$_GET[id];
$preset=$_GET[preset];
$session=$_GET[session];
$tg = ($_GET[tg]) ? '&tg=1' : '';
$sb = ($_GET[sb]) ? '&sb=1' : '';
$minpix = ($_GET[np]) ? '&np='.$_GET[np] : '';
$maxpix = ($_GET[xp]) ? '&xp='.$_GET[xp] : '';
$fft = ($_GET[fft]) ? '&fft='.$_GET[fft] : '';
$options = $tg.$sb.$minpix.$maxpix.$fft;

$filename = $leginondata->getFilename($id);
$imgsrc = "getparentimgtarget.php?preset=".$preset."&session=".$session."&id=".$id."&t=80&s=256".$options;
?>
<html>
<head>
<title>
MAP: <?=$filename; ?>
</title>
<script>
var ns4 = (document.layers)? true:false;
var ns6 = (document.getElementById&&!document.all) ? true:false;
var ie = (document.all)? true:false;

var coordx=0;
var coordy=0;
var mx=0;
var my=0;
var mapmx=0;
var mapmy=0;
var initx=0;
var inity=0;
var cx=256;
var cy=256;
var jsmapsize = 256;
var my1;
var jsimgwidth;
var jsimgheight;
var ratio=1;
var deoffsetx=0;
var deoffsety=0;
var move=false;
var initmousex=0;
var initmousey=0;

function mousecoord(e) {
        if (ns4||ns6) {var mouseX=e.pageX; var mouseY=e.pageY}
        if (ie) {var mouseX=event.x; var mouseY=event.y}
	mx = mouseX;
	my = mouseY;
}

function mousedown(e){
	mousecoord(e);
	initmousex=mx;
	initmousey=my;
	size_timer=setInterval('getImageSize()',250);	
	getRatio();
	newLocation();
		if (move)
			move=false;
		else
			move=true;
}

function getRatio() {
	ratio = jsimgwidth/jsmapsize;
}

function getImageSize() {
	if (my1.document.getElementById('imgmvId')) 
	{
		jsimgwidth = my1.document.getElementById('imgmvId').width;
		jsimgheight = my1.document.getElementById('imgmvId').height;
		clearInterval(size_timer);
	}
} 

function mouseup(e){
	if (Math.abs(initmousex-mx)>5 && Math.abs(initmousex-mx)>5)
		if (move)
			move=false;
		else
			move=true;
}

function newLocation() {
	getIframesize();
	if (ns6) {
		initx = window.my1.pageXOffset; 
		inity = window.my1.pageYOffset;
	}
	if (ie) {
		deoffsetx = window.my1.document.body.scrollLeft;
		deoffsety = window.my1.document.body.scrollTop;
	}
	mapmx = parseInt(mx*ratio);
	mapmy = parseInt(my*ratio);
	window.my1.scrollBy(mapmx-initx-cx-deoffsetx,mapmy-inity-cy-deoffsety);
}

function mousemove(e) {
	mousecoord(e);
	if (move)
		newLocation();
}

function getKey(e) {
	// --- Spacebar => unicode 32
	var spacebarunicode = 32;
        if (ns6) {var unicode = e.which;}
        if (ie)  {var unicode = event.keyCode;}
	if (unicode == spacebarunicode)
		if (move)
			move=false;
		else
			move=true;
}

function getIframesize(){
	var iframewidth = ie ? my1.document.body.clientWidth : my1.innerWidth;
	var iframeheight = ie ? my1.document.body.clientHeight : my1.innerHeight;
	cx=parseInt(iframewidth/2);
	cy=parseInt(iframeheight/2);
}

function init() {
	var URL = 'nw.php?preset=<?=$preset?>&session=<?=$session?>&id=<?=$id?><?=$options?>';
	my1=window.open(URL, 'my1', 'left=300,top=0,height=512,width=512,toolbar=0,scrollbars=1,location=0,statusbar=0,menubar=0,resizable=1,alwaysRaised=yes');
        document.newimgmv.onmousemove=mousemove;
        document.newimgmv.onmousedown=mousedown;
        document.newimgmv.onmouseup=mouseup;
	document.onkeypress=getKey;
	this.focus();
}


function imgIsComplete() {
	if (my1.document.getElementById('imgmvId')) 
	if (my1.document.getElementById('imgmvId').complete) {
		clearInterval(img_timer)
		jsimgwidth = my1.document.getElementById('imgmvId').width;
		jsimgheight = my1.document.getElementById('imgmvId').height;
	}
}

function exit() {
	my1.close();
}

</script>

</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" onload="init();" onUnload="exit();">

<img name="newimgmv" hspace="0" vspace="0" border="0" src="<?=$imgsrc?>">
</body>
</html>
