<html>
<head>
<title>Queue Count</title>
<link rel="stylesheet" href="css/viewer.css" type="text/css" /> 
</head>

<body>
<form name="queuecount" method="POST" action="queuecount.php">
<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 */

require_once ("inc/leginon.inc");

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

function printResult($qresult,$qtype='',$ttype='', $is_queue=true) {
	if ($qresult[2] == 0) return;
	$pretext = $qresult[0];
	$totalNew = $qresult[1];
	$totalActive = $qresult[2];
	$avgtime = $qresult[3];
	$esttime = $qresult[4];
	if ($avgtime && $totalActive && $esttime==0) $esttime = $totalActive * $avgtime;
		
	$estday = (int) floor($esttime / 86400);
	$esthour = (int) floor(($esttime%86400) / 3600);
	$estminute = (int) floor(($esttime%3600) / 60);
	$estsecond = (int) floor($esttime%60);
	$queuetext = ($is_queue) ? 'queue': 'targetlist';
?>
	<td>
		<p> <h3> <?php echo $qtype ?> </h3></p>
		<p> total <?php echo $ttype ?> targets in <?php echo $queuetext.' '.$pretext.$totalNew ?> </p>
		<p> <h4> unprocessed = <?php echo $totalActive  ?></h4></p>
		<p> avg time so far = <?php echo (int)($avgtime) ?> s</p>
		<p> <h4> estimated time for the remaining targets  = 
	<?php
	if ($estday > 0)
		echo "$estday days, $esthour hours\n";
	elseif ($esthour > 0)
		echo "$esthour hours, $estminute minutes\n";
	else
		echo "$estminute minutes, $estsecond seconds\n";
	?> <h4></p>
	</td>
	</tr><tr>
<?php return;
	}
// --- Set sessionId
$selected_sessionId = ($_GET['expId']);

if (!$selected_sessionId) {
	$lastId = $leginondata->getLastSessionId();
	$defaultsession= ($_GET['expId']) ? $_GET['expId']: $lastId;
	$sessionId = ($_POST['sessionId']) ? $_POST['sessionId'] : $defaultsession;

	if(!$sessions)
		$sessions = $leginondata->getSessions('description', $projectId);
	$sessionSelector = getSessionSelector($sessions, $sessionId);
} else {
	$sessionId = $selected_sessionId;
}
?>
	<table>
	<tr><td> <?php if (!$selected_sessionId) echo 'Session '.$sessionSelector; ?></td>
	</tr>
	<tr>
<?php
// --- Get nodes with queue
$qtypes = $leginondata->getQueueTypes($sessionId);
if (!$qtypes) {
	?><td><h4>No queuing in this session</h4></td><?php
} else {
	arsort($qtypes);
	// Change details to true to see acquisition and focus separately for debuging
	$details = false;
	if (!$details)
		$qcountsall = $leginondata->getQueueCountResults($sessionId);
	foreach ((array)$qtypes as $t) {
		$qtype = $t['label'];
		if ($details) {
			$qcountbytype = $leginondata->getQueueCountResultByQueueType($sessionId,$qtype);
			if ($qcountbytype === false) continue;
			foreach ($qcountbytype as $ttype=>$qresult) printResult($qresult,$qtype,$ttype);
		} else {
			printResult($qcountsall[$qtype],$qtype);
		}

	} 
}

	$countbytype = $leginondata->getNonQueueCountResults($sessionId);
	if ($countbytype !== false)
		printResult($countbytype['acquisition'],'Non Queue Targets',false);
?>
</tr></table>
</form> </body></html>
