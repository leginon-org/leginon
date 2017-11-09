<?php
require_once 'tomography.php';
require_once 'thumbnails.php';

login_header('Tomography');
?>
<html>

<head>
<title>Tomography</title>
<link rel="stylesheet" href="../css/viewer.css" type="text/css" /> 
</head>

<body onLoad="init()">
<form name="tomography" method="POST" action="index.php">

<?php
if ($_GET['tid']) {
	$tiltSeriesId = $_GET['tid'];
	$sessionInfo = $tomography->getTiltSeriesSession($tiltSeriesId);
	$sessionId = $sessionInfo['DEF_id'];
}

$sessionId = ($_POST['sessionId']) ? $_POST['sessionId'] : $sessionId;
$tiltSeriesId = ($_POST['tiltSeriesId']) ? $_POST['tiltSeriesId'] : $tiltSeriesId;
$alabel= ($_POST['alignlabel']) ? $_POST['alignlabel'] : '';

$showmodel = ($_POST['showmodel']== 'on') ? 'CHECKED' : '';
if ($_POST['action']=='Mark for Deletion') {
	$tomography->setTiltSeriesDeletionStatus($tiltSeriesId,'marked');
} else {
	if ($_POST['action']=='Remove from Deletion List') {
		$tomography->setTiltSeriesDeletionStatus($tiltSeriesId,'');
	}
}
$deletestatus = $tomography->getTiltSeriesDeletionStatus($tiltSeriesId);
$sessions = $tomography->getTiltSeriesSessions();

if ($sessionId == NULL) {
    $sessionId = $sessions[0]['id'];
}

$sessionSelector = $tomography->getSessionSelector($sessions, $sessionId);

$tiltSeries = $tomography->getTiltSeries($sessionId);

$tiltSeriesSelector_array = $tomography->getTiltSeriesSelector($tiltSeries, $tiltSeriesId);
$tiltSeriesSelector = $tiltSeriesSelector_array[0];
$tiltSeriesNumber = $tiltSeriesSelector_array[1];
$tiltSeriesData = $tomography->getTiltSeriesData($tiltSeriesId);
$first_filename = $tiltSeriesData[0]['filename'];
$tiltSeriesName = substr($first_filename,0,strrpos($first_filename,'_'));

$tiltSeriesDose = $tomography->getTiltSeriesDose($tiltSeriesData);

$width = 800;
$height = 300;
$images = array();
#$axes = array('x', 'y', 'z', 'n', 't', 'theta');
$axes = array('x', 'y', 'z', 'phi','optical axis', 'z0');
foreach ($axes as $axis) {
	$images[] = '<img src="graph.php?'
		."tiltSeriesId=$tiltSeriesId"
		."&axis=$axis"
		."&width=$width"
		."&height=$height"
		.'" '
		."width=$width height=$height>";
}

$images[] = '<img src="graphmean.php?'
	."tiltSeriesId=$tiltSeriesId"
	."&width=$width"
	."&height=$height"
	.'" '
	."width=$width height=$height>";

?>


<script language="text/javascript">
function submit() {
	document.tomography.submit();
}
function init() {
	if (l=document.tomography.tiltSeriesId)
		l.focus();
}
</script>

<div class="header">
<table>
	<tr><td>
		<a href="summary.php?sessionId=<?php echo $sessionId; ?>">Summary</a>
		</td><td width=200 align=right>
		<b>show model parameters:</b>
		<input type='checkbox' name='showmodel' <?php echo $showmodel; ?> onClick="submit()">
	</td></tr>
</table>
</div>

<div class="body">
<table>
	<tr><td colspan=2>Session <?php echo $sessionSelector; ?></td>
	</tr><tr>
		<td rowspan=10 valign=top>Tilt Series
			<br>
<?php
echo $tiltSeriesSelector.'<br>';
if($tiltSeriesId != NULL) {
	echo "<a href=stack.php?tiltSeriesId=$tiltSeriesId&tiltSeriesNumber=$tiltSeriesNumber&alignlabel=".$alabel.">Download MRC stack</a><br>";
	echo "align label: <INPUT TYPE='text' NAME='alignlabel' SIZE='4' VALUE='".$alabel."'>\n";
	echo '</td><td>';
	echo '<table><tr><td colspan=2>';
	thumbnails($tiltSeriesId, $tomography);
	echo '</td></tr><tr><td>';
	echo "$tiltSeriesName &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>tiltSeriesId =</b> $tiltSeriesId";
	echo ";<b> total Dose=</b> $tiltSeriesDose e/&Aring;^2";
	echo '</td><td>';
	if ($deletestatus == 'deleted') {
		echo "<b> --- Images in this series are deleted ---</b>";
	} else {
		$state = ($deletestatus== 'marked') ? 'Remove from Deletion List' : 'Mark for Deletion';
		?>
		<input type="submit" name="action" value="<?php echo $state; ?>">
		<?php
	} 
	echo '</td></tr></table>';
	echo '</td></tr>';
}
?>
	<tr><td><?php echo $images[0]; ?></td></tr>
	<tr><td><?php echo $images[1]; ?></td></tr>
	<tr><td><?php echo $images[2]; ?></td></tr>
<?php
if ($showmodel) {
?>
	<tr><td><?php echo $images[3]; ?></td></tr>
	<tr><td><?php echo $images[4]; ?></td></tr>
	<tr><td><?php echo $images[5]; ?></td></tr>
<?php } ?>
<!--- <tr><td><?php echo $images[6]; ?></td></tr> --->
<?php
if($tiltSeriesId != NULL) {
	echo '<tr><td>';
	echo $images[6];
	echo '</td></tr>';
}
?>
</table>
</div>

</form>

</body>

</html>

