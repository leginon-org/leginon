<?php
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";

$filename = ($_GET['file']) ? $_GET['file']: false;
$sessionId = ($_GET['expId']) ? $_GET['expId']: false;

//Block unauthorized user
checkExptAccessPrivilege($sessionId,'data');
preg_match("%(.*)config(.*)%", $filename, $reg_match_config);
preg_match("%(.*)dbemauth(.*)%", $filename, $reg_match_auth);

if (empty($reg_match_config) && empty($reg_match_auth)) {
	$sessioninfo = $leginondata->getSessionInfo($sessionId);
	preg_match("%(.*)".$sessioninfo['name']."(.*)%", $filename, $reg_match);

	if (file_exists($filename) && is_link($filename)) {
		$filename = readlink($filename);
	}

	if (file_exists($filename) && !empty($reg_match))  {
		$size=filesize($filename);
		header("Content-Type: application/octet-stream");
		header("Content-Type: application/force-download");
		header("Content-Type: application/download");
		header("Content-Transfer-Encoding: binary");
		header("Content-Length: $size");
		$basename=basename($filename);
		header("Content-Disposition: attachment; filename=$basename;");
		readfile($filename);
	} else {
		echo "
		<script>
		alert('file: $filename \\n is not available');
		history.go(-1);
		</script>
		";
	}
}
?>
