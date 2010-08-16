<html>
<head>
	<title>info</title>
	<link rel="StyleSheet" type="text/css" href="css/project.css" />
</head>
<script type="text/javascript">
function init() {
	this.focus()
}
</script>
<body onload="init()">
<?php

require "inc/project.inc.php";
require "inc/confirmlib.php";
require "inc/packagelib.php";
require "inc/samplelib.php";
require "inc/gridlib.php";
require "inc/utilpj.inc.php";
$grid = new Grid();
$confirm = new Confirm();
$package = new Package();
$sample = new Sample();

$gridId = ($_GET['gid']);
$confirmId = ($_GET['cid']);
$packageId = ($_GET['pkid']);
$sampleId = ($_GET['sid']);
$projectId = ($_GET['pid']);
$gridi = $grid->getGridInfo($gridId);
$samplei = $sample->getSampleInfo($sampleId);
$packagei = $package->getPackageInfo($packageId);
$confirmi = $confirm->getConfirmInfo($confirmId);
if ($gridId){
	$data=$gridi;
	$class=$grid;
}
if ($sampleId) {
	$data=$samplei;
	$class=$sample;
}
if ($packageId) {
	$data=$packagei;
	$class=$package;
}
if ($confirmId) {
	$data=$confirmi;
	$class=$confirm;
}

foreach ((array)$data as $k=>$v) {
	if ($k=="number") {
	if ($gridId) {
		$v=$class->format_number($v, $gridi['type']);
	} else {
		$v=$class->format_number($v);
	}
	}
	echo "<b>$k :</b> $v <br />\n";
}
?>
</body>
</html>
