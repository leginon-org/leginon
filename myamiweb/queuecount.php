<html><head><title>Queue Count</title>
<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require ("inc/leginon.inc");

function getQueueCountData($sessionId,$qtype,$status) {
	global $leginondata;
	$q="SELECT "
."count(`t`.`REF|AcquisitionImageData|image`) as QueueCount "
."FROM "
."`AcquisitionImageTargetData` AS `t` "
."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
."WHERE "
." q.`REF|SessionData|session` = ".$sessionId." "
."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
."AND t.`status` LIKE CONVERT(_utf8 '".$status."' USING latin1) COLLATE " ."latin1_swedish_ci "
."AND q.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE "
."latin1_swedish_ci "
				."";
return $leginondata->mysql->getSQLResult($q);
}

function getDeQueuedCountData($sessionId,$qtype) {
  global $leginondata;
  $q="SELECT "
."new.QueueCount as DeQueuedCount FROM (SELECT "
."t.`REF|ImageTargetListData|list` as list, "
."count(`t`.`REF|AcquisitionImageData|image`) as QueueCount "
."FROM "
."`AcquisitionImageTargetData` AS `t` "
."LEFT JOIN `DequeuedImageTargetListData` AS `itlist` ON " ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
."WHERE "
." q.`REF|SessionData|session` = ".$sessionId." "
."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "
."latin1_swedish_ci "
."AND t.`status` LIKE CONVERT(_utf8 'processing' USING latin1) COLLATE " ."latin1_swedish_ci "
."AND q.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE "
."latin1_swedish_ci AND `t`.`version`=0 group by t.`REF|ImageTargetListData|list`) new "
."";
return $leginondata->mysql->getSQLResult($q);
}

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

function getCount($itl) {
  global $leginondata;
      $q="SELECT "
."count(`t`.`REF|AcquisitionImageData|image`) as Count "
."FROM "
."`AcquisitionImageTargetData` AS `t` "
."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
."WHERE "
." `t`.`REF|ImageTargetListData|list`=".$itl." "
."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
."AND t.`status` LIKE CONVERT(_utf8 'new' USING latin1) COLLATE " ."latin1_swedish_ci "
."";
$countarray = $leginondata->mysql->getSQLResult($q);
return $countarray[0]['Count'];
}

function rsum($v, $w) {
  $v += $w;
  return $v;
}

function getCountsFromImageTargetLists($itls) {
	$counts = array();
	foreach ($itls as $itl) {
		$count = getCount($itl);
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
		."from "
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
		."`label` from QueueData where `REF|SessionData|session` = ".$sessionId."";
	return $leginondata->mysql->getSQLResult($q);
}

if (!$sessionId=$_GET[id])
	$sessionId="2147";
if (!$qtype=$_GET[q]) {
	$qtypes = getQueueTypes($sessionId);
} else {
	$qtypes=array();
	$qtype = array();
	$qtype['label'] = "Exposure Targeting";
	$qtypes[] = $qtype;
}

$sessioninfo = $leginondata->getSessionInfo($sessionId);
?>
<p>To use: queuecount.php?id=(sessionid)&q=Exposure Targeting</p>
<p><h2> Session <? echo $sessioninfo['Name'] ?> </h2> </p>
<?
foreach ($qtypes as $t) {
$qtype = $t['label'];
$sqldata1 = getQueueCountData($sessionId,$qtype,'new');
$sqldata1a = getQueueCountData($sessionId,$qtype,'done');
$sqldata1b = getQueueCountData($sessionId,$qtype,'aborted');
$sqldata1c = getDeQueuedCountData($sessionId,$qtype);
$sqldata2 = getQueueTimeData($sessionId,$qtype);
$sqldata0dq = getDeQueuedTargetListIds($sessionId,$qtype);
$sqldata0it = getTargetListIds($sessionId,$qtype);

$doneitls = array();
$allitls = array();
foreach ($sqldata0dq as $d1) {
	array_push($doneitls,$d1['doneid']);
};
foreach ($sqldata0it as $d1) {
	array_push($allitls,$d1['itlid']);
};

$activeitls = array_diff($allitls,$doneitls);
$totalActive = getCountsFromImageTargetLists($activeitls);


$totalNew = getCountsFromImageTargetLists($allitls);
$totalProced = getCountsFromImageTargetLists($doneitls);
$totalDone = 0;
$totalTime = 0;
$totalDeQueued = 0;


$i = -1;

foreach ($sqldata1b as $d1b) {
        $i = $i + 1;
        $totalProced = $totalProced + $d1b['QueueCount'];        
}
" ";

foreach ($sqldata1c as $d1c) {
        $i = $i + 1;
        $totalDeQueued = $totalDeQueued + $d1c['DeQueuedCount'];        
}
" ";

$j = -1;
foreach ($sqldata2 as $d2) {
        $j = $j + 1;
	$data2x[] = $d2['QueueCount']; // any timestamp
	$data2y[] = $d2['QueueTime']; // any value
        $totalDone = $totalDone + $data2x[$j];        
        $totalTime = $totalTime + $data2y[$j];
}
?>
<p> <h2> Queue Label: <? echo $qtype ?> </h2></p>
<? 
if ($totalDone > 0)
	$esttime=($totalActive)*$totalTime/$totalDone;
$estminute=(int)($esttime/60);
$estsecond=(int)($esttime-$estminute*60);

$totalqaborted = $totalNew-$totalDeQueued - ($totalProced-$totalDone)
?>
<p> total acquisition targets in queue= <? echo $totalNew ?> </p>
<p><h2> unprocessed queue= <? echo $totalActive  ?></h2></p>
<?if ($total2x==0)
   $total2x=1;
" ";
?>
<p> avg time so far = 
<? 
	if ($totalDone > 0) {
		echo  (int)($totalTime/$totalDone);
	} else {
		echo "unknown";
	}
?> s</p>
<p><h2>estimated time for the remaining targets  = <? echo $estminute ?> min <? echo $estsecond ?> s</h2></p>
</p>
<? } ?>
</body></html>
