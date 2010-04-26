<?php
require "inc/leginon.inc";
require "inc/image.inc";
require "inc/project.inc";
require "inc/particledata.inc";
require "inc/ace.inc";

$imgId=$_GET['id'];
$preset=$_GET['preset'];
$imgsize=$_GET['s'];

switch($_GET['g']){
	case 1: $graph="graph1"; break;
	case 2: $graph="graph2"; break;
	// show ctffind image
	case 3:
		$graph="graph1";
		$ctffindvals=True;
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
if ($ctffindvals) {
	list($ctfdata)  = $ctf->getCtfInfoFromImageId($imgId, $order=False, $ctffind=True);
	$path=$ctfdata['path'].'/';
}
else {
	list($ctfdata)  = $ctf->getCtfInfoFromImageId($imgId);
	$path=$ctfdata['path'].'/opimages/';
}
$filename=$path.$ctfdata[$graph];

(array)$imageinfo = @getimagesize($filename);
$imagecreate = 'imagecreatefrompng';
$imagemime = 'image/png';
switch ($imageinfo['mime']) {
	case 'image/jpeg':
		$imagecreate = "imagecreatefromjpeg";
		$imagemime = $imageinfo['mime'];
	break;
}

if ($img=@$imagecreate($filename)) {
		resample($img, $imgsize);
} else {
	$acedatafile =$ctfdata['path'].'/'.$normfile;
	if (file_exists($acedatafile)) {
		$acedata=readAceNormFile($acedatafile);
		
		require 'inc/jpgraph.php';
		require 'inc/jpgraph_line.php';

		$d1= $acedata['d1'];
		$d2= $acedata['d2'];
		$d3= $acedata['d3'];
		$d4= $acedata['d4'];

		$graph = new Graph(512,400);
		$graph->SetScale("linlin");
		$graph->img->SetMargin(40,40,80,40);

		$graph->ygrid->SetFill(true,'#EFEFEF@0.5','#BBCCFF@0.5');
		$graph->SetTickDensity(TICKD_SPARSE);
		$graph->xscale->SetAutoTicks();

		$ngraph=count((array)$des);

		foreach ((array)$des as $k=>$val) {
			unset($p);
			$p = new LinePlot($$k);
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
?>
