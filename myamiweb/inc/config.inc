<?php
function addplugin($path, $name='') {
	if (empty($name)) {
		$name=strtoupper($path);
	}
	define($name."_BASE_URL", BASE_URL.$path."/");
	$path=$_SERVER['DOCUMENT_ROOT'] . '/' . BASE_URL . $path;
	addincludepath($path);
}

function addincludepath($path) {
	set_include_path(get_include_path() . PATH_SEPARATOR . $path);
}
?>
