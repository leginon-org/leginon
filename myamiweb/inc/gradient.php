<?php
$graddir=$_SERVER['DOCUMENT_ROOT']."/".BASE_URL."/gradient/";
define('GRADIENT_DIR', $graddir);

function getGradient($name) {
	$gradfile=GRADIENT_DIR.$name.".txt";
	if ($dgradient=@file($gradfile)) {
		$gradient=array_map('getcolor', $dgradient);
		return $gradient;
	}
	return false;
}


function getcolor($hex) {
  $hex=trim($hex);
  return hexdec($hex);
}
?>
