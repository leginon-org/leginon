<?php

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
<?php
require 'inc/xmldata.inc';
$p[]='mag';
$p[]='defocus';
$p[]='pixelsize';
$p[]='dose';
$id=$_GET['id'];
$preset=$_GET['preset'];
$viewfilename=$_GET['vf'];
if ($id) {
	echo "<font style='font-size: 12px;'>";
	$xmldata = new xmldata(XML_DATA);
	$imageinfo = $xmldata->getImageInfo($id);
	$filename = $xmldata->getFilenameFromId($id);
	$presets = $xmldata->getPresetData($id);
	$imageinfo = $xmldata->getImageInfo($id);
	if (is_array($presets))
			foreach($presets as $k=>$v)
				if ($k=='defocus')
					echo " <b>$k:</b> ",(format_micro_number($v));
				else if ($k=='pixelsize') {
					$v *= $imageinfo['binning'];
					echo " <b>$k:</b> ",(format_nano_number($v));
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

