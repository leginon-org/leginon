<?php
$file_hed=$_GET['hed'];
$file_img=$_GET['img'];
$img_num=$_GET['n'];
$info=$_GET['i'];
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


$mrcimg = imagicread($file_hed, $file_img, $img_num);
$maxval=255;
list($pmin, $pmax) = array(0, $maxval);
if ($updateheader)
	mrcupdateheader($mrcimg);
list($pmin, $pmax) = mrcstdevscale($mrcimg, $maxval, 3);
mrcbinning($mrcimg,$binning);
$img = mrctoimage($mrcimg,$pmin,$pmax);
mrcdestroy($mrcimg);

$text="$img_num";
if ($info) {
  $text.=", $info";
}

$color=imagecolorallocate($img,128,0,128);
$w=imagecolorallocate($img,255,255,255);
$x1=0;
$y1=imagesy($img)-15;
$x2=strlen($text)*6;
$y2=imagesy($img);
imagefilledrectangle ($img, $x1, $y1, $x2, $y2, $color );
imagestring($img, 2, 1, $y1, $text, $w);

$filename="image$img_num.$ext";
header( "Content-type: $type ");
header( "Content-Disposition: inline; filename=".$filename);
	if ($t=='png')
		imagepng($img);
	else
		imagejpeg($img,'',$quality);

imagedestroy($img);
?>
