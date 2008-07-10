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
 */

require ("inc/leginon.inc");

function getDeQueuedTargetListIds($sessionId,$qtype) {
	global $leginondata;
	$q="SELECT "
		."dqlist.`REF|ImageTargetListData|list` as doneid "
		."FROM "
		."`DequeuedImageTargetListData` AS `dqlist` "
		."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`dqlist`.`REF|QueueData|queue`) "
		."where "
		."`q`.`REF|SessionData|session`=".$sessionId." "
		."AND "
		."`q`.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE latin1_swedish_ci "
		."";
	return $leginondata->mysql->getSQLResult($q);
}

function getTargetListIds($sessionId,$qtype) {
	global $leginondata;
	$q="SELECT "
		."itlist.`DEF_id` as itlid "
		."FROM "
		."`ImageTargetListData` AS `itlist` "
		."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
		."where "
		."`q`.`REF|SessionData|session`=".$sessionId." "
		."AND "
		."`q`.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE latin1_swedish_ci "
		."";
	return $leginondata->mysql->getSQLResult($q);
}

function rsum($v, $w) {
	$v += $w;
	return $v;
}

function getCountFromTargetListId($targetlistId,$status) {
	global $leginondata;
	$q="SELECT "
		."count(`t`.`DEF_id`) as Count "
		."FROM "
		."`AcquisitionImageTargetData` AS `t` "
		."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
		."WHERE "
		." t.`REF|ImageTargetListData|list` = ".$targetlistId." "
		."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
		."AND t.`status` LIKE CONVERT(_utf8 '".$status."' USING latin1) COLLATE " ."latin1_swedish_ci "
		."";
	$result = $leginondata->mysql->getSQLResult($q);
	if ($result) {
		return $result[0]['Count'];
	} else {
		return;	
	}
}

function getCountsFromImageTargetLists($itls) {
	$counts = array();
	foreach ($itls as $itl) {
		$count = getCountFromTargetListId($itl,'new');
		array_push($counts, $count);
	};
	$result = array_reduce($counts,"rsum");
	if (!$result) $result=0;
	return $result;
}

function getQueueTimeData($sessionId,$qtype) {
  global $leginondata;
  $q="SELECT "
		."proc.QueueOn as queue,"
		."done.QueueCount as QueueCount, "
		."(done.time-proc.time) as QueueTime "
		."FROM "
		."(SELECT "
		."min(UNIX_timestamp(`t`.`DEF_timestamp`)) as time, "
		."`t`.`REF|AcquisitionImageData|image` as QueueOn, "
		."count(`t`.`REF|AcquisitionImageData|image`) as QueueCount "
		."FROM "
		."`AcquisitionImageTargetData` AS `t` "
		."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
		."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
		."WHERE "
		." q.`REF|SessionData|session` = ".$sessionId." "
		."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
		."AND t.`status` LIKE CONVERT(_utf8 'processing' USING latin1) COLLATE " ."latin1_swedish_ci "
		."AND q.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE "
		."latin1_swedish_ci "
		."group by t.`REF|AcquisitionImageData|image`) AS proc, "
		."(SELECT "
		."max(UNIX_timestamp(`t`.`DEF_timestamp`)) as time, "
		."`t`.`REF|AcquisitionImageData|image` as QueueOn, "
		."count(`t`.`REF|AcquisitionImageData|image`) as QueueCount "
		."FROM "
		."`AcquisitionImageTargetData` AS `t` "
		."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
		."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
		."WHERE "
		." q.`REF|SessionData|session` = ".$sessionId." "
		."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
		."AND t.`status` LIKE CONVERT(_utf8 'done' USING latin1) COLLATE "."latin1_swedish_ci "
		."AND q.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE "
		."latin1_swedish_ci "
		."group by t.`REF|AcquisitionImageData|image`) AS done "
		."WHERE "
		."proc.QueueOn=done.QueueOn "
		."";
	return $leginondata->mysql->getSQLResult($q);
}

function getQueueTypes($sessionId) {
	global $leginondata;
	$q="SELECT "
		."`label` FROM QueueData where `REF|SessionData|session` = ".$sessionId."";
	return $leginondata->mysql->getSQLResult($q);
}

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
$qtypes = getQueueTypes($sessionId);
if (!$qtypes) {
	?><td><h4>No queuing in this session</h4></td><?
} else {
	arsort($qtypes);
	foreach ($qtypes as $t) {
		$qtype = $t['label'];
		$sqldataTime = getQueueTimeData($sessionId,$qtype);
		$sqldataDqList = getDeQueuedTargetListIds($sessionId,$qtype);
		$sqldataTList = getTargetListIds($sessionId,$qtype);


		$doneitls = array();
		$allitls = array();
		foreach ($sqldataDqList as $d) {
			array_push($doneitls,$d['doneid']);
		};
		foreach ($sqldataTList as $d) {
			array_push($allitls,$d['itlid']);
		};

		$activeitls = array_diff($allitls,$doneitls);
		$totalActive = getCountsFromImageTargetLists($activeitls);
		$totalNew = getCountsFromImageTargetLists($allitls);
		$totalDone = 0;
		$totalTime = 0;
		$totalDoneInActive = 0;
		// Some targets in the active target list may have been processed
		foreach ($activeitls as $d) {
			$totalDoneInActive += getCountFromTargetListId($d,'done');
			$totalDoneInActive += getCountFromTargetListId($d,'aborted');
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
		$estminute= (int)($esttime / 60);
		$estsecond= (int)($esttime - $estminute * 60);

	?>
	<td>
	<p> <h3> <? echo $qtype ?> </h3></p>
	<p> total acquisition targets in queue= <? echo $totalNew ?> </p>
	<p> <h4> unprocessed queue= <? echo $totalActive  ?></h4></p>
	<p> avg time so far = <? echo (int)($avgtime) ?> s</p>
	<p> <h4> estimated time for the remaining targets  = <? echo $estminute ?> min <? echo $estsecond ?> s <h4></p>
	</td>
	</tr><tr>
<?
	} 
}
?>
</tr></table>
</form> </body></html>
