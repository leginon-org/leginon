<?php
require_once "inc/leginon.inc";

$sessionId = $_GET['sessionId'];
$preset = $_GET['pre'];
if ($preset && $sessionId)
	$filenames = $leginondata->getFilenames($sessionId, $preset);

$filename="filelist.txt";

header("Content-Type: application/octet-stream");
header("Content-Type: application/force-download");
header("Content-Type: application/download");
header("Content-Disposition: attachment; filename=".$filename);
array_map('d', $filenames);

function d($a) {
	echo $a['name']."\n";
}
?>
