<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
if ($leginondata->mysql->checkDBConnection())
	$leginondata->importTables($DEF_TABLES_FILE);

function admin_header($javascriptinit="") {
global $leginondata;


$link = new iconlink();
$link->align = 'center';
$link->cols = 1;
$link->onimg = "_on.png";
$link->offimg = "_off.png";
$link->setImagePath('img/');
$link->addlink('addgroup.php','Groups','', 'group1', '');
$link->addlink('adduser.php','Users','', 'user', '');
$link->addlink('addinstrument.php','Instruments','', 'tem_tecnai_icon', '');
$link->addlink('addcal.php','Calibrations','', 'calibration', '');
$link->addlink('addapp.php','Applications','', 'application', '');
$link->addlink('goniometer.php','Goniometer','', 'goniometer', '');


?>

<html>
<head>
<title>Leginon II Admin Tools</title>
<link rel="stylesheet" href="css/viewer.css" type="text/css" /> 
<script src="js/dataform.js"></script>
</head>
<body Background='img/background.jpg' leftmargin="0" topmargin="5" marginwidth="0" marginheight="5" alink="#00CCCC" vlink="#006699" link="#006699" <?php echo $javascriptinit; ?>>

<center><h1>Leginon II Admin Tools</h1></center>
<hr/>
<table border=0>
<tr valign="top">
<td width=100>
<?php $link->Display(); ?>
</td>
<td>
<?php
}

function admin_footer() {
	echo "
 	 </td>
	</tr>
    </body>
</html>
";
}
?>
