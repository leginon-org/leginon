<?php

function addplugin($path, $name='') {
	if (empty($name)) {
		$name=strtoupper($path);
	}
	define($name, true);
	define($name."_BASE_URL", BASE_URL.$path."/");
	$pluginPath = WEB_ROOT."/".$path;

	addincludepath($pluginPath);
}

function addincludepath($path) {
	set_include_path(get_include_path() . PATH_SEPARATOR . $path);
}

?>
