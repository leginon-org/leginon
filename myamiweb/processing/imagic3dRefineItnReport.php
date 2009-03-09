<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";
  
// get refinement parameters
$refineId = $_GET['refineId'];
$expId = $_GET['expId'];

$formAction = $_SERVER['PHP_SELF']."?expId=$expId&refineId=$refineId";

$javascript="<script src='../js/viewer.js'></script>\n";

processing_header("IMAGIC 3d Refinement Iteration Report","IMAGIC 3d Refinement Iteration Report Page", $javascript);

$html .= "<form name='iterations' method='post' action='$formAction'>\n";

$particle = new particledata();

// get reference-free classification parameters for refinement run
$refineparams = $particle->getImagic3dRefinementParamsFromRefineId($refineId);

//print_r($refineparams);
if ($refineparams[0]['REF|ApNoRefClassRunData|norefclass']) {
	$norefClassId = $refineparams[0]['REF|ApNoRefClassRunData|norefclass'];
	$norefclassdata = $particle->getNoRefClassRunData($norefClassId);
	$norefId = $norefclassdata['REF|ApNoRefRunData|norefRun'];
	$norefdata = $particle->getNoRefParams($norefId);
	$norefpath = $norefdata['path'];
	$norefclassfilepath = $norefclassdata['classFile'];
	$clsavgfile = $norefpath."/".$norefclassfilepath.".img";
}
elseif ($refineparams[0]['REF|ApClusteringStackData|clusterclass']) {
	$clusterid = $refineparams[0]['REF|ApClusteringStackData|clusterclass'];
	$clusterdata = $particle->getClusteringStackParams($clusterid);
	$clsavgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];	
}

########################### BASIC REFINEMENT INFO ##############################

// basic refinement run info
$title = "Refinement info";
if ($refineparams[0]['REF|ApNoRefClassRunData|norefclass']) {
	$clsavgs = "<a href='viewstack.php?file=$clsavgfile&expId=$sessionId&norefId=$norefId&norefClassId=$norefClassId'>$norefclassfilepath</a>";
}
elseif ($refineparams[0]['REF|ApClusteringStackData|clusterclass']) {
	$clsavgs = "<a href='viewstack.php?file=$clsavgfile&expId=$sessionId&clusterId=$clusterid'>$clusterdata[avg_imagicfile]</a>";
}

$refinementinfo = array(
	'id'=>$refineparams[0]['DEF_id'],
	'name'=>$refineparams[0]['runname'],
	'description'=>$refineparams[0]['description'],
	'path'=>$refineparams[0]['path'],
	'class averages used for refinement'=>$clsavgs,
	'boxsize'=>$refineparams[0]['boxsize'],
	'pixelsize'=>$refineparams[0]['pixelsize']
);

$particle->displayParameters($title,$refinementinfo,array(),$expId);

// get total number of iterations for refinement
$numiters = count($refineparams);




########################### 3d0 Model Info ##############################


$html.= "<br><h4> Initial 3d0 Model Selected for Refinement </h4>";
$html.= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html.= "<TR>";

$imagic3d0Id = $refineparams[0]['REF|ApImagic3d0Data|imagic3d0run'];
$modeldata = $particle->getImagic3d0Data($imagic3d0Id);

// get 3 initial projections for angular reconstitution associated with model		
$projections = $modeldata['projections'];
$projections = explode(";", $projections);
// check to see if initial model was created from reference-free classification or reclassification
if ($modeldata['REF|ApImagicReclassifyData|reclass'])  {
	$clsavgparams = $particle->getImagicReclassParamsFrom3d0($imagic3d0Id);
	$reclassnum = $clsavgparams['DEF_id'];
	$norefClassId = $clsavgparams['REF|ApNoRefClassRunData|norefclass'];
	$clsavgpath = $clsavgparams['path']."/".$clsavgparams['runname'];
	$classimgfile = $clsavgpath."/reclassified_classums_sorted.img";
	$classhedfile = $clsavgpath."/reclassified_classums_sorted.hed";
}
if ($modeldata['REF|ApNoRefClassRunData|norefclass']) {
	$clsavgparams = $particle->getNoRefClassRunParamsFrom3d0($imagic3d0Id);
	$norefClassId = $clsavgparams['DEF_id'];
	$norefId = $clsavgparams['REF|ApNoRefRunData|norefRun'];
	$norefparams = $particle->getNoRefParams($norefId);
	$clsavgpath = $norefparams['path']."/".$clsavgparams['classFile'];
	$classimgfile = $clsavgpath.".img";
	$classhedfile = $clsavgpath.".hed";
}
if ($modeldata['REF|ApClusteringStackData|clusterclass']) {
	$clsavgparams = $particle->getClusteringStackParamsFrom3d0($imagic3d0Id);
	$clsavgpath = $clsavgparams['path'];
	$strippedfile = ereg_replace(".hed", "", $clsavgparams['avg_imagicfile']);
	$classimgfile = $clsavgpath."/".$strippedfile.".img";
	$classhedfile = $clsavgpath."/".$strippedfile.".hed";	
}

$html.= "<td colspan='11'><b> 3 Initial Projections Used in Angular Reconstitution </b></td>
		 </tr><TR>";
