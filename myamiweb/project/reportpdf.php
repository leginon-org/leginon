<?php

/**
 *	This script requires pdflib Lite 1.2.7 or newer and pdf wrapper from pear
*/
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

$reportname='report.'.$packagenumber;
	
$columns=array();
$display_header=true;

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

	$img_data = array();

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
	$name='';
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
		$fmag = number_format($presetinfo[$preset]['magnification']);
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
		$img_link="http://localhost".BASE_URL.'getimg.php'.$imgopt;
		$figure = 'Figure '.$imageindex.$l[$pindex];
		$img_data[]=array('link'=>$img_link, 'figure'=>$figure, 'title'=>$title);
		$pindex++;
	} else break;
}
}

}
}
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

$p = PDF_new();
if (PDF_begin_document($p, "", "") == 0) {
     die("Error: " . PDF_get_errmsg($p));
}
PDF_set_info($p, "Creator", "NanoImaging Services Inc.");
PDF_set_info($p, "Title", "Image Report");
// --- letter format --- //
$p_width = 612;
$p_height= 792;

// --- set document font
$font = PDF_load_font($p, "Helvetica", "winansi", "");
$font_bold = PDF_load_font($p, "Helvetica-Bold", "winansi", "");

$img_size = 512;
$img_quality = 'png';


foreach ($img_data as $k=>$imageinfo) {

	PDF_begin_page_ext($p, $p_width, $p_height, ""); // This is letter.

	$url = $imageinfo['link'];
	$figure = $imageinfo['figure'].'. ';
	$title = $imageinfo['title'];

	if ($stream = fopen($url, 'r')) {
		 $imgstream = stream_get_contents($stream, -1);
		 fclose($stream);
	}

	$pvf_filename = "image".$k.".jpg";

	PDF_create_pvf($p, $pvf_filename, $imgstream, "");
	$image = PDF_load_image($p, "png", $pvf_filename,"");
	$img_pos_x = ($p_width - $img_size) / 2;
	$img_pos_y = ($p_height - $img_size) / 2;
	PDF_fit_image($p, $image, $img_pos_x, $img_pos_y, '');
	PDF_delete_pvf($p, $pvf_filename);

	PDF_setfont($p, $font, 12.0);
	PDF_set_text_pos($p, $img_pos_x, $img_pos_y-20);
	$title = wordwrap($title, 80, "\n");
	$text = explode("\n", $title);
	foreach ($text as $ln=>$line) {
		if (!$ln) {
			PDF_setfont($p, $font_bold, 12.0);
			PDF_show($p, $figure);
			PDF_setfont($p, $font, 12.0);
			PDF_show($p, $line );
		} else {
			PDF_continue_text($p, $line);
		}
	}

	PDF_end_page_ext($p, "");

}

PDF_end_document($p, "");
$buf = PDF_get_buffer($p);
$len = strlen($buf);
header("Content-type: application/pdf");
header("Content-Length: $len");
header("Content-Disposition: inline; filename=".$reportname.".pdf");
echo $buf;
?>
