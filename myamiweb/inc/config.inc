<?php
function addplugin($path) {
	addincludepath($path);
}

function addincludepath($path) {
	set_include_path(get_include_path() . PATH_SEPARATOR . $path);
}
?>
