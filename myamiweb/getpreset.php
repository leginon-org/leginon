<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

?>
<?php
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
?>
<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="5" marginheight="0" >
<font face="Arial, Helvetica, sans-serif" size="2">
<table cellpadding="0" cellspacing="0">
<tr valign="top">
<td>
<?
$p[]='gridId';
$p[]='mag';
$p[]='defocus';
$p[]='pixelsize';
$p[]='dose';
$p[]='exposure time';
$p[]='tilt';
$str_tilt="";
$id=$_GET['id'];
$preset=$_GET['preset'];
$viewfilename=$_GET['vf'];
$showtilt=$_GET['tl'];
if ($id) {
	echo "<font style='font-size: 12px;'>";
	$newimage = $leginondata->findImage($id, $preset);
	$id = $newimage[id];
	$imageinfo = $leginondata->getImageInfo($id);
	$gridId	= $leginondata->getGridId($id);
	$projectdata = new project();
	if($projectdata->checkDBConnection()) {
		$gridinfo = $projectdata->getGridInfo($gridId);
		if ($gridId)
			echo '<a class="header" target="gridinfo" href="'.$PROJECT_URL.'getgrid.php?gridId='
				.$gridId.'">grid#'.$gridinfo[number].' info&raquo;</a>';
	}
	list($filename) = $leginondata->getFilename($id);
	$presets = $leginondata->getPresets($id, $p);
	if (is_array($presets))
		foreach($presets as $k=>$v)

			if ($k=='defocus')
				echo " <b>$k:</b> ",($leginondata->formatDefocus($v));
			else if ($k=='pixelsize') {
				$v *= $imageinfo['binning'];
				echo " <b>$k:</b> ",($leginondata->formatPixelsize($v));
			}
			else if ($k=='tilt' && (abs($v) > 1 || $showtilt)) {
				$angle=$v;
				$str_tilt=" <b>$k:</b> ".(format_angle_degree($v));
			}
			else if ($k=='tilt')
				continue;
			else if ($k=='dose') {
				if (!empty($v))
					if($presets['exposure time'] && !empty($imageinfo['exposure time']))
						$dose = $v*$imageinfo['exposure time']/$presets['exposure time'];
					else
						$dose = $v;
					echo " <b>$k:</b> ",($leginondata->formatDose($dose));
			}
			else if ($k=='exposure time')
				continue;
			else
				echo " <b>$k:</b> $v";
	if ($str_tilt) {
		echo $str_tilt;
		echo "&nbsp;<img src='imgangle.php?a=".$angle."'>";
	}
	if ($viewfilename && !$str_tilt)
		echo " <br />".$filename['filename']."</font>";
}
?>
</td>
</tr>
</table>
</font>
</body>
</html>
