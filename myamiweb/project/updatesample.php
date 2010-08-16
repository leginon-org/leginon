<?php

require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/samplelib.php";
require "inc/packagelib.php";
require "inc/utilpj.inc.php";

$sampleId = ($_GET['id']) ? $_GET['id'] : $_POST['sampleId'];
$projectId = ($_GET['pid']) ? $_GET['pid'] : $_POST['projectId'];

$is_admin = checkProjectAdminPrivilege($projectId);
if ($is_admin) {
	$title = "Projects";
	login_header($title);
} else {
	$redirect=$_SERVER['PHP_SELF'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

$sample = new Sample();

$map=array();
$map["packageId"]="sa1";
$map["label"]="sa4";
$map["volume"]="sa5";
$map["description"]="sa6";
$map["concentration1"]="sa7";
$map["concentration2"]="sa8";
$map["stored"]="sa9";
$map["notes"]="sa10";


if ($_POST ) {

	$data_from_post=from_POST_values(array_values($map));

	foreach($map as $k=>$v) {
		if (ereg("date$", $k)) {
			$$k=mysql::format_date($data_from_post[$v]);
		} else {
			$$k=$data_from_post[$v];
		}
	}
	$packageId=($packageId) ? $packageId : null;

	// --- find next sample number --- // 
	$newnumber=$sample->getNextNumber($packageId);
	$newnumberstr=$sample->format_number($newnumber);

	if ($_POST['btsubmit']=='add') {
		$sampleId = $sample->addSample($projectId, $packageId, $newnumber, $label, $volume, $description, $concentration1, $concentration2, $stored, $notes);

	} else if ($_POST['btsubmit']=='update') {
		$sample->updateSample($sampleId, $packageId, $label, $volume, $description, $concentration1, $concentration2, $stored, $notes);
	}
// --- redirect after submission --- //
	if ($_POST['btsubmit']=='add' || $_POST['btsubmit']=='update') {
		redirect($_GET['ln']);
	}
} 

if (empty($sampleId) || !($sample->checkSampleExistsbyId($sampleId))) {
	$title='- new sample';
	$action='add';
} else {
	$cursample = $sample->getSampleInfo($sampleId);
	$title='- update sample: '.$cursample['Name'];
	$action='update';

}

if ($_POST) {
	foreach($_POST as $k=>$v) {
		if (ereg("^sa",$k))
			$defaults[$k]=trim($v);
	}
}

$package=new Package();
$where=array("projectId"=>$projectId);
$packages=$package->getPackages($where, array('packageId', 'number', 'label'));
$packageslist[null]='P000 - internal';
foreach($packages as $pack) {
	$packageslist[$pack['packageId']]=$pack['number']." - ".$pack['label'];
}
if (!$packageId) {
	$newnumber=$sample->getNextNumber($packageId, $projectId);
	$newnumberstr=$sample->format_number($newnumber);
}

if ($sampleId) {
$cursample = $sample->getSampleInfo($sampleId);
foreach($map as $k=>$v) {
	$val=$cursample[$k];
	if (ereg("date$", $k)) {
			$val=mysql::format_date($val, "ymd", "mdy", "-" );
	}
	$defaults[$v]=$val;
}
$newnumberstr=$sample->format_number($cursample['number']);
}

project_header("Sample $title");
?>

<a href="<?=$_GET['ln'];?>">[ &laquo; back ]</a>
<p>
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
</p>
<?
require "inc/aform.php";
?>
<link href="css/aform.css" rel="stylesheet" type="text/css" />
<?
$form=new form();
$form->setPrefix("sa");
$form->action=$_SERVER['REQUEST_URI'];
$form->setDefaults($defaults);
$form->onsubmit="return validate();";
$form->addList("Package", $packageslist, 1, false, "use P000 for internal sample", true);
$form->addHiddenField('sampleId', $sampleId);
$form->addLabel("Sample Number", $newnumberstr);
$form->addField("Label", 20, true);
$form->addField("Approximate Volume (uL)", 20, true);
$form->addTextArea("Description", 5, 50, true);
$form->addField("Concentration (mg/L)", 20, false);
$form->addField("Concentration (pt/L)", 20, false);
$form->addField("Stored", 20, true, "RT, 4C, -80C");
$form->addTextArea("Notes", 5, 50, false);

$form->addSubmit("btsubmit", $action);

echo $form->display();
echo $form->getFormValidation();

project_footer();
?>

