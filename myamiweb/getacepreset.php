<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/viewer.inc";
require_once "inc/leginon.inc";
if (!defined('PROCESSING')) exit;
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

// Set the order of the displayed information
$keys[]='resolution_50_percent';
$keys[]='ctffind4_resolution';

// estimate parameters
$keys[]='defocus';
$keys[]='defocus1';
// assume defocus1 and defocus2 are equal if equal at Angstrom level
$epsilon = 1e-10;
if (abs($ctfdata['defocus1'] - $ctfdata['defocus2']) > $epsilon) {
	$keys[]='defocus2';
	$keys[]='angle_astigmatism';
}
if (abs($ctfdata['extra_phase_shift']) > 0.001) {
	$keys[]='extra_phase_shift';
}
$keys[]='runname';
$keys[]='resolution_80_percent';
$keys[]='confidence_appion';
//$keys[]='confidence_30_10';
//$keys[]='confidence_5_peak';

if ($ctftype=='ctffind') 
	$keys[]='cross_correlation';
else 
	$keys[]='confidence';
$keys[]='cs';
$keys[]='amplitude_contrast';

//$keys[]='confidence_d';
// add the Cs


$keymap = array(
	"defocus"  => "nomDef",
	"defocus1"  => "def1",
	"defocus2"  => "def2",
	"runname"  => "runname",
	"confidence"  => "conf<sub>pkg</sub>",
	"angle_astigmatism"  => "&theta;<sub>astig</sub>",
	"extra_phase_shift"  => "&phi;<sub>pp</sub>",
	"cross_correlation"  => "cc",
	"amplitude_contrast" => "amp&nbsp;con",
	"confidence_appion" => "conf<sub>appion</sub>",
	"confidence_30_10" => "conf<sub>30/10</sub>",
	"confidence_5_peak" => "conf<sub>5 peak</sub>",
	"resolution_80_percent" => "res<sub>0.8</sub>",
	"resolution_50_percent" => "res<sub>0.5</sub>",
	"ctffind4_resolution" => "res<sub>pkg</sub>",
);

if ($ctfdata) {
	echo "<font style='font-size: 11px; font-family: monospace;'>";
	if (is_array($ctfdata))
		foreach($keys as $k) {
			// skip unknown values
			if (!array_key_exists($k, $ctfdata))
				continue;
			// get the value
			$v=$ctfdata[$k];
			// use keymap for better formatting
			if (array_key_exists($k, $keymap)) 
				$name = $keymap[$k];
			else
				$name = $k;
			// special numerical formatting
			if (preg_match('%defocus%',$k))
				echo " <b>$name:</b>&nbsp;",($leginondata->formatDefocus($v));
			elseif ($k == 'angle_astigmatism')
				echo " <b>$name:</b>&nbsp;".format_angle_degree($v,2,2);
			elseif ($k == 'extra_phase_shift')
				echo " <b>$name:</b>&nbsp;".format_angle_degree($v*180/3.14159,2,2);
			elseif (preg_match('%resolution%',$k))
				echo " <b>$name:</b>&nbsp;".format_angstrom_number($v*1e-10,2,2);
			elseif (preg_match('confidence%',$k) || $k == "amplitude_contrast")
				echo " <b>$name:</b>&nbsp;".number_format($v,2);
			elseif ($k == 'cs')
				echo " <b>$name:</b>&nbsp;".number_format($v,3)."&nbsp;mm";
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
