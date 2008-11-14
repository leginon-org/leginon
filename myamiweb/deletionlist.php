<?php
require_once 'inc/leginon.inc';
?>
<html>
<head>
<title>Image Deletion List</title>
<link rel="stylesheet" href="../css/viewer.css" type="text/css" /> 
</head>
	<body>
	<div class="header">
	<form name="deletionlist" method="POST" action="deletionlist.php">
		<table>
			<tr><td>
	<?echo divtitle("Files marked for deletion but still exist");?>
			<table class='tableborder' border='1' cellspacing='1' cellpadding='5' width=100%>
				<tr><td>
<?php
$filecount = 0;
$filearray = $leginondata->getDeletionList(1);
foreach ($filearray as $file) {
	echo $file['filepath'];
	$filecount += 1;
	?><br><?
}
if ($filecount == 0) 
	echo 'NONE';
?>
			</td></tr>
		</table>
		<br>
		</td></tr><tr><td>
	<?echo divtitle("Files marked for deletion that are removed");?>
<table class='tableborder' border='1' cellspacing='1' cellpadding='5' width=100%>
<tr><td>
<?php
$filearray = $leginondata->getDeletionList(0);
$filecount = 0;
$status = 'Mark as Deleted';
foreach ($filearray as $file) {
	if ($_POST['markasdeleted']=='Mark as Deleted') {
		$imageId = $file['imageId'];
		$sessionId = $file['sessionId'];
		$leginondata-> setImageDeletionStatus($imageId,$sessionId, 'deleted');
		$status = '';
	} else {
		echo $file['filepath'];
		$status = 'Mark as Deleted';
		$filecount += 1;
		?>
		<br>
		<?
	}
}
if ($filecount > 0) {
?>
</td></tr>
<tr><td>
	<input type="submit" name="markasdeleted" value = "<?echo $status?>" >
<?
} else {
echo 'NONE';
}
?>
</td></tr>
</table>
</td></tr></table>
</form>
</body>

</html>

