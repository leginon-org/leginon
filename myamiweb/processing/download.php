<?php

require 'inc/leginon.inc';
$filename = ($_GET['file']) ? $_GET['file']: false;

if (file_exists($filename))  {
	$size=filesize($filename);
	header("Content-Type: application/octet-stream");
	header("Content-Type: application/force-download");
	header("Content-Type: application/download");
	header("Content-Length: $size");
	header("Content-Disposition: attachment; filename=".$filename);
	readfile($filename);
} else {
	echo "
	<script>
	alert('file: $filename \\n is not available');
	history.go(-1);
	</script>
	";
}
?>
