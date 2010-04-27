<?php
require_once "inc/project.inc.php";
require_once "inc/util.inc";
require_once "inc/gridbox.inc.php";
require_once "inc/mysql.inc";
$gridbox = new gridbox();
$boxtypes = $gridbox->getBoxTypes();
// print_r($boxtypes);

$gridboxId = ($_GET['gridboxId']) ? $_GET['gridboxId'] : $_POST['gridboxId'];
if (empty($gridboxId) || !($gridbox->checkGridBoxExistsbyId($gridboxId))) {
	$title='- new gridbox';
	$action='add';
	$f_date=date("j/n/Y");
} else {
	$curgridbox = $gridbox->getGridBoxInfo($gridboxId);
//	print_r($curgridbox);
	$label = $curgridbox[gridboxlabel];
	$boxtypeId = $curgridbox[boxtypeId];
	$container = $curgridbox[container];
	$title ='- update gridbox: '.$label;
	$action='update';
}

if ($_POST['submit']) {
	$label = $_POST['label'];
	$boxtypeId = $_POST['boxtypeId'];
	$container = $_POST['container'];
	if ($_POST['submit']=='add')
		$gridboxId = $gridbox->addGridBox($label, $boxtypeId, $container);
	else if ($_POST['submit']=='update')
		$gridbox->updateGridBox($gridboxId, $label, $boxtypeId, $container);
		
		header("location: gridtray.php");
} 
project_header("Projects $title");
?>

<a href="javascript:history.back()">&laquo; back</a>
<p>
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
<?php
include('inc/gridboxform.inc');
project_footer();
?>
