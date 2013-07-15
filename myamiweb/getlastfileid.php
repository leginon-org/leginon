<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require_once "inc/leginon.inc";
$lastfileid = false;
$session = ($_GET['session']) ? $_GET['session'] : $_POST['session'];
$lastfileid = $leginondata->getLastFilenameId($session);
$strfileid = ($lastfileid) ? "=$lastfileid" : "";
$refresh = ($_POST['refreshstate']) ? $_POST['refreshstate'] : "false";
$refreshtime = ($_POST['refreshtime']) ? $_POST['refreshtime'] : "10000";
?>
<html>
<head>
<script>
var jsfileid <?php echo $strfileid; ?>;
var jstime = <?php echo time(); ?>;
var refresh = <?php echo $refresh; ?>;
var refreshtime = "<?php echo $refreshtime; ?>";

function getfileid() {
	return jsfileid;
}

function start(refreshtime) {
	if (refreshtime)
		document.memo.refreshtime.value=refreshtime;
	setRefreshState(true);
}

function setRefreshState(state) {
	document.memo.refreshstate.value=state;
	document.memo.submit();
}

function stop() {
	setRefreshState(false);
}

function rl() {
	if (parent.window.name=="loi") 
		parent.reset(getfileid());
	if (refresh)
		setTimeout("document.memo.submit(); ",refreshtime);
}
</script>
</head>
<body onload="rl()">
<form name="memo" method="POST">
<input type="hidden" name="refreshstate" value="true">
<input type="hidden" name="refreshtime" value="<?php echo $refreshtime; ?>">
<input type="hidden" name="session" value="<?php echo $session; ?>">
</form>
</body>
</html>
