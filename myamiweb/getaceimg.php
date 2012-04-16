<?php
require "inc/leginon.inc";
require "inc/image.inc";
require "inc/project.inc";
require "inc/particledata.inc";
require "inc/ace.inc";

$imgId=$_GET['id'];
$preset=$_GET['preset'];
$imgsize=$_GET['s'];
$graphsc_x=$_GET['scx'];
$graphsc_y=$_GET['scy'];
if (!is_numeric($graphsc_x)) $graphsc_x=1;
if (!is_numeric($graphsc_y)) $graphsc_y=1;

switch($_GET['g']){
	case 1: $graph="graph1"; break;
	case 2: $graph="graph2"; break;
}

switch($_GET['m']){
	case 1: $ctfmethod=""; break;
	case 2: $ctfmethod="ace1"; break;
	case 3: $ctfmethod="ace2"; break;
	case 4:
		$ctfmethod="ctffind"; 
		$graph="graph1";
		break;
}

$opt=trim($_GET['opt']);
if (!is_numeric($opt)) {
	$opt=15;
}
if ($opt&1) {
	$des['d1']['t']=$ACE['d1'];
	$des['d1']['c']='navy';
}
if ($opt&2) {
	$des['d2']['t']=$ACE['d2'];
	$des['d2']['c']='red';
}
if ($opt&4) {
	$des['d3']['t']=$ACE['d3'];
	$des['d3']['c']='orange';
}
if ($opt&8) {
	$des['d4']['t']=$ACE['d4'];
	$des['d4']['c']='green';
}

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo['sessionId'];
$filename = $leginondata->getFilenameFromId($imgId);
$normfile = trim($filename).'.norm.txt';
$ctf = new particledata();
list($ctfdata)  = $ctf->getCtfInfoFromImageId($imgId, $order=False, $ctfmethod);
$aceparams = $ctf->getAceParams($ctfdata['acerunId']);

if ($ctfmethod==='') {
	// If the best CtfInfo found for the ImageId is from ctffind,
	// we need to set ctfmethod to ctffind in order to get the image path
	if ($aceparams['REF|ApCtfTiltParamsData|ctftilt_params'] !== null) {
		$ctfmethod='ctffind';
		$graph="graph1";
	}
}
if ($ctfmethod==='ctffind') {
	$path=$ctfdata['path'].'/';
}
else {
	$path=$ctfdata['path'].'/opimages/';
}

$filename=$path.$ctfdata[$graph];
(array)$ctfimageinfo = @getimagesize($filename);
$imagecreate = 'imagecreatefrompng';
$imagemime = 'image/png';
switch ($ctfimageinfo['mime']) {
	case 'image/jpeg':
		$imagecreate = "imagecreatefromjpeg";
		$imagemime = $ctfimageinfo['mime'];
	break;
}
if ($img=@$imagecreate($filename)) {
	resample($img, $imgsize);
} else {
	$acedatafile =$ctfdata['path'].'/'.$normfile;
	if (file_exists($acedatafile)) {
		$acedata=readAceNormFile($acedatafile);
		$imagepixelsize = $imageinfo['pixelsize']*$imageinfo['binning'];
		$imagesize = min($imageinfo['dimx'],$imageinfo['dimy']);
		//ace2 datasize is not a constant, so count from acedata
		$datasize = count($acedata['d1']);
		$acebin = ($aceparams['bin']) ? $aceparams['bin']:1;
		$inverse_pixelsize = 1e-10 / (2*$acebin*$datasize*$imagepixelsize);

		require 'inc/jpgraph.php';
		require 'inc/jpgraph_line.php';

		$d1= $acedata['d1'];
		$d2= $acedata['d2'];
		$d3= $acedata['d3'];
		$d4= $acedata['d4'];
		if ($graphsc_x<1 || $graphsc_y<1){
			$d1=rescaleArray($d1,$graphsc_x,$graphsc_y);
			$d2=rescaleArray($d2,$graphsc_x,$graphsc_y);
			$d3=rescaleArray($d3,$graphsc_x,$graphsc_y);
			$d4=rescaleArray($d4,$graphsc_x,$graphsc_y);
		}
		$inverse_distance= array();
		for ($i = 0; $i < count($d1);$i++) {
			$inverse_distance[]=$i*$inverse_pixelsize;
		}

		$graph = new Graph(512,400);
		$graph->SetScale("linlin");
		$graph->img->SetMargin(40,40,80,40);

		$graph->ygrid->SetFill(true,'#EFEFEF@0.5','#BBCCFF@0.5');
		$graph->SetTickDensity(TICKD_SPARSE);
		$graph->xscale->SetAutoTicks();
		$graph->xaxis->title->Set('1/Angstrom');

		$ngraph=count((array)$des);

		foreach ((array)$des as $k=>$val) {
			unset($p);
			$p = new LinePlot($$k,$inverse_distance);
			$p->SetColor($val['c']);
			$p->SetLegend($val['t']);
			if ($k=='d1' && $ngraph>1) {
				$graph->AddY2($p);
			} else {
				$graph->Add($p);
			}
		}
		if ($ngraph>1 && $des['d1']) {
			$graph->SetY2Scale("lin");
			$graph->y2axis->SetColor($des['d1']['c']);
		}
		$graph->legend->Pos(0,0,'right','top');

		$graph->legend->SetShadow('gray@0.4',5);
		$graph->Stroke();

	} else {
		header('Content-type: '.$imagemime);
		$blkimg = blankimage();
		imagepng($blkimg);
		imagedestroy($blkimg);
	}
}
function rescaleArray($vals,$scx,$scy) {
	// need to add a selection for scaling
	$maxval = max($vals)*$scy;
	$vlen = count($vals)*$scx;
	$newvals=array();

	$valcount = 0;
	foreach ($vals as $val) {
		if ($val > $maxval) $newvals[]=$maxval;
		elseif (-$val > $maxval) $newvals[]=-$maxval;
		else $newvals[]=$val;
		$valcount++;
		if ($valcount > $vlen) break;
	}
	return $newvals;
}
?>
