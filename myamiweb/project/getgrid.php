<?php
require_once "inc/project.inc.php";
require_once "inc/gridbox.inc.php";
require_once "inc/grid.inc.php";
require_once "inc/mysql.inc";

$gridId = ($_GET['gridId']) ? $_GET['gridId'] : $_POST['gridId'];
if ($gridId) {
?>
<html>
<head>
<link rel="StyleSheet" type="text/css" href="css/project.css" />
</head>
<body>

<?php
$selectedgridId=$gridId;
$grid = new grid();
$gridinfo = $grid->getGridInfo($selectedgridId);
if (is_array($gridinfo)) {
	$gridId = $gridinfo['gridId'];

?>
<table border=0>
<tr valign="top">
<td>
<h3>Label</h3>
</td>
<td>
<h3>Preparation Date</h3>
</td>
</tr>
<tr valign="top">
<td>
<?php echo $gridinfo['label'] ?>
</td>
<td>
<?php echo $gridinfo['prepdate'] ?>
</td>
</tr>
<tr valign="top">
<td>
<h3>Substrate</h3>
</td>
<td>
<h3>Preparation</h3>
</td>
</tr>
<tr valign="top">
<td>
<?php echo $gridinfo['specimen'] ?>
</td>
<td>
<?php echo $gridinfo['preparation'] ?>
</td>
</tr>
<tr valign="top">
<td>
<h3>Number</h3>
</td>
<td>
<h3>Location</h3>
</td>
</tr>
<tr valign="top">
<td>
<?php echo $gridinfo['number'] ?>
</td>
<td>
<?php echo $gridinfo['location'] ?>
</td>
</tr>
<tr valign="top">
<td>
<h3>Note</h3>
</td>
<td>
<h3>Fraction</h3>
</td>
<td>
<h3>Concentration</h3>
</td>
</tr>
<tr valign="top">
<td>
<?php echo $gridinfo['note'] ?>
</td>
<td>
<?php echo $gridinfo['fraction'] ?>
</td>
<td>
<?php echo $gridinfo['concentration'] ?>
</td>
</tr>
<tr valign="top">
<td>
<?php
}
?>
</td>
</tr>
<tr>
<td colspan="3">
<?php
$gridboxdata = new gridbox();
$gridboxinfo = $gridboxdata->getGridBoxInfo($gridinfo['boxId']);
if ($gridinfo['boxId']) {
?><h3>Grid Box: <?php echo $gridboxinfo['gridboxlabel'] ?></h3><?php

switch ($gridboxinfo['boxtypeId']) {
	case '1':
		$link="type=cgb&";
		break;
	case '2':
		$link="type=gb&";
		break;
	case '3':
		$link="type=tgb&";
		break;
}
?>
<img alt="gridbox" src="drawgridbox.php?gbt=<?php echo $gridboxinfo['boxtypeId'] ?>&amp;<?php echo $link ?>size=tiny&amp;gl=<?php echo $gridinfo['boxId'] ?>&amp;gid=<?php echo $gridId ?>" border="0">
<?php } ?>

</td>
</tr>
</table>
</table>
</body>
</html>
<?php
}
?>
