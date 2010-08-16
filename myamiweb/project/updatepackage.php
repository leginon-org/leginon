<?php

require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/confirmlib.php";
require "inc/packagelib.php";
require "inc/utilpj.inc.php";
require "inc/aform.php";

$packageId = ($_GET['id']) ? $_GET['id'] : $_POST['packageId'];
$projectId = ($_GET['pid']) ? $_GET['pid'] : $_POST['projectId'];

$is_admin = checkProjectAdminPrivilege($projectId);
if ($is_admin) {
	$title = "Projects";
	login_header($title);
} else {
	$redirect=$_SERVER['PHP_SELF'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

$package = new Package();

// --- map db fields and form --- //
	$map=array();
	$map["confirmId"]="f3";
	$map["label"]="f5";
	$map["expdate"]="f6";
	$map["expcarrier"]="f7";
	$map["carriernumber"]="f8";
	$map["expnumaliquots"]="f9";
	$map["sampledescription"]="f10";
	$map["expnote"]="f11";
	$map["arrivedate"]="f12";
	$map["arrivetime"]="f13";
	$map["condition"]="f14";
	$map["shipmethod"]="f15";
	$map["temp"]="f16";
	$map["numaliquots"]="f17";
	$map["notified"]="f18";
	$map["note"]="f19";

// --- find next package number --- // 

$newnumber=$package->getNextNumber($projectId);
$newnumberstr=$package->format_number($newnumber);

if ($_POST ) {
	$data_from_post=from_POST_values(array_values($map));

	foreach($map as $k=>$v) {
		if (ereg("date$", $k)) {
			$$k=mysql::format_date($data_from_post[$v]);
		} else {
			$$k=$data_from_post[$v];
		}
	}

	if (!$confirmId) {
		$confirmId=null;
	}

	if ($_POST['btsubmit']=='add') {
		$number=$newnumber;
		$packageId = $package->addPackage($projectId, $confirmId, $number, $label, $expdate, $expcarrier, $carriernumber, $expnumaliquots, $sampledescription, $expnote, $arrivedate, $arrivetime, $condition, $shipmethod, $temp, $numaliquots, $notified, $note);

	} else if ($_POST['btsubmit']=='update') {
		$package->updatePackage($packageId, $projectId, $confirmId, $label, $expdate, $expcarrier, $carriernumber, $expnumaliquots, $sampledescription, $expnote, $arrivedate, $arrivetime, $condition, $shipmethod, $temp, $numaliquots, $notified, $note);
	}

// --- redirect after submission --- //
	if ($_POST['btsubmit']=='add' || $_POST['btsubmit']=='update') {
		redirect($_GET['ln']);
	}
} 

if (empty($packageId) || !($package->checkPackageExistsbyId($packageId))) {
	$title='- new package';
	$action='add';
} else {
	$title='- update package: '.$curpackage['Name'];
	$action='update';

}

$confirm=new Confirm();
$where=array("projectId"=>$projectId);
$confirms=$confirm->getConfirms($where, array('confirmId', 'confirmnum'));
$confirmlist[0]=$confirm->format_number(0);
foreach($confirms as $c) {
	$confirmlist[$c['confirmId']]=$confirm->format_number($c['confirmnum']);
}

if ($packageId) {
$curpackage = $package->getPackageInfo($packageId);
foreach($map as $k=>$v) {
	$val=$curpackage[$k];
	if (ereg("date$", $k)) {
			$val=mysql::format_date($val, "ymd", "mdy", "-" );
	}
	$defaults[$v]=$val;
}
$newnumberstr=$package->format_number($curpackage['number']);
}
	

project_header("Package $title");
?>

<a href="<?=$_GET['ln'];?>">[ &laquo; back ]</a>
<p>
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
</p>
<link href="css/aform.css" rel="stylesheet" type="text/css" />
<?

$form=new form();
$form->action=$_SERVER['REQUEST_URI'];
$form->setDefaults($defaults);
$form->onsubmit="return validate();";

$form->addHiddenField('packageId', $packageId);
$form->addHiddenField('projectId', $projectId);
$form->addList("Confirmation", $confirmlist, 1, false, "", false);
$form->addLabel("Package number", $newnumberstr);
$form->addField("Label", 20, true);
$form->addDate("Expected date of arrival", 20, false);
$form->addField("Expected carrier", 20, false);
$form->addField("Carrier number", 20, false);
$form->addField("Expected number of aliquots", 20, false);
$form->addTextArea("Sample description", 4, 50, false);
$form->addTextArea("Carrier Note", 2, 20);
if ($packageId) {
$form->addDate("Date of sample arrival", 20, true);
$form->addTime("Time of sample arrival", 20, true);
$form->addField("Condition of package", 20, true, "Good, fair, poor");
$form->addTextArea("Shipping method", 2, 20, true, "Room temp, ice packs, dry ice");
$form->addField("Expected sample temperature maintained", 20, true, "Yes/No");
$form->addField("Number of aliquots", 20, true);
$form->addField("Sender was notified", 20, false, "Yes/No");
$form->addTextArea("Note", 2, 20);
}

$form->addSubmit("btsubmit", $action);
// $form->add('<input type="button" onclick="validate()" />');


echo $form->display();
echo $form->getFormValidation();

project_footer();
?>
