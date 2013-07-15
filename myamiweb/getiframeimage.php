<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/leginon.inc";
?>
<html>
<head>
</head>
<?php
$template = $_GET['tmpl'];
$preset = $_GET['preset'];
$session = $_GET['session'];
$id= $_GET['id'];
$size=$_GET['s'];
$quality=$_GET['t'];
$minpix=$_GET['np'];
$maxpix=$_GET['xp'];
$src = ($template) ?
	"$template?preset=$preset&session=$session&id=$id&t=$quality&s=$size&np=$minpix&xp=$maxpix&sb=1" :
	"img/empty.gif"	
;
?>

<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" >
<img id=imgmv name=newimgmv src="<?php echo $src; ?>">
</body>
</html>

