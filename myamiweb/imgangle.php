<?php
require('inc/graphutil.inc');
$angle=$_GET['a'];
$w=24;
$h=24;
$cx=$w/2;
$cy=$h/2;
$cw=$w*.9;
$ch=$h*.9;
$angle_rad=$angle*PI()/180;

$img = imagecreatetruecolor($w,$h);
//imageantialias($img,true);
$b=imagecolorallocate($img,255,255,255);
imagefill($img,0,0, $b);
imagecolortransparent($img,$b);
$t=imagecolorallocate($img,189,206,221);
$rt=imagecolorallocate($img,255,0,0);
imageellipse($img,$cx,$cy,$cw+2,$ch+2,$t);
imageline($img,$cx-$cw/2,$cy,$cx+$cw/2,$cy,$t);
$poly = array 
			(
			$cx-$cw/2,$cy,
			$cx-$cw/2,$cy,
			$cx+$cw/2,$cy,
			$cx+$cw/2,$cy
		);
$graphutil = new graphutil();
$poly = $graphutil->rotatePoly($poly, $angle_rad, $cx, $cy);
imagepolygon($img, $poly,count($poly)/2, $rt);

imagepng($img);
imagedestroy($img);
?>
