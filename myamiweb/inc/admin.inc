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
$link->addlink('addsettings.php','Default Settings','', 'calibration', '');
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

function wizard_footer() {
}

function mysql2UnixTime($mysqltime) {
	$year = substr($mysqltime, 0,4);
	$month  = substr($mysqltime, 4,2);
	$day = substr($mysqltime, 6,2);
	$hour = substr($mysqltime, 8,2);
	$minute = substr($mysqltime, 10,2);
	$second = substr($mysqltime, 12,2);
	return mktime($hour, $minute, $second, $month, $day, $year);
}

function display($r, $display_fields=False) {
	echo "<table class='tableborder' border=1 cellspacing=0, cellpadding=5>";
	if (!is_array($r))
		return False;
	$data = $r;
	if ($display_fields) {
		if ($r[0]) {
			$fields = array_keys($r[0]);
			foreach ($fields as $field)
				$f[$field] = $field;
			$data = array_merge(array($f), $r);
		}
	}
	foreach ($data as $row) {
	echo "<tr>";
		foreach ($row as $k=>$value) {
			if (eregi('^DEF_id|^REF\|', $k)) 
				continue;
			else if (eregi('^DEF_timestamp$', $k)) {
				if (!$display_fields)
					$value = date('D, j M Y G:i:s ', mysql2UnixTime($value));
				$display_fields = False;
			}
			echo "	<td>$value</td>\n";
		}
	echo "</tr>";
	}
	echo "</table>";
}
?>
