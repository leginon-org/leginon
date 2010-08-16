<?php

require "inc/project.inc.php";
require "inc/gridlib.php";
require "inc/packagelib.php";
require "inc/samplelib.php";
require "inc/aform.php";
require "inc/utilpj.inc.php";
require_once "inc/getleginondata.php";

$package = new Package();

$packageId = ($_GET['id']) ? $_GET['id'] : $_POST['packageId'];
$projectId = ($_GET['pid']) ? $_GET['pid'] : $_POST['projectId'];
checkProjectAccessPrivilege($projectId);

$project = new project();
$projectinfo = $project->getProjectInfo($projectId);
$projectname = $projectinfo['Name'];

$curpackage = $package->getPackageInfo($packageId);
$packagenumber = $package->format_number($curpackage['number']);
$packagenumber = "$projectname.$packagenumber";

$packagelabel = $curpackage['label'];
$condition = strtolower($curpackage['condition']);
$shipmethod = $curpackage['shipmethod'];
$arrival = $curpackage['arrivedate']." ".$curpackage['arrivetime'];
$carrier = $curpackage['expcarrier'];
$tracking = $curpackage['carriernumber'];
$numaliquots = $curpackage['numaliquots'];
$note = trim($curpackage['note']);

$sample=new Sample();
$where=array("projectId"=>$projectId, "packageId"=>$packageId);
$samples=$sample->getSamples($where);

	
$columns=array();
$display_header=true;

project_header("Report $title");
?>
<u><b>Section 1: Sample shipping, receiving and handling.</b></u>

<?php
$section1='<p>
<ul>
	Package %s received in %s condition on %s.
</ul>
<ul>
	Date/Time of sample arrival: %s
</ul>
<ul>
	Carrier/Tracking Number: %s %s
</ul>
</p>
<p>
	The package was labeled "%s" and contained %s vials labeled as follows:
</p>';
$s=sprintf($section1, $packagenumber, $condition, $shipmethod, $arrival, $carrier, $tracking, $packagelabel, $numaliquots);
if ($curpackage) {
	echo $s;
} else {
	echo "<p>Internal Package</p>";
}
$columns=array(
	"label"=>"Label",
	"sample"=>"NIS Sample ID",
	"volume"=>"Approx. Volume (ul)",
	"stored"=>"Where Stored (RT, 4C, -80C)"
);
foreach ($samples as $k=>$s) {
	$sId = $s['sampleId'];
	$sampleIds[]=$sId;
	$samples[$k]['sample']=$packagenumber.".".$s['number'];
	$samplenumbers[$sId] = $s['number'];
	$samplepackages[$sId] = $packagenumber;
	$samplelabels[$sId] = $s['label'];
}
echo data2table($samples, $columns, $display_header);
if (!empty($note)) {
	echo '<p><img alt="red arrow" align="middle" src="img/arrow_red.png">
<span style="display:inline-block; vertical-align:middle">
<span style="font-weight: bold">Note: </span>'.$note.'</span></p>';
}
?>
<p>
<u><b>Section 2: EM grid preparation</b></u>
<?php
$griddata=new Grid();
$grids=$griddata->getGridsFromPackage($packageId);

foreach ((array)$grids as $k=>$grid) {
	$sampleId=$grids[$k]['sampleId'];
	if (!in_array($sampleId, $sampleIds)) {
		continue;
	}

	$gridIdstr=$samplepackages[$sampleId].".".$samplenumbers[$sampleId].".".$grid['grbox'].".".$grid['number'];
	$grids[$k]['sample']=$samplelabels[$sampleId];
	$grids[$k]['gridIdstr']=$gridIdstr;
	$grids[$k]['grsubstrate']=array($grid['grsubstrate'], 'width="200px" nowrap ');
	if ($grid['type']=="V") {
		$grids_v[]=$grids[$k];
	} else {
		$grids_n[]=$grids[$k];
	}
}

$display_header=true;
$columns=array();
$columns['sample']='Sample #/ Label';
$columns['gridIdstr']='Grid Id';
$columns['grsubstrate']='Grid substrate';
$columns['comments']='Comment';
$columns['volume']='Sample volume (uL)';
$columns['dilution']='dilution';

$columns_v=array_merge($columns, array(
'plasma'=>'Plasma cleaned time (s)',
'vitrobotblot'=>'Vitrobot: Blot time (s)',
'vitrobotoffset'=>'Vitrobot: Offset (mm)',
'vitrobottemp'=>'Vitrobot: temperature (C)',
'vitrobotrh'=>'Vitrobot: RH (%)'
));

$columns_n=array_merge($columns, array(
'stain'=>'Stain',
'stainconc'=>'Stain concentration',
'wash'=>'Stain wash (#x, uL)',
'stainvolume'=>'Stain volume (uL)'
));


