<?
require('inc/leginon.inc');
$id=$_GET[id];
$tg = ($_GET[tg]) ? '&tg=1' : '';
$sb = ($_GET[sb]) ? '&sb=1' : '';
$minpix = ($_GET[np]) ? '&np='.$_GET[np] : '';
$maxpix = ($_GET[xp]) ? '&xp='.$_GET[xp] : '';
$fft = ($_GET[fft]) ? '&fft='.$_GET[fft] : '';
$filter = ($_GET[flt]) ? '&flt='.$_GET[flt] : '';
$binning = ($_GET[binning]) ? '&binning='.$_GET[binning] : '';
$colormap = ($_GET[colormap]) ? '&colormap='.$_GET[colormap] : '';

$options = $tg.$sb.$minpix.$maxpix.$fft.$filter.$binning.$colormap;

$filename = $leginondata->getFilenameFromId($id);
$imgsrc = "getparentimgtarget.php?preset=".$_GET[preset]."&session=".$_GET[session]."&id=".$id."&t=png&s=0".$options;
?>
<html>
<head>
<title>
<? echo $filename; ?>
</title>
<script>
function init() {
	this.focus();
}
</script>
</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" onload="init();">
<img name="newimgmv" id="imgmvId" border="0" src="<?=$imgsrc?>" >
</body>
</html>
