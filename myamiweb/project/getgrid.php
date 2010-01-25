<?php
require "inc/project.inc.php";
require "inc/gridbox.inc.php";
require "inc/grid.inc.php";
require "inc/mysql.inc";

$gridId = ($_GET['gridId']) ? $_GET['gridId'] : $_POST['gridId'];
if ($gridId) {
?>
<html>
<head>
<link rel="StyleSheet" type="text/css" href="css/project.css" />
</head>
<body>

<?
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
<?=$gridinfo['label']?>
</td>
<td>
<?=$gridinfo['prepdate']?>
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
<?=$gridinfo['specimen']?>
</td>
<td>
<?=$gridinfo['preparation']?>
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
<?=$gridinfo['number']?>
</td>
<td>
<?=$gridinfo['location']?>
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
<?=$gridinfo['note']?>
</td>
<td>
<?=$gridinfo['fraction']?>
</td>
<td>
<?=$gridinfo['concentration']?>
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
<?
$gridboxdata = new gridbox();
$gridboxinfo = $gridboxdata->getGridBoxInfo($gridinfo['boxId']);
if ($gridinfo['boxId']) {
?><h3>Grid Box: <?=$gridboxinfo['gridboxlabel']?></h3><?

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
<img alt="gridbox" src="drawgridbox.php?gbt=<?=$gridboxinfo['boxtypeId']?>&amp;<?=$link?>size=tiny&amp;gl=<?=$gridinfo['boxId']?>&amp;gid=<?=$gridId?>" border="0">
<? } ?>

</td>
</tr>
</table>
</table>
</body>
</html>
<?
}
?>
