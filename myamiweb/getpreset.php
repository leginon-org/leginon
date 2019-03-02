<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

?>
<?php
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";

// Do these first to set processing database for particle labeling
$imgId=$_GET['id'];
$preset=$_GET['preset'];
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
//----Define what to display in array $p
$p[]='gridId';
$p[]='mag';
$p[]='defocus';
$p[]='pixelsize';
$p[]='exposure time';
$p[]='dose';
$p[]='tilt';
$str_tilt="";
$viewfilename=$_GET['vf'];
$showtilt=$_GET['tl'];
$showexptime=$_GET['xt'];
if ($imgId) {
	echo "<font style='font-size: 12px;'>";
	$gridId	= $leginondata->getGridId($imgId);
	$projectdata = new project();
	if($projectdata->checkDBConnection()) {
		$gridinfo = $projectdata->getGridInfo($gridId);
		if ($gridId)
			echo '<a class="header" target="gridinfo" href="'.PROJECT_URL.'getgrid.php?gridId='
				.$gridId.'">grid#'.$gridinfo[number].' info&raquo;</a>';
	}
	list($filename) = $leginondata->getFilename($imgId);
	$presets = $leginondata->getPresets($imgId, $p);
	if (is_array($presets)) {
		$is_diffraction = $imageinfo['is_diffraction'];
		foreach($presets as $k=>$v)

			if ($k=='defocus')
				echo " <b>$k:</b> ",($leginondata->formatDefocus($v));
			else if ($k=='pixelsize') {
				$v *= $imageinfo['binning'];
				echo " <b>$k:</b> ",($leginondata->formatPixelsize($v,$is_diffraction));
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
			else if ($k=='exposure time') {
				if( empty($v) && !empty($imageinfo['exposure time']))
  				$v = $imageinfo['exposure time'];
				if(!empty($v) && $showexptime)
					echo " <b>$k:</b> ",($leginondata->formatExposuretime($v));
			}
			else
				echo " <b>$k:</b> $v";
	}
	if ($str_tilt) {
		echo $str_tilt;
		echo "&nbsp;<img src='imgangle.php?a=".$angle."'>";
	}
	//Phase Plate
	if ($imageinfo['pp_usageId']) {
		$ppinfo = $leginondata->getPhasePlateInfo($imageinfo['pp_usageId']);
		$str_pp = " <b> pp:</b> ".$ppinfo['phase plate number'].'-'.$ppinfo['patch position'];
		echo $str_pp;
	}
	// Next Line
	// Filename
	echo " <font size='-2'>";
	if ($viewfilename)
		echo " <br/>".$filename['filename'];

	// --- Display Particle Labels --- //
	$sessionId = $imageinfo['sessionId'];

	$nptclsel = ($_GET['psel']) ? $_GET['psel'] : 0;
	$displaynptcl = ($_GET['nptcl']) ? true : false;
	$ptclparams= ($displaynptcl) ? trim($_GET['nptcl']) : false;
	if ($ptclparams) { 
			require_once "inc/image.inc";
			require_once "inc/particledata.inc";

			$colors = particleLabelsColors();
			$particle = new particledata();
			$particlerun=$particle->getLastParticleRun($sessionId);
			if ($nptclsel) {
				$particleruns=$particle->getParticleRunIds($sessionId);
				foreach ($particleruns as $prun) {
					$particlerun=$prun['DEF_id'];
					if($nptclsel==$particlerun)
						break;
				}
			}

			$particlelabels =$particle->getParticleLabels($particlerun);

			$formatlabels = array();
			foreach ((array)$particlelabels as $index=>$particlelabel) {
				$color = $colors[$index];
				$label = $particlelabel['label'];
				$formatlabels[] = '<span style="color:#'.$color.'">'.$label.'</span>';
			}
		echo "<br /><b>particle labels:</b> ".join(', ', $formatlabels);

	} else {
		$format_timestamp = '<span style="color:20B2AA">'.$imageinfo['timestamp'].'</span>';
		$zlp_thickness = $leginondata->getZeroLossIceThicknessfromImage($sessionId,$imgId);
		$obj_thickness = $leginondata->getObjIceThicknessfromImage($sessionId,$imgId);
  		$obj_thickness = $obj_thickness[0];
  		$zlp_thickness = $zlp_thickness[0];
		echo "<br />".$format_timestamp;
		if ( !empty($zlp_thickness['thickness'])) {
			echo "&nbsp &nbsp <b>ZLP Thickness:</b> ",intval($zlp_thickness['thickness']), " nm";
		}
		if ( !empty($obj_thickness['thickness'])) {
			echo "&nbsp &nbsp <b>ALS Thickness:</b> ",intval($obj_thickness['thickness']), " nm";
		}
	}
	echo "</font>";
}
?>
</td>
</tr>
</table>
</font>
</body>
</html>
