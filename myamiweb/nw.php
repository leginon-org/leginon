<?
require('inc/leginon.inc');
$id=$_GET[id];
$filename = $leginondata->getFilename($id);
$imgsrc = "getparentimg.php?preset=".$_GET[preset]."&session=".$_GET[session]."&id=".$id."&t=png&s=&tg=1";
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
