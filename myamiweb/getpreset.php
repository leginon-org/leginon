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
$p[]='mag';
$p[]='defocus';
$p[]='pixelsize';
$id=$_GET['id'];
$preset=$_GET['preset'];
$viewfilename=$_GET['vf'];
if ($id) {
	$parent = $leginondata->getParent($id, $preset);
	$id = $parent[parentId];
	$filename = $leginondata->getFilename($id);
	$presets = $leginondata->getPresets($id, $p);
	if (is_array($presets))
	foreach($presets as $k=>$v)
		if ($k=='defocus')
			printf(" <b>$k:</b> %1.4f &micro;m",($v/1e-6));
		else if ($k=='pixelsize')
			printf(" <b>$k:</b> %1.4f nm",($v/1e-9));
		else
			echo " <b>$k:</b> $v";
	if ($viewfilename)
		echo " <br>$filename";

}
?>
</font>
</body>
</html>

