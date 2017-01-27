<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/viewer.inc";
require_once "inc/leginon.inc";
require_once "inc/particledata.inc";

$imgId=$_GET['id'];
$preset=$_GET['preset'];
$ctftype = $_GET['ctf'];
$runId = $_GET['r'];

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo['sessionId'];

$newexpId = $sessionId; // --- variable use by setdatabase() in inc/project.inc
// These require statements need to be here after $newexpId is defined
// in order to set processing database properly
require_once "inc/project.inc";

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
list($ctfdata) = $ctf->getCtfInfoFromImageId($imgId,$order=False,$ctftype,$runId);

$ctfdata['cs'] = $leginondata->getCsValueFromSession($sessionId);

$keys[]='runname';
// estimate parameters
$keys[]='defocus';
$keys[]='defocus1';
// assume defocus1 and defocus2 are equal if equal at Angstrom level
$epsilon = 1e-10;
if (abs($ctfdata['defocus1'] - $ctfdata['defocus2']) > $epsilon) {
	$keys[]='defocus2';
	$keys[]='angle_astigmatism';
}
$keys[]='amplitude_contrast';
if (abs($ctfdata['extra_phase_shift']) > 0.001) {
	$keys[]='extra_phase_shift';
}
$keys[]='cs';
// estimate quality
$keys[]='resolution_80_percent';
$keys[]='resolution_50_percent';
$keys[]='confidence_appion';
//$keys[]='confidence_30_10';
//$keys[]='confidence_5_peak';
$keys[]='ctffind4_resolution';
if ($ctftype=='ctffind') 
	$keys[]='cross_correlation';
else 
	$keys[]='confidence';
//$keys[]='confidence_d';
// add the Cs


$keymap = array(
	"defocus"  => "nomDef",
	"defocus1"  => "def1",
	"defocus2"  => "def2",
	"confidence"  => "conf&nbsp;(pkg)",
	"angle_astigmatism"  => "&theta;<sub>astig</sub>",
	"extra_phase_shift"  => "&phi;<sub>pp</sub>",
	"cross_correlation"  => "cc",
	"amplitude_contrast" => "amp&nbsp;con",
	"confidence_appion" => "conf&nbsp;(appion)",
	"confidence_30_10" => "conf&nbsp;(30/10)",
	"confidence_5_peak" => "conf&nbsp;(5 peak)",
	"resolution_80_percent" => "<br/>res&nbsp;(0.8)",
	"resolution_50_percent" => "res&nbsp;(0.5)",
	"ctffind4_resolution" => "res&nbsp;(pkg)",

);

if ($ctfdata) {
	echo "<font style='font-size: 12px;'>";
	if (is_array($ctfdata))
		foreach($keys as $k) {
			if (!array_key_exists($k,$ctfdata))
				continue;
			$v=$ctfdata[$k];
			if (array_key_exists($k, $keymap)) 
				$name = $keymap[$k];
			else
				$name = $k;
			if (preg_match('%defocus%',$k))
				echo " <b>$name:</b>&nbsp;",($leginondata->formatDefocus($v));
			elseif (preg_match('%phase_shift%',$k))
				echo " <b>$name:</b>&nbsp;".format_angle_degree($v*180/3.14159,2,2);
			elseif (preg_match('%ctffind4_res%',$k))
				echo " <b>$name:</b>&nbsp;".format_angstrom_number($v*1e-10,2,2);
			elseif ($v-floor($v)) 
				echo " <b>$name:</b>&nbsp;".format_sci_number($v,2,2);
			else
				echo " <b>$name:</b>&nbsp;$v";
		}
}
?>
</td>
</tr>
</table>
</font>
</body>
</html>
