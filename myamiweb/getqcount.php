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
require_once 'inc/leginon.inc';
$sessionId=$_GET['id'];
$targetlistIds = $leginondata->getTargetListIds($sessionId,'',$limit=500);
if (count($targetlistIds) == 500) {
	// To speed up loi, this queue creates a link to queucount.php instead when queue is large 
	$display = '
<div id="qcount" style="position:relative; width:250px; border: 1px #696969 solid" >';
	$display .= '<a class="header" target="queuecount" href="queuecount.php?expId='.$sessionId.'"> [link to estimated queue processing time] </a> ';
	$display .= '</div>';
	echo $display;
} else {
	$qcounts = $leginondata->getQueueCountResults($sessionId);
	if ($qcounts) {
		$display='estimated queue processing time
	<div id="qcount" style="position:relative; width:250px; border: 1px #696969 solid" >';
		foreach ((array)$qcounts as $qtype=>$q) {
			$esttime = $q[4];
			$estminute = (int) floor(($esttime / 60));
			$estsecond = (int) floor($esttime%60);
			$display	.= '<ul><li><b>'.$qtype.' </b>('.$q[1].' targets)</li>'
							.'<li>unprocessed queue = '.$q[2].'</li>'
							.'<li>avg time so far = '. (int)($q[3]) .' s</li>'
							.'<li>remaining time  = '. $estminute .' min '.$estsecond.' s</li>'
							.'</ul>';
		}
		$display .= '</div>';
		echo $display;
	}
}
?>
	</body>
</html>
