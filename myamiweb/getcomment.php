<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once 'inc/leginon.inc';

$id=$_GET['id'];
$preset=$_GET['preset'];

// --- find image
$newimage = $leginondata->findImage($id, $preset);
$imageId = $newimage['id'];
?>
<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="5" marginheight="0" >
<font face="Arial, Helvetica, sans-serif" size="2">
<table width=100% cellpadding="2" cellspacing="0" style="position:relative; border: 1px #696969 solid">
<tr valign="top">
<td >
<?php

if ($id) {
	echo "<font style='font-size: 10px;'>";
	$imagecomment = $leginondata->getImageComment($imageId);
	echo $imagecomment."</font>";
}

?>
</td>
</tr>
</table>
</font>
</body>
</html>