echo "<ul>";
if (is_array($grids_v)) {
echo "<li><b>Cryo grids</b>";
echo data2table($grids_v, $columns_v, $display_header);
echo "</li>";
}
if (is_array($grids_n)) {
echo "<li><b>Negative stain grids</b>";
echo data2table($grids_n, $columns_n, $display_header);
echo "</li>";
}
echo "</ul>";
?>
</p>
<p>
<u><b>Section 3: EM imaging</b></u>
<br />
<?php
	$imgreportlink='<a alt="image report" class="header" href="reportimg.php?pid='.$projectId.'&id='.$packageId.'&ln='.$ln.'">[ view image report ]</a>';
	$thumbreportlink='<a alt="thumbnail report" class="header" href="reportimgthumb.php?pid='.$projectId.'&id='.$packageId.'&ln='.$ln.'">[ view thumbnail report ]</a>';
	$imgreportpdflink='<a alt="download pdf" class="header" href="reportpdf.php?pid='.$projectId.'&id='.$packageId.'">[ download pdf report ]</a>';
	echo '<span style="margin: 10px">'.$imgreportlink.'</span>';
	echo '<span style="margin: 10px">'.$thumbreportlink.'</span>';
	echo '<span style="margin: 10px">'.$imgreportpdflink.'</span>';

	$experimentIds = $project->getExperiments($projectId,'ASC');
	$exemplars=array();
  $sessions=array();
  $experiments=array();

  foreach ($experimentIds as $k=>$e) {
		$exp = $e['leginonId'];
		$info = getExperimentInfo($exp, $hidden=true);
		foreach ($samples as $s) {
			if (ereg("^".$s['sample'], $info['Purpose'])) {
				$filenames=getExemplars($exp);
				$name='None';
				if ($filenames) {
					$name='';
					foreach ($filenames as $filename) {
						$opt='&imageId='.$filename['id'].'&pre=exemplar&v1pre=hl';
						$name.='<a target="2way" class="header" href="'.BASE_URL.'2wayviewer.php?expId='.$info['SessionId'].$opt.'">';
						$name.=$filename['name'];
						$name.='</a>';
						$name.='<br>';
					}
				}
			$exemplars[$exp]=$name;

				$gridId= $griddata->getGridId($info);
				$gridinfo=$griddata->getGridInfo($gridId);
				$experiments[$k]['label']=$s['label'];
				$experiments[$k]['comment']=$gridinfo['comments'];
				$experiments[$k]['dilution']=$gridinfo['dilution'];
				$experiments[$k]['name']=$info['Name'];
				$experiments[$k]['purpose']=$info['Purpose'];
				$totimg = 0;

				$presetinfo=get_preset_mag($info, 0);
				$ntotimg=$ndose=$ndefocus=array();
				foreach ($presetinfo as $pr=>$pifo) {
					if (!ereg("^en[1-9]{0,}", $pr)){
							continue;
					}
					$totimg+=$pifo['totimg'];
					$ntotimg[]=$pifo['magnification']."x <b>$pr</b>: ".$pifo['totimg'];
					$ndose[]="<b>$pr</b>: ".$pifo['dose']."</font>";
					$ndefocus[]="<b>$pr</b>: ".$pifo['defocus'];
				}
				$experiments[$k]['totalimg']=$totimg;
				$experiments[$k]['n']=implode("<br />",$ntotimg);
				$experiments[$k]['dose']=array(implode("<br />",$ndose), 'width="150px"');
				$experiments[$k]['defocus']=array(implode("<br />",$ndefocus), 'width="100px"');
				$experiments[$k]['reporttag']=$s['label'].' ('.$info['Purpose'].'; '.$info['Name'].')';
				$experiments[$k]['exemplars']=$exemplars[$info['SessionId']];
		}
		}
	}

function get_preset_mag($info, $mag) {
	$presetinfo=array();
	foreach ($info as $k=>$v) {
		if (!ereg("^Total_.* x", $k)) {
			continue;
		}
		list($imgnb, $dose, $defocusmin, $defocusmax) = split("	", $info[$k]);
		
		ereg("Total_(.*) x", $k, $match);
		$preset=$match[1];
		$cmag=ereg_replace("^Total_.* x", "", $k);
		if ($cmag>=$mag) {
			$presetinfo[$preset]['magnification']=$cmag;
			$presetinfo[$preset]['totimg']=$imgnb;
			$presetinfo[$preset]['dose']=$dose;
			$presetinfo[$preset]['defocus']=($defocusmin==$defocusmax) ? $defocusmin : "$defocusmin, $defocusmax";
		}
	}
	return $presetinfo;
}

function get_totimg_mag($info, $mag) {
	$tot_img=0;
	foreach ($info as $k=>$v) {
		if (!ereg("^Total_.* x", $k)) {
			continue;
		}
		$cmag=ereg_replace("^Total_.* x", "", $k);
		if ($cmag>=$mag) {
			$tot_img+=$info[$k];
		}
	}
	return $tot_img;
}

$columns_tag=array(
  'reporttag'=>'SampleID (GridID; ExptID)',
	'exemplars'=>'Exemplar images'
);

$columns=array(
  'label'=>'Sample #/ Label',
  'purpose'=>'Grid ID',
  'name'=>'Expt ID',
	'totalimg'=>'&Sigma; # High Mag',
  'n'=>'# High Mag (non-hidden)',
	'dose'=>'Dose (e<sup>&ndash;</sup>/&Aring;<sup>2</sup>)',
	'defocus'=>'Defocus'
  );
$columns_r=array(
  'label'=>'Sample #/ Label',
  'purpose'=>'Grid ID',
	'comment'=>'Comment',
	'dilution'=>'Dilution',
  'name'=>'Expt ID',
#  'n'=>'# High Mag (non-hidden)',
	'totalimg'=>'&Sigma; # High Mag'
  );

$display_header=true;
echo "<br />";
echo data2table($experiments, $columns_tag, $display_header);
echo "<br />";
echo data2table($experiments, $columns_r, $display_header);
echo "<br />";
echo data2table($experiments, $columns, $display_header);
?>
</p>
<?php
project_footer();
?>
