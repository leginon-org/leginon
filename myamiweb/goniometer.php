<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
$applications = $leginondata->getApplications();
?>
<html>
<head>
<title>Leginon2 Application Import/Export</title>
<link rel="stylesheet" type="text/css" href="css/leginon.css"> 
</head>
<body>
<?
$label = ($_GET[label]) ? $_GET[label] : "03sep23x";
$axis = ($_GET[axis]) ? $_GET[axis] : "x";
$goniometerId = $leginondata->getGoniometerModelId($label, $axis);
?>
<img src="goniometergraph.php?Id=<? echo $goniometerId; ?>">
</body>
</html>
