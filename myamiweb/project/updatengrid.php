<?php

require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/packagelib.php";
require "inc/samplelib.php";
require "inc/gridlib.php";
require "inc/utilpj.inc.php";

$gridId = ($_GET['id']) ? $_GET['id'] : $_POST['gridId'];
$projectId = ($_GET['pid']) ? $_GET['pid'] : $_POST['projectId'];

$is_admin = checkProjectAdminPrivilege($projectId);
if ($is_admin) {
	$title = "Projects";
	login_header($title);
} else {
	$redirect=$_SERVER['PHP_SELF'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

$grid = new Grid();

$map=array();
$map["sampleId"]="gr2";
$map["type"]="gr3";
$map["grbox"]="gr4";
$map["grboxslot"]="gr5";
$map["grsubstrate"]="gr7";
$map["dilution"]="gr8";
$map["volume"]="gr9";
$map["plasma"]="gr10";
$map["vitrobotblot"]="gr11";
$map["vitrobotoffset"]="gr12";
$map["vitrobottemp"]="gr13";
$map["vitrobotrh"]="gr14";
$map["stored"]="gr15";
$map["stain"]="gr16";
$map["stainconc"]="gr17";
$map["waterwash"]="gr18";
$map["stainwash"]="gr19";
$map["stainvolume"]="gr20";
$map["datemade"]="gr21";
$map["comments"]="gr22";

if ($_POST ) {

	$data_from_post=from_POST_values(array_values($map));

	foreach($map as $k=>$v) {
		if (ereg("^date", $k)) {
			$$k=mysql::format_date($data_from_post[$v]);
		} else {
			$$k=$data_from_post[$v];
		}
	}

	$sampleId=($sampleId) ? $sampleId : null;

	// --- find next sample number --- // 
	$newgbnumber=$grid->getNextGridBoxNumber($sampleId);
	$newnumber=$grid->getNextNumber($sampleId, $type, $grbox);
	$newnumberstr=$grid->format_number($newnumber, $type);

	if ($_POST['btsubmit']=='add') {
		$gridId = $grid->addGrid($projectId, $sampleId, $newnumber, $grsubstrate, $volume, $datemade, $comments, $dilution, $type, $plasma, $vitrobotblot, $vitrobotoffset, $vitrobottemp, $vitrobotrh, $stored, $stain, $stainconc, $waterwash, $stainwash, $stainvolume, $grbox, $grboxslot);

	} else if ($_POST['btsubmit']=='update') {
		$curgrid = $grid->getGridInfo($gridId);
		$gridnumber = $curgrid['number'];
		if ($type!=$curgrid['type'] || $grbox!=$curgrid['grbox']) {
			$gridnumber=$newnumber;
		}
		$grid->updateGrid($gridId, $sampleId, $gridnumber, $grsubstrate, $volume, $datemade, $comments, $dilution, $type, $plasma, $vitrobotblot, $vitrobotoffset, $vitrobottemp, $vitrobotrh, $stored, $stain, $stainconc, $waterwash, $stainwash, $stainvolume,  $grbox, $grboxslot);
	}

	if ($_POST['btsubmit']=='add' || $_POST['btsubmit']=='update') {
		redirect($_GET['ln']);
	}
} 

if (empty($gridId) || !($grid->checkGridExistsbyId($gridId))) {
	$title='- new Grid';
	$action='add';
} else {
	$curgrid = $grid->getGridInfo($gridId);
	$title='- update  Grid: '.$curgrid['Name'];
	$action='update';

	$sample=new Sample();
	$where=array("projectId"=>$projectId, "sampleId"=>$curgrid['sampleId']);
	list($cursample)=$sample->getSamples($where, array('sampleId', 'number', 'label', 'packageId'));
	$package=new Package();
	$where=array("projectId"=>$projectId, "packageId"=>$cursample['packageId']);
	list($curpackage)=$package->getPackages($where);
	$title .= $curpackage['number']." - ".$cursample['number']." - ".$cursample['label'];

}

project_header("Grid $title");
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
$grids=array(
	'N'=>"Negative Stain",
	'V'=>"Vitreous Ice"
);

// --- set defaults for grid type/box --- //
$sampleId=null;
$gridtype="N";
$grbox=1;

if ($gridId) {
	foreach($map as $k=>$v) {
		$val=$curgrid[$k];
		if (ereg("^date", $k)) {
				$val=mysql::format_date($val, "ymd", "mdy", "-" );
		}
		$defaults[$v]=$val;
	}
	$gridtype=$curgrid['type'];
	$gridnumber=$curgrid['number'];
	$sampleId=$curgrid['sampleId'];
}
$sampleId=($data_from_post['gr2']) ? $data_from_post['gr2'] : $sampleId;
$gridtype=($data_from_post['gr3']) ? $data_from_post['gr3'] : $gridtype;
$grbox=($data_from_post['gr4']) ? $data_from_post['gr4'] : $grbox;
$defaults['gr2']=$sampleId;
$defaults['gr3']=$gridtype;
$defaults['gr4']=$grbox;

if ($gridtype!=$curgrid['type'] || $grbox!=$curgrid['grbox']) {
	$gridnumber=$grid->getNextNumber($sampleId, $gridtype, $grbox);
}

$numberstr=$grid->format_number($gridnumber, $gridtype);


$package=new Package();
$where=array("projectId"=>$projectId);
$packages=$package->getPackages($where);

foreach ((array)$packages as $k=>$package) {
	$sId = $package['packageId'];
	$packagenumbers[$sId] = $package['number'];
}

$sample=new Sample();
$where=array("projectId"=>$projectId);
$samples=$sample->getSamples($where, array('sampleId', 'number', 'label', 'packageId'));
foreach($samples as $samp) {
	$sampleslist[$samp['sampleId']]=$packagenumbers[$samp['packageId']]." - ".$samp['number']." - ".$samp['label'];
}
if (!$sampleId) {
	$sampleId=$samples[0]['sampleId'];
}
if (!$gridId) {
	$newnumber=$grid->getNextNumber($sampleId, $gridtype, $grbox);
	$numberstr=$grid->format_number($newnumber, $gridtype);
}
$newgbnumber=$grid->getNextGridBoxNumber($sampleId, $gridtype);

$gridboxes=array();
$gbprefix=($gridtype=="V") ? "G" : "B";
foreach (range(1, $newgbnumber+1) as $v) {
	$gridboxes[$v]=$gbprefix.$v;
}


$form=new form();
$form->setPrefix("gr");
$form->action=$_SERVER['REQUEST_URI'];
$form->setDefaults($defaults);
$form->onsubmit="return validate();";
$form->addHiddenField('gridId', $gridId);
$form->addList("Sample", $sampleslist, 1, false, "", true);
$form->addList("Grid type", $grids, 1, false, "types: Vitreous Ice, Negative Stain", true);
$form->addList("Grid box", $gridboxes, 1, false, "", true);
$nkeys[]=$form->addField("Grid slot", 20, true);
$form->addLabel("Grid number", $numberstr);
$form->addField("Grid substrate", 20, true);
$form->addTextArea("Sample dilution ",1 ,20, true);
$form->addField("Sample volume (uL)", 20, true);
$form->addField("Plasma cleaned time (s)", 20);
$vkeys[]=$form->addField("Vitrobot: Blot time (s)", 20, true);
$vkeys[]=$form->addField("Vitrobot: Offset (mm)", 20, true);
$vkeys[]=$form->addField("Vitrobot: temperature", 20, true);
$vkeys[]=$form->addField("Vitrobot: RH", 20, true);
$vkeys[]=$form->addField("Stored", 20, true, "Number of dewar storing grid");

$nkeys[]=$form->addField("Stain", 20, true);
$nkeys[]=$form->addField("Stain concentration", 20, true);
$nkeys[]=$form->addTextArea("Water wash (#x, uL)", 2, 20);
$nkeys[]=$form->addTextArea("Stain wash (#x, uL)", 2, 20);
$nkeys[]=$form->addField("Stain volume (uL)", 20, true);


$form->addDate(($gridtype=="N") ? "Date made" : "Date frozen", 20, true);
$form->addTextArea("Comments", 3, 50, false);

$form->addSubmit("btsubmit", $action);

$keys=$form->getFieldkeys();
$keys=($gridtype=="N") ? array_diff($keys, $vkeys) : array_diff($keys, $nkeys);


echo $form->display($keys);
echo $form->getFormValidation($keys);

project_footer();
?>
