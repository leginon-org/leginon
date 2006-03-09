<?php
require_once('tomography.php');
$sessionId = $_GET['sessionId'];
$tiltSeriesId = $_GET['tiltSeriesId'];
?>
<?php
$sessions = $tomography->getTiltSeriesSessions();

if ($sessionId == NULL) {
    $sessionId = $sessions[0]['id'];
}

$sessionSelector = $tomography->getSessionSelector($sessions, $sessionId);

$tiltSeries = $tomography->getTiltSeries($sessionId);

$tiltSeriesSelector = $tomography->getTiltSeriesSelector($tiltSeries, $tiltSeriesId);

$width = 800;
$height = 300;
$images = array();
#$axes = array('x', 'y', 'z', 'n', 't', 'theta');
$axes = array('x', 'y', 'z');
foreach ($axes as $axis) {
	$images[] = '<img src="graph.php?'
		."tiltSeriesId=$tiltSeriesId"
		."&axis=$axis"
		."&width=$width"
		."&height=$height"
		.'" '
		."width=$width height=$height>";
}
?>
<html>

<head>
<title>Tomography</title>
<link rel="stylesheet" href="../css/viewer.css" type="text/css" /> 
</head>

<body onLoad="init()">

<form name="tomography" method="GET" action="index.php">

<script language="JavaScript">
function submit() {
	document.tomography.submit();
}
function init() {
	if (l=document.tomography.tiltSeriesId)
		l.focus();
}
</script>

<div class="header">
Tomography Prediction Plot
</div>

<div class="body">
<table>
<tr><td colspan=2>Session <?php echo $sessionSelector; ?></td></tr>
<tr>
<td rowspan=6 valign=top>Tilt Series<br>
<?php
echo $tiltSeriesSelector.'<br>';
if($tiltSeriesId != NULL) {
    echo "<a href=stack.php?tiltSeriesId=$tiltSeriesId>Download MRC stack</a><br>";
}
?>
</td>
<td><?php echo $images[0]; ?></td>
</tr>
<tr><td><?php echo $images[1]; ?></td></tr>
<tr><td><?php echo $images[2]; ?></td></tr>
<tr><td><?php echo $images[3]; ?></td></tr>
<tr><td><?php echo $images[4]; ?></td></tr>
<tr><td><?php echo $images[5]; ?></td></tr>
</table>
</div>

</form>

</body>

</html>

