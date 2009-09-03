<?php
require '../inc/scalebar.inc';

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
	$type = "image/x-png";
	$ext = "png";
} else {
  $type = "image/jpeg";
	$quality=$t;
	$ext = "jpg";
}

if (!$info && $stackinfoindex==1) {
  $iminfo = imagicinfo($file_hed, $img_num);
  $info = $iminfo['mrc2'];
}

$mrcimg = imagicread($file_hed, $file_img, $img_num);
$maxval=255;
list($pmin, $pmax) = array(0, $maxval);
if ($updateheader)
	mrcupdateheader($mrcimg);
list($pmin, $pmax) = mrcstdevscale($mrcimg, 3);
mrcbinning($mrcimg,$binning);
$img = mrctoimage($mrcimg,$pmin,$pmax);
mrcdestroy($mrcimg);

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

$color=imagecolorallocate($img,128,0,128);
$w=imagecolorallocate($img,255,255,255);
$x1=0;
$y1=$imgh-$yfont;
$x2=strlen($text)*$xfont+1;
$y2=$imgh;
imagefilledrectangle ($img, $x1, $y1, $x2, $y2, $color );
imagestring($img, $fontsize, 1, $y1, $text, $w);

if (is_numeric(trim($_GET['ps'])) && $_GET['sb']==1) {
	$ps = $_GET['ps'];
	$size = imagesx($img);
	$scalebar = new ScaleBar($img, $size, $ps);
	$v = imagesy($img)-12;
	$scalebar->setFontSize(2);
	$scalebar->setoffsetbarY($v);
	$scalebar->display();
}

$filename="image$img_num.$ext";
header( "Content-type: $type ");
header( "Content-Disposition: inline; filename=".$filename);
	if ($t=='png')
		imagepng($img);
	else
		imagejpeg($img,'',$quality);

imagedestroy($img);
?>
