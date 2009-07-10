<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"  "http://www.w3.org/TR/html4/strict.dtd">
<html>
	<head>
		<meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
		<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
		<style>
		ul {
			list-style-type: none;
			margin : 2px 2px 2px 2px;
			padding : 2px 2px 2px 2px;
			font-size: 14px;
		}
		li {
			padding-left : 15px;
		}
		</style>
	</head>
	<body>
<?php
require 'inc/leginon.inc';
$sessionId=$_GET['id'];
$qcounts = $leginondata->getQueueCountResults($sessionId);
if ($qcounts) {
	$display='estimated queue processing time
<div id="qcount" style="position:relative; width:250px; border: 1px #696969 solid" >';
	foreach ((array)$qcounts as $q) {
		$display	.= '<ul><li><b>'.$q[0].' </b></li>'
							.'<li>unprocessed queue= '.$q[1].'</li>'
							.'<li>avg time so far = '. (int)($q[2]) .' s</li>'
							.'<li>remaining time  = '. $q[3] .' min '.$q[4].' s</li>'
							.'</ul>';
	}
	echo $display;
	echo '<div>';
}
?>
	</body>
</html>