foreach ($projections as $key => $projection) {
	$num = $key + 1;
	$image = $projection - 1; // Imagic numbering system starts with 1 instead of 0
	$html.= "<TD colspan='1' align='center' valign='top'>";
	$html.= "<img src='getstackimg.php?hed=$classhedfile
		&img=$classimgfile&n=".$image."&t=80&b=1&uh=0'><br/>\n";
	$html.= "<i>projection $num</i></TD>\n";
}
$html.="</tr></table>";

// display model info
$html.= "<br>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html.= "<TR><TD colspan='6' bgcolor='#bbffbb'>";
// view class averages used for 3d0 in summary page (both norefs and reclassifications)
$html.= "<a href='viewstack.php?file=$classimgfile&expId=$expId&reclassId=$reclassnum'>";
$html.= "class averages used to create 3d0 ---- <b>model ID: $modeldata[DEF_id]</b></a>";
$html.= "</TD></tr>";
// view model parameters
$html.="<TR><td>";
$html.="<TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html.="<tr><td>euler ang increment</td><td><b>$modeldata[euler_ang_inc]</b></td>
	    <td>num cls avgs used</td><td><b>$modeldata[num_classums]</b></td>
	    <td>symmetry</td><td><b>$modeldata[symmetry]</b></td></tr>
	<tr><td>hamming window</td><td><b>$modeldata[ham_win]</b></td>
	    <td>object size</td><td><b>$modeldata[obj_size]</b></td>
	    <td>reproj alignments</td><td><b>$modeldata[repalignments]</b></td></tr>
	<tr><td>automask dimension</td><td><b>$modeldata[amask_dim]</b></td>
	    <td>automask low-pass</td><td><b>$modeldata[amask_lp]</b></td>
	    <td>automask sharpness</td><td><b>$modeldata[amask_sharp]</b></td></tr>
	<tr><td>automask threshold</td><td><b>$modeldata[amask_thresh]</b></td>
	    <td>mrarefs ang incr</td><td><b>$modeldata[mra_ang_inc]</b></td>
	    <td>forw proj ang incr</td><td><b>$modeldata[forw_ang_inc]</b></td></tr>";
$html.="</table>";
$html.="</TD>";

// get list of png files in initial model (3d0) directory
$pngfiles = array();
$modeldir = opendir($modeldata['path']."/".$modeldata['runname']);
while ($f = readdir($modeldir)) {
	if (eregi($modeldata['name'].'.*\.png$',$f)) $pngfiles[] = $f;
}
sort($pngfiles);
		
// display starting models

$html.= "<TD width='550'>\n";	
foreach ($pngfiles as $snapshot) {
	$snapfile = $modeldata['path'].'/'.$modeldata['runname'].'/'.$snapshot;
	$html.= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>
		<img src='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
}
$html.="</TD>";
$html.= "</tr></table><br><br>";




#######################  REFINEMENT ITERATIONS  ############################


$html .= "<br>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html .= "<TR>\n";
$display_keys = array ( 'iter', 'parameters', 'snapshots');
$numcols = count($display_keys);
foreach($display_keys as $key) {
        $html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
}
$html .= "</tr>\n";

$html.= "<h4> Refinement Iterations </h4>";
foreach ($refineparams as $iteration) {
	$html.="<TR>
		<td>$iteration[iteration]</TD>";
	$html.="<td>";
	$html.="<TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html.="<tr><td>euler ang increment</td><td><b>$iteration[euler_ang_inc]</b></td>
		    <td>num cls avgs used</td><td><b>$iteration[num_classums]</b></td>
		    <td>symmetry</td><td><b>$iteration[symmetry]</b></td></tr>
		<tr><td>sampling param (MRA)</td><td><b>$iteration[sampling_parameter]</b></td>
		    <td>max shift orig (MRA)</td><td><b>$iteration[max_shift_orig]</b></td>
		    <td>max shift this (MRA)</td><td><b>$iteration[max_shift_this]</b></td></tr>
		<tr><td>hamming window</td><td><b>$iteration[ham_win]</b></td>
		    <td>object size</td><td><b>$iteration[obj_size]</b></td>
		    <td>reproj alignments</td><td><b>$iteration[repalignments]</b></td></tr>
		<tr><td>automask dimension</td><td><b>$iteration[amask_dim]</b></td>
		    <td>automask low-pass</td><td><b>$iteration[amask_lp]</b></td>
		    <td>automask sharpness</td><td><b>$iteration[amask_sharp]</b></td></tr>
		<tr><td>automask threshold</td><td><b>$iteration[amask_thresh]</b></td>
		    <td>mrarefs ang incr</td><td><b>$iteration[mra_ang_inc]</b></td>
		    <td>forw proj ang incr</td><td><b>$iteration[forw_ang_inc]</b></td></tr>";
	$html.="</table>";

	// get list of png files in directory
	$pngfiles = array();
	$modeldir = opendir($iteration['path']."/".$iteration['runname']);
	while ($f = readdir($modeldir)) {
		if (eregi($iteration['name'].'.*\.png$',$f)) $pngfiles[] = $f;

	}
	sort($pngfiles);

	// display all .png files in model directory
	$html.= "<TD width='600'>";
	foreach ($pngfiles as $snapshot) {
		$snapfile = $iteration['path'].'/'.$iteration['runname'].'/'.$snapshot;
		$html.= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>
			<img src='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
	}
	$html.="</TD>";

}

echo $html;

processing_footer();
?>
