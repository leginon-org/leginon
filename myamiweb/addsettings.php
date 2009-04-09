<?
require('inc/admin.inc');

admin_header('onload="init()"');
if ($_POST) {
	require "inc/setdefault.php";
}
?>
<script>


function init() {
}
</script>
<h3>Load Default Settings</h3>
<div align="center">
<?php
if ($_POST) {
	echo "default settings loaded";
} else {
?>
<form method="POST" action="<?php $_SERVER['PHP_SELF']?>" >
	<input type="submit" name="def" value="Load" >
</form>
<? } ?>
</div>
<?
admin_footer();
?>
