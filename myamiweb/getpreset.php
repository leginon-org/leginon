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
	if (in_array($preset, $leginondata->getTypeFFT())) {
		$fftimage  = $leginondata->getImageFFT($id);
		if (!$fftimage) {
			// --- try to find sibling if preset not a parent
			if ($preset=='focpow') {
				$preset='foc';
			} else {
				$imageinfo = $leginondata->getImageInfo($id);
				$preset = $imageinfo[preset];
			}
			$relation = $leginondata->getImageRelation($id, $preset,false);
			$fftimage  = $leginondata->getImageFFT($relation[siblingimageId]);
		}
		$filename = $fftimage[fftimage];
	} else {
	if (!$parent)
			// --- try to find sibling if preset not a parent
				$relation = $leginondata->getImageRelation($id, $preset);
				if (!$relation)
				// --- try to find sibling if from an other target
					$relation = $leginondata->getImageRelation($id, $preset, false);
				
			if ($relation) {
				$id = $relation[siblingimageId];
				$preset = $relation[siblingpreset];
				$parent = $leginondata->getParent($id, $preset);
			}
			$parent = $leginondata->getParent($id, $preset);
			$id = $parent[parentId];
			$info = $leginondata->getGridInfo($id);
			$filename = $leginondata->getFilename($id);
			$presets = $leginondata->getPresets($id, $p);
			if ($info[gridNb])
				echo "<b>grid#:</b> ".$info[gridNb];
			if (is_array($presets))
			foreach($presets as $k=>$v)
				if ($k=='defocus')
					printf(" <b>$k:</b> %1.4f &micro;m",($v/1e-6));
				else if ($k=='pixelsize')
					printf(" <b>$k:</b> %1.4f nm",($v/1e-9));
				else if ($k=='dose') {
					if (!empty($v))
						printf(" <b>$k:</b> %1.4f e¯/Å²",($v/1e20));
				}
				else
					echo " <b>$k:</b> $v";
	}
	if ($viewfilename)
		echo " <br>$filename";

}
?>
</font>
</body>
</html>

