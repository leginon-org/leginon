<?php
function addplugin($path) {
	addincludepath($path);
	define(strtoupper($path)."_BASE_URL", BASE_URL.$path."/");
}

function addincludepath($path) {
	set_include_path(get_include_path() . PATH_SEPARATOR . $path);
}
?>
