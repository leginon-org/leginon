<?php

function addplugin($path, $name='') {
	if (empty($name)) {
		$name=strtoupper($path);
	}
	define($name."_BASE_URL", BASE_URL.$path."/");
	$base = $_SERVER['DOCUMENT_ROOT'] . '/' . BASE_URL;
	$path = $base . $path;
	addincludepath($path);
}

function addincludepath($path) {
	set_include_path(get_include_path() . PATH_SEPARATOR . $path);
}

?>
