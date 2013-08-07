<?php
require_once dirname(__FILE__).'/../config.php';
require_once '../inc/scalebar.inc';
require_once "../inc/image.inc";
require_once "../inc/imagerequest.inc";

$file_hed=$_GET['hed'];
$file_img=$_GET['img'];
$img_num=$_GET['n'];
$info=$_GET['i'];
$stackinfoindex=$_GET['k'];
$updateheader=($_GET['uh']==1) ? true : false;
# don't remove
$updateheader=true;

if (!$t = $_GET['t'])
	$t=80;
if (!$binning = $_GET['b'])
	$binning=1;
if ($t=='png') {
	$ext = "png";
	$oformat = 'PNG';
} else {
	$quality=$t;
	$ext = "jpg";
	$oformat = 'JPEG';
}

// create imageRequester and imageUtil instances to begin.
$imagerequest = new imageRequester();
$imageUtil = new imageUtil();

$pic = $file_hed;
	
// frame number for redux
$frame=$img_num;
// scale type is stdev only for now
$scaletype = 'stdev';
$arg1 = -3;
$arg2= 3;
// find out the proper x, y for display
$imginfo = $imagerequest->requestInfo($pic,$frame);
$dimx = $imginfo->nx;
$dimy = $imginfo->ny;
// eman uses i4lp to pass number of particles in class average imagic file
if (!$info && $stackinfoindex==1) $info = $imginfo->i4lp;

$xyDim = $imageUtil->imageBinning($dimx, $dimy, $binning);
// request image
$imgstr = $imagerequest->requestImage($pic,'PNG',$xyDim,$scaletype,$arg1,$arg2,0,false,false,true,$frame);
if (empty($imgstr)) exit();
$img = imagecreatefromstring($imgstr);

$text="$img_num";
if ($info) {
  $text.=", $info";
}

$imgh=imagesy($img);
$fontsize=2;
$yfont=14;
$xfont=6;

if ($imgh<128) {
  $fontsize=1;
  $yfont=8;
  $xfont=5;
}

// --- display info --- //
if (trim($_GET['di'])==1) {
	// some PNG images can not allocate purple as background color. Using imagecolorresolve
	// avoid this problem even though the backgroupd might not be purple if the image
	// is greyscale only
	$color=imagecolorresolve($img,128,0,128);
	$w=imagecolorresolve($img,255,255,255);
	$x1=0;
	$y1=$imgh-$yfont;
	$x2=strlen($text)*$xfont+1;
	$y2=$imgh;
	imagefilledrectangle ($img, $x1, $y1, $x2, $y2, $color );
	imagestring($img, $fontsize, 1, $y1, $text, $w);
}

if (is_numeric(trim($_GET['ps'])) && $_GET['sb']==1) {
	$ps = $_GET['ps'] * $binning;
	$size = imagesx($img);
	$scalebar = new ScaleBar($img, $size, $ps);
	$v = imagesy($img)-12;
	$scalebar->setFontSize(2);
	$scalebar->setoffsetbarY($v);
	$scalebar->display();
}

$filename="image$img_num.$ext";

$imagerequest->displayImageObj($img,$oformat,$quality,$filename);
?>
