<?php
require "inc/leginon.inc";
require "inc/image.inc";

$sessionId = $_GET['sessionId'];
$imageId = $_GET['imageId'];
$name = $_GET['name'];
$comment = $_GET['comment'];

$dbc = $leginondata->mysql;

if ($sessionId && $imageId && $name && $comment) {
	$q = 'insert into `viewer_comment` (`sessionId`, `imageId`, `type`, `name`, `comment`) values '
		.'('.$sessionId.', "'.$imageId.'", "rt", "'.$name.'", "'.$comment.'")';
	if ($dbc->SQLQuery($q, true))
		$text = "comment inserted succesfully";
	else
		$text = "comment NOT inserted ".$dbc->getError();
	$img = createAltMessage($text);
} else if (!$name) {
	$img = createAltMessage("Enter a 'Name'");
} else if (!$comment) {
	$img = createAltMessage("Enter a 'Comment'");
} 
if (!$_GET) {
	$img = imagecreate(1,1);
	imagecolorallocate($img, 255, 255, 255);
}
Header("Content-type: image/x-png");
imagepng($img);
imagedestroy($img);
?>
