<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/viewer.inc";
require "inc/leginon.inc";
require "inc/particledata.inc";

$imgId=$_GET['id'];
$preset=$_GET['preset'];
$ctftype = $_GET['ctf'];

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo['sessionId'];

$newexpId = $sessionId; // --- variable use by setdatabase() in inc/project.inc
// These require statements need to be here after $newexpId is defined
// in order to set processing database properly
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
<?php

$ctf = new particledata();
if ($ctftype=='ctffind')
	list($ctfdata) = $ctf->getCtfInfoFromImageId($imgId,$order=False,$ctffind=True);
else
	list($ctfdata)  = $ctf->getCtfInfoFromImageId($imgId);

$keys[]='defocus';
$keys[]='defocus1';
if ($ctfdata['angle_astigmatism']) {
	$keys[]='defocus2';
	$keys[]='angle_astigmatism';
}
$keys[]='confidence';
$keys[]='confidence_d';

if ($ctfdata) {
	echo "<font style='font-size: 12px;'>";
	if (is_array($ctfdata))
		foreach($keys as $k) {
			if (!array_key_exists($k,$ctfdata))
				continue;
			$v=$ctfdata[$k];
			if (ereg('defocus',$k))
				echo " <b>$k:</b> ",($leginondata->formatDefocus($v));
			elseif ($v-floor($v)) 
				echo " <b>$k:</b> ".format_sci_number($v,4,2);
			else
				echo " <b>$k:</b> $v";
		}
}
?>
</td>
</tr>
</table>
</font>
</body>
</html>
