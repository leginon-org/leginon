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

$sample=new Sample();
$where=array("projectId"=>$projectId, "packageId"=>$packageId);
$samples=$sample->getSamples($where);

$columns=array();
$display_header=true;

project_header("EM Image Report $title");
?>

<?php
foreach ($samples as $k=>$s) {
	$sId = $s['sampleId'];
	$sampleIds[]=$sId;
	$samples[$k]['sample']=$packagenumber.".".$s['number'];
	$samplenumbers[$sId] = $s['number'];
	$samplepackages[$sId] = $packagenumber;
	$samplelabels[$sId] = $s['label'];
}

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

	$experimentIds = $project->getExperiments($projectId,'ASC');
	$exemplars=array();

  $sessions=array();
  $experiments=array();

	$quality="png";
	$size=512;
	$l=array('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j');
	$labels = array (
		'outer'=>'Higher magnification (%sx) of the field of view in (a) approximately represented by the outer yellow box.',
		'mid'=>'Higher magnification (%sx) of the field of view in (a) approximately represented by the middle yellow box.',
		'inner'=>'Higher magnification (%sx) of the field of view in (a) approximately represented by the inner yellow box.'
);
	$imageindex=0;
  foreach ($experimentIds as $k=>$exp) {
    $info = getExperimentInfo($exp, $hidden=true);
		$presetinfo=get_preset_mag($info, 0);
		$sessionId = $info['SessionId'];

		foreach ($samples as $s) {
			if (ereg("^".$s['sample'], $info['Purpose'])) {

				$filenames=getExemplars($sessionId);
				$name='None';
				if ($filenames) {
					$presetimages = array();
					foreach ($filenames as $i=>$filename) {
						$imageId=$filename['id'];
						++$imageindex;

						$pindex=0; 
						$datatypes=array();
						foreach ($presetinfo as $preset=>$pinfo) {
							if (!ereg("^en[1-9]{0,}|^hl", $preset)){
								continue;
							}
							$datatypes[$preset]=$pinfo['magnification'];	
						}
						asort($datatypes);
						$datatypes = array_keys($datatypes);
						if (in_array('en', $datatypes)) {
							$presetlabels['en']=$labels['inner'];
						}
						if (in_array('en1', $datatypes)) {
							$presetlabels['en1']=$labels['outer'];
						}
						if (in_array('en2', $datatypes)) {
							$presetlabels['en2']=$labels['inner'];
							$presetlabels['en']=$labels['mid'];
						}

						if (is_array($datatypes)) {
							$presetmemo=array();
							foreach ($datatypes as $datatype) {
								$rel = $leginondata->findImage($imageId, $datatype);
								if ($rel) {
									$relId = $rel['id'];
									### get only sq and en's preset 
									$preset=$rel['preset'];
									if (!ereg("^en[1-9]{0,}|^hl", $preset)){
										continue;
									}
									if (in_array($preset, $presetmemo)) {
										continue;
									}
									$presetmemo[]=$preset;
									$mag = $presetinfo[$preset]['magnification'];
									$fmag = number_format($mag);
									if (!$title = $presetlabels[$preset]) {
										$figurelabel = $s['label'].' ('.$info['Purpose'].'; '.$info['Name'].')';
										$title = 'Image of sample %s at a magnification of %sx.';
										$title = sprintf($title, $figurelabel, $fmag);
									} else {
										$title = sprintf($title, $fmag);
									}
									#$title = $info['Purpose'];
									$relfilename = $leginondata->getFilenameFromId($relId);
									$imgopt="?imgsc=getimg.php&session=".$sessionId."&id=".$imageId."&preset=".$preset."&s=".$size."&t=".$quality."&tg=1&sb=1&flt=default&binning=auto&colormap=0&autoscale=s;3&df=3&lj=1&g=1&opt=2";
									$name='<p>';
									$name.='<img alt="'.$relfilename.'" src="'.BASE_URL.'getimg.php'.$imgopt.'">';
									$name.='<li style="display: inline"><b>Figure '.$imageindex.$l[$pindex].'.</b> '.$title.'</li>';
									$name.='</p>';
									$pindex++;
									$presetimages[]=$name;
								} else break;
							}
						}

					}
				}
				if ($presetimages) {
					$exemplars[$exp['name']]=implode("\n", $presetimages);
				}


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
				$experiments[$k]['exemplars']=$exemplars[$info['Name']];
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
);

$display_header=true;
echo data2table($experiments, $columns_tag, $display_header);
echo "<br />";
$columns_tag=array(
	'exemplars'=>'Exemplar images'
);
echo '<div style="margin-left: 10em;">';
echo data2str($experiments, $columns_tag);
echo '</div>';
?>
</p>
<?php
project_footer();
?>
