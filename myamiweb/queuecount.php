<html>
<head>
<title>Queue Count</title>
<link rel="stylesheet" href="css/viewer.css" type="text/css" /> 
</head>

<body onLoad="init()">
<form name="queuecount" method="POST" action="queuecount.php">
<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

require ("inc/leginon.inc");

function getSessionSelector($sessions, $sessionId=NULL) {
	$selector = '<select name="sessionId" onchange=submit()>';
	foreach ($sessions as $session) {
		$selector .= '<option class="fixed" value='.$session['id'];
		if ($session['id'] == $sessionId)
			$selector .= ' selected ';
			$fullname = $session['name'];
			$length = 100;
			if (strlen($fullname) <= $length) {
				$shortname = $fullname;
			} else {
				$shortname = substr($fullname,0,$length)."....";
			}
			$selector .= '>'.$shortname.'</option>';
		}
		$selector .= '</select>';
		return $selector;
}

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = ($_POST['sessionId']) ? $_POST['sessionId'] : $lastId;

if(!$sessions)
	$sessions = $leginondata->getSessions('description', $projectId);
$sessionSelector = getSessionSelector($sessions, $sessionId);

?>
	<table>
	<tr><td>Session <?php echo $sessionSelector; ?></td>
	</tr>
	<tr>
<?
// --- Get nodes with queue
$qtypes = $leginondata->getQueueTypes($sessionId);
if (!$qtypes) {
	?><td><h4>No queuing in this session</h4></td><?
} else {
	arsort($qtypes);
	foreach ($qtypes as $t) {
		$qtype = $t['label'];
		$sqldataTime = $leginondata->getQueueTimeData($sessionId,$qtype);
		$sqldataDqList = $leginondata->getDeQueuedTargetListIds($sessionId,$qtype);
		$sqldataTList = $leginondata->getTargetListIds($sessionId,$qtype);


		$doneitls = array();
		$allitls = array();
		foreach ($sqldataDqList as $d) {
			array_push($doneitls,$d['doneid']);
		};
		foreach ($sqldataTList as $d) {
			array_push($allitls,$d['itlid']);
		};

		$activeitls = array_diff($allitls,$doneitls);
		$totalActive = $leginondata->getCountsFromImageTargetLists($activeitls);
		$totalNew = $leginondata->getCountsFromImageTargetLists($allitls);
		$totalDone = 0;
		$totalTime = 0;
		$totalDoneInActive = 0;
		// Some targets in the active target list may have been processed
		foreach ($activeitls as $d) {
			$totalDoneInActive += $leginondata->getCountFromTargetListId($d,'done');
			$totalDoneInActive += $leginondata->getCountFromTargetListId($d,'aborted');
		}
		$totalActive -= $totalDoneInActive;

		// Total Done include only  non-aborted done targets
		foreach ($sqldataTime as $d) {
			$totalDone = $totalDone + $d['QueueCount'];
			$totalTime = $totalTime + $d['QueueTime'];
		}
		if ($totalDone > 0) {
			$avgtime = ($totalTime / $totalDone);
			$esttime= ($totalActive) * $avgtime;
		} else {
			$avgtime = "unknown";
		}
		$estday = (int) floor($esttime / 86400);
		$esthour = (int) floor(($esttime%86400) / 3600);
		$estminute = (int) floor(($esttime%3600) / 60);
		$estsecond = (int) floor($esttime%60);

	?>
	<td>
	<p> <h3> <? echo $qtype ?> </h3></p>
	<p> total acquisition targets in queue= <? echo $totalNew ?> </p>
	<p> <h4> unprocessed queue= <? echo $totalActive  ?></h4></p>
	<p> avg time so far = <? echo (int)($avgtime) ?> s</p>
	<p> <h4> estimated time for the remaining targets  = 
	<? 
	if ($estday > 0)
		echo "$estday days, $esthour hours\n";
	elseif ($esthour > 0)
		echo "$esthour hours, $estminute minutes\n";
	else
		echo "$estminute minutes, $estsecond seconds\n";
	?> <h4></p>
	</td>
	</tr><tr>
<?
	} 
}
?>
</tr></table>
</form> </body></html>
