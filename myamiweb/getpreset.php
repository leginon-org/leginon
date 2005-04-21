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
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>
<body leftmargin="5" topmargin="0" bottommargin="0" marginwidth="5" marginheight="0" >
<font face="Arial, Helvetica, sans-serif" size="2">
<?
require('inc/leginon.inc');
$p[]='gridId';
$p[]='mag';
$p[]='defocus';
$p[]='pixelsize';
$p[]='dose';
$id=$_GET['id'];
$preset=$_GET['preset'];
$viewfilename=$_GET['vf'];
if ($id) {
	echo "<font style='font-size: 12px;'>";
	$newimage = $leginondata->findImage($id, $preset);
	$id = $newimage[id];
			$gridId	= $leginondata->getGridId($id);
			$filename = $leginondata->getFilenameFromId($id);
			$presets = $leginondata->getPresets($id, $p);
			if (is_array($presets))
			foreach($presets as $k=>$v)
				if ($k=='defocus')
					echo " <b>$k:</b> ",($leginondata->formatDefocus($v));
				else if ($k=='pixelsize')
					echo " <b>$k:</b> ",($leginondata->formatPixelsize($v));
				else if ($k=='dose') {
					if (!empty($v))
						echo " <b>$k:</b> ",($leginondata->formatDose($v));
				}
				else
					echo " <b>$k:</b> $v";
	if ($viewfilename)
		echo " <br>".$filename."</font>";

}
?>
</font>
</body>
</html>

