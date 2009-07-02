<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";

$vd = ($_POST) ? $_POST : $_REQUEST;

if($ch0 = $vd['ch0'])
	$sel_channels['ch0'] = $ch0;
if($ch1 = $vd['ch1'])
	$sel_channels['ch1'] = $ch1;
if($ch2 = $vd['ch2'])
	$sel_channels['ch2'] = $ch2;
if($ch3 = $vd['ch3'])
	$sel_channels['ch3'] = $ch3;
if($ch4 = $vd['ch4'])
	$sel_channels['ch4'] = $ch4;
if($ch5 = $vd['ch5'])
	$sel_channels['ch5'] = $ch5;
if($ch6 = $vd['ch6'])
	$sel_channels['ch6'] = $ch6;
if($ch7 = $vd['ch7'])
	$sel_channels['ch7'] = $ch7;

if ($opt = $vd['opt']) {
	$sel_q[]="opt=1";
	$sel_opt="checked";
}

if (is_array($sel_channels)) {
	$chs = array_keys($sel_channels);
	foreach ($sel_channels as $k=>$v) {
		$sel_q[] = $k."=1";
	}
	$url_ch=implode('&', $sel_q);
}

$defaultId= 1445;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$maxtemp= (is_numeric($_POST['maxr'])) ? $_POST['maxr'] 
		: (is_numeric($_GET['maxr']) ? $_GET['maxr'] : false);
$mintemp= (is_numeric($_POST['minr'])) ? $_POST['minr'] 
		: (is_numeric($_GET['minr']) ? $_GET['minr'] : false);


if ($driftdata = $leginondata->getDriftDataFromSessionId($sessionId)) {
foreach ($driftdata as $drift) {
	$id = $drift['imageId'];
	$data[$id] = $drift;
}

foreach ($data as $drift) {
	$id = $drift['imageId'];
	$t  = $drift['time'];
}
}
// --- Set  experimentId
// $lastId = $leginondata->getLastSessionId();
// $sessionId = (empty($_GET[Id])) ? $lastId : $_GET[sessionId];
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$title = $sessioninfo[Name];

?>
<html>
<head>
<title><?php echo $title; ?> drift report</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border=0 cellpadding=10>
<tr>
 <td>
  <a class="header" HREF="index.php">&lt;index&gt;</a>
 </td>
 <td>
  <a class="header" HREF="3wviewer.php?sessionId=<?php echo $sessionId; ?>">&lt;view <?php echo $title; ?>&gt;</a>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?php echo divtitle("Temperature Report $title Experiment"); ?>
	</td>
</tr>
<?php
echo "<tr>";
echo "<td colspan='2'>";
?>
<form method="POST" action="<?php echo $_SERVER['REQUEST_URI']?>">
	max temperature:<input class="field" name="maxr" type="text" size="5" value="<?php echo $maxtemp; ?>">
	min temperature:<input class="field" name="minr" type="text" size="5" value="<?php echo $mintemp; ?>">
	<input type='checkbox' name='opt' <?php echo $sel_opt; ?> >filter
	
<input class="button" type="submit" value="update">
<br>
<?php

$TEMPERATURE_DB_HOST = 'cronus4';
$TEMPERATURE_DB_USER = 'usr_inst';
$TEMPERATURE_DB_PASS = '';
$TEMPERATURE_DB = 'instrumentation';

$db =  new mysql ($TEMPERATURE_DB_HOST, $TEMPERATURE_DB_USER, $TEMPERATURE_DB_PASS, $TEMPERATURE_DB);

$q = 'SELECT `name` , `description`, `color` '
        . ' FROM `channelinfo` '
        . ' ORDER BY name ASC '
        . ' LIMIT 8 ';
$channelinfo = $db->getSQLResult($q);
$displaychannels = array (0,1,2,4,5,7);
foreach ($channelinfo as $k=>$a) {
	$channel = $k; 
	if (!in_array($k, $displaychannels))
		continue;
	$labels[$channel] = (empty($a[description])) ? $channel : $a[description];
	$colors[$channel] = $a['color'];
	$sel = ($sel_channels[$a['name']]) ? 'checked' : '';
	echo "<input type='checkbox' name='".$a['name']."' ".$sel." >".$labels[$channel];
}
?>
</form>
<?php
$urlrate = ($maxtemp) ? "&maxr=$maxtemp" : "";
$urlrate .= ($mintemp) ? "&minr=$mintemp" : "";
echo "<a href='temperaturegraph.php?vd=1&Id=$sessionId&$url_ch'>[data]</a>";
echo "<a href='temperaturegraph.php?vs=1&Id=$sessionId&$url_ch'>[sql]</a><br>";
echo "<img src='temperaturegraph.php?Id=$sessionId$urlrate&$url_ch'>";
echo "<br>";
echo "<br>";
echo "<img src='temperaturegraph.php?hg=1&Id=$sessionId$urlrate&$url_ch'>";
echo "</td>\n";
?>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>
