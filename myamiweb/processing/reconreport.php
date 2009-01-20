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
  
// check if reconstruction is specified
if (!$reconId = $_GET['reconId'])
	$reconId=false;
$expId = $_GET['expId'];

$formAction = $_SERVER['PHP_SELF']."?expId=$expId&reconId=$reconId";

$refine_params_fields = array('refinerun', 'ang', 'mask', 'imask', 'pad', 'hard', 'classkeep', 'classiter', 'median', 'phasecls', 'refine','cckeep','minptls');
$javascript="<script src='../js/viewer.js'></script>\n";

// javascript to display the refinement parameters
$javascript="<script LANGUAGE='JavaScript'>
        function infopopup(";
foreach ($refine_params_fields as $param) {
        if (ereg("\|", $param)) {
	        $namesplit=explode("|", $param);
		$param=end($namesplit);
	}
	$refinestring.="$param,";
}
$refinestring=rtrim($refinestring,',');
$javascript.=$refinestring;
$javascript.=") {
                var newwindow=window.open('','name','height=400, width=200, resizable=1, scrollbar=1');
                newwindow.document.write(\"<HTML><HEAD><link rel='stylesheet' type='text/css' href='css/viewer.css'>\");
                newwindow.document.write('<TITLE>Ace Parameters</TITLE>');
                newwindow.document.write(\"</HEAD><BODY><TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>\");\n";
foreach($refine_params_fields as $param) {
	if (ereg("\|", $param)) {
		$namesplit=explode("|", $param);
		$param=end($namesplit);
	}
	$javascript.="                if ($param) {\n";
	$javascript.="                        newwindow.document.write('<TR><TD>$param</TD>');\n";
	$javascript.="                        newwindow.document.write('<TD>'+$param+'</TD></TR>');\n";
	$javascript.="                }\n";
}
$javascript.="                newwindow.document.write('</TABLE></BODY></HTML>');\n";
$javascript.="                newwindow.document.close()\n";
$javascript.="        }\n";
$javascript.="</script>\n";

$javascript.=eulerImgJava(); 

processing_header("Reconstruction Report","Reconstruction Report Page", $javascript);
if (!$reconId) {
	processing_footer();
	exit;
}

// --- Get Reconstruction Data
$particle = new particledata();
$stackId = $particle->getStackIdFromReconId($reconId);
$stackparams = $particle->getStackParams($stackId);
// get pixel size
$apix=($particle->getStackPixelSizeFromStackId($stackId))*1e10;
// don't think we need to calculate the binned pixel size
//$apix=($stackparams['bin']) ? $apix*$stackparams['bin'] : $apix;
$boxsz=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];

$html .= "<form name='iterations' method='post' action='$formAction'>\n";
$html .= "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html .= "<TR>\n";
$display_keys = array ( 'iter', 'ang', 'fsc', 'classes', '# particles', 'density','snapshot');
$numcols = count($display_keys);
foreach($display_keys as $key) {
        $html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
}
$html .= "</TR>\n";

$refinerun=$particle->getRefinementRunInfo($reconId);
$initmodel=$particle->getInitModelInfo($refinerun['REF|ApInitialModelData|initialModel']);

$stackfile=$stackparams['path']."/".$stackparams['name'];
$res = $particle->getHighestResForRecon($refinerun['DEF_id']);
$avgmedjump = $particle->getAverageMedianJump($refinerun['DEF_id']);
if ($avgmedjump['count'] > 0) {
	$avgmedjumpstr .= "<A HREF='eulergraph.php?expId=$expId&hg=1&recon=$refinerun[DEF_id]'>";
	$avgmedjumpstr .= sprintf("%2.2f &plusmn; %2.1f </A>", $avgmedjump['average'], $avgmedjump['stdev']);
} else
	$avgmedjumpstr = NULL;

$title = "recon info";
//print_r($refinerun);

$reconinfo = array(
	'id'=>"<A HREF='reconsummary.php?expId=$expId'>$refinerun[DEF_id]</A>",
	'name'=>$refinerun['name'],
	'description'=>$refinerun['description'],
	'path'=>$refinerun['path'],
	'refine package'=>$refinerun['package'],
	'best resolution'=>	sprintf("% 2.2f / % 2.2f &Aring; (%d)", $res[half],$res[rmeas],$res[iter]),
	'median euler jump'=>$avgmedjumpstr,
);

if ($refinerun['package']=='EMAN/SpiCoran') {
	$corankeepplotfile = $refinerun['path']."/corankeepplot-".$refinerun['DEF_id'].".png";
	if (file_exists($corankeepplotfile)) {
		echo "<TABLE><TR><TD>\n";
		$particle->displayParameters($title,$reconinfo,array(),$expId);
		echo "</TD><TD>";
		echo "<A HREF='loadimg.php?filename=$corankeepplotfile' target='corankeepplotfile'>"
			."<IMG SRC='loadimg.php?filename=$corankeepplotfile&s=180' HEIGHT='180'><BR/>\nCoran Keep Plot</A>";
		echo "</TD></TR></TABLE>";
	} else {
		$particle->displayParameters($title,$reconinfo,array(),$expId);
	}
} else {
	$particle->displayParameters($title,$reconinfo,array(),$expId);
}

// use summarytables.inc
echo ministacksummarytable($stackId);

$initmodelname = showModelInfo($initmodel, $expId, $particle);

$misc = $particle->getMiscInfoFromReconId($reconId);
if ($misc) echo "<A HREF='viewmisc.php?reconId=$reconId'>[Related Images, Movies, etc]</A><BR>\n"; 

$iterations = $particle->getIterationInfo($reconId);

# get starting model png files
$initpngs = array();
$initdir = opendir($initmodel['path']);

while ($f = readdir($initdir)){
	if (eregi($initmodelname.'.*\.png$',$f)) {
		$initpngs[] = $f;
	}
}
sort($initpngs);

# get list of png files in directory
$pngimages = getPngList($refinerun['path']);

# display starting model
$html .= "<TR>\n";
foreach ($display_keys as $p) {
	$html .= "<TD>";
	if ($p == 'iteration') $html .= "0";
	elseif ($p == 'snapshot') {
		foreach ($initpngs as $snapshot) {
			$snapfile = $initmodel['path'].'/'.$snapshot;
			$html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>"
				."<IMG SRC='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'></A>\n";
		}
	}
	$html .= "</TD>";
}
$html .= "</TR>\n";

# show info for each iteration
//sort($iterations);

foreach ($iterations as $iteration){
	$refinementData=$particle->getRefinementData($refinerun['DEF_id'], $iteration['iteration']);
	// set as exemplar if submitted
	if ($_POST['exemplar'.$refinementData['DEF_id']]) {
		$particle->updateExemplar('ApRefinementData',$refinementData['DEF_id'],1);
		$refinementData['exemplar'] = 1;
	}
	elseif ($_POST['notExemplar'.$refinementData['DEF_id']]) {
		$particle->updateExemplar('ApRefinementData',$refinementData['DEF_id'],0);
		$refinementData['exemplar'] = False;
	}

	// set background color of line based on exemplar
	$bg = ($refinementData['exemplar']) ? "#EEEEEE" : "#FFFFFF";

	$numclasses=$particle->getNumClasses($refinementData['DEF_id']);
	$res = $particle->getResolutionInfo($iteration['REF|ApResolutionData|resolution']);
	$RMeasure = $particle->getRMeasureInfo($iteration['REF|ApRMeasureData|rMeasure']);
	$fscid = ($res) ? $refinementData['DEF_id'] : False;
	$fscfile = ($res) ? $refinerun['path'].'/'.$res['fscfile'] : "None" ;
	$halfres = ($res) ? sprintf("%.2f",$res['half']) : "None" ;
	$rmeasureres = ($RMeasure) ? sprintf("%.2f",$RMeasure['rMeasure']) : "None" ;
	$badprtls = array();
	$goodprtls = array();
	$clsavgs = array();
	$refinetypes = array('EMAN','SpiCoran','MsgP');
	foreach ($refinetypes as $type) {
		switch ($type) {
			case 'EMAN':
				$clsavgfield = 'emanClassAvg';
				break;
			case 'SpiCoran':
				$clsavgfield = 'SpiCoranGoodClassAvg';
			  break; 	 
			case 'MsgP':
				$clsavgfield = 'MsgPGoodClassAvg';
			  break;
		}
		if ($refinementData[$clsavgfield]) {
			$clsavgs[$type] = $refinementData[$clsavgfield]; 
			$badprtls[$type]=$particle->getSubsetParticlesInStack($refinementData['DEF_id'], 'bad', $type, True);
			$goodprtls[$type]=$particle->getSubsetParticlesInStack($refinementData['DEF_id'], 'good', $type, True);
		}
	}
	# old data has no class average distinction, only eman bad particles
	if ((count($badprtls)==0) || ($refinerun['package']=='EMAN/MsgP' && (!array_key_exists('EMAN',$badprtls)))) 
		$badprtls['EMAN']=$particle->getSubsetParticlesInStack($refinementData['DEF_id'], 'bad', 'EMAN', True);
		$goodprtls['EMAN']=$particle->getSubsetParticlesInStack($refinementData['DEF_id'], 'good', 'EMAN', True);
	# old data has no class average distinction, force association 
	if ((count($clsavgs)==0 && ($refinerun['package'] == 'EMAN')) || ($refinerun['package']=='EMAN/MsgP' && (!array_key_exists('EMAN',$clsavgs)))) { 
		$clsavgs['EMAN']= $refinementData['classAverage'];
	} elseif (count($clsavgs)==0 && $refinerun['package']=='EMAN/SpiCoran') {
		$classnamearray = explode('.',$refinementData['classAverage']);
		$newnamearray = array_slice($classnamearray,0,count($classnamearray)-1);
		array_push($newnamearray,'old',$classnamearray[count($classnamearray)-1]);
		$clsavgs['EMAN'] = implode('.',$newnamearray);
		$clsavgs['SpiCoran']= $refinementData['classAverage'];
	}
	$html .= "<tr>\n";
	$html .= "<td bgcolor='$bg'>\n";

/*
  $html .= "<TD><A HREF=\"javascript:infopopup(";
  $refinestr2='';
  foreach ($refine_params_fields as $param) {
    if (eregi('hard|class|median|phasecls|refine',$param)){$param="EMAN_$param";}
    if (eregi('cckeep|minptls',$param)){$param="MsgP_$param";}
		$refinestr2.="'$iteration[$param]',";
  }
  $refinestr2=rtrim($refinestr2,',');
  $html .=$refinestr2;
*/ 
	$html .="<a class='aptitle' href='iterationreport.php?expId=$expId&rId=".$reconId."&itr=".$iteration['iteration']."'\n";
	$html .=")\">$iteration[iteration]</A></TD>\n";
	$html .= "<TD bgcolor='$bg'>$iteration[ang]&deg;</TD>\n";
	if ($halfres!='None' && $fscid)
		$html .= "<td bgcolor='$bg'><a href='fscplot.php?expId=$expId&fscid=$fscid&width=800&height=600&apix=$apix&box=$boxsz' target='snapshot'><img src='fscplot.php?expId=$expId&fscid=$fscid&width=100&height=80&nomargin=TRUE'></a><br />\n";
	elseif ($halfres!='None' && $fscfile) 
		$html .= "<td bgcolor='$bg'><a href='fscplot.php?expId=$expId&fscfile=$fscfile&width=800&height=600&apix=$apix&box=$boxsz' target='snapshot'><img src='fscplot.php?expId=$expId&fscfile=$fscfile&width=100&height=80&nomargin=TRUE'></a><br />\n";
	else $html .= "<td bgcolor='$bg'>\n";
	$html .= "<I>FSC 0.5:</I><br />$halfres<br />\n";
  
	if ($rmeasureres!='None')
		$html .= "<I>Rmeas:</I><br>$rmeasureres\n";
	$html .= "</TD>";
  
	$html .="<td bgcolor='$bg'><table>";
	$html .= "<TR><td bgcolor='$bg'>";
	$html .= "$numclasses classes<br />\n";
	foreach ($refinetypes as $type) {
		if (array_key_exists($type,$clsavgs)) {
			$clsavgfile = $refinerun['path'].'/'.$clsavgs[$type];
			$html .= "<a target='stackview' href='viewstack.php?file=$clsavgfile'>".$clsavgs[$type]."</a><br />";
		}
	}

	//Euler plots
	$firsteulerimg='';
	$eulerSelect = "<select name='eulerplot".$iteration['iteration']."' onChange='switchEulerImg(".$iteration['iteration'].",this.options(this.selectedIndex).value)'>\n";
	foreach ($pngimages['eulerfiles'] as $eulername) {
		if (eregi($reconId."_".$iteration['iteration']."\.png$", $eulername)) {
			$eulerfile = $refinerun['path'].'/'.$eulername;
			$opname = ereg_replace("euler","",$eulername);
			$opname = ereg_replace("-".$reconId."_".$iteration['iteration']."\.png$","",$opname);
			if (file_exists($eulerfile)) {
				$eulerSelect.= "<option value='$eulerfile'>$opname</option>\n";
				// set the first image as the default
				if (!$firsteulerimg) $firsteulerimg = $eulerfile;
			}
		}
	}
	$eulerSelect .= "</select>\n";
	
	$eulerhtml = "<a id='eulerlink".$iteration['iteration']
		."' href='loadimg.php?filename=".$firsteulerimg."' target='snapshot'>"
		."<img name='eulerimg".$iteration['iteration']."' src='loadimg.php?scale=.125&filename=".$firsteulerimg."'>"
		."</a><br />\n";
	$eulerhtml .= $eulerSelect;
	// add euler plots to iteration if exist
	if ($firsteulerimg) $html .=$eulerhtml;

	$html .= "</td></tr>\n";
	$html .= "</table></td>\n";
  
	//particle stack viewing 
	$html .="<td bgcolor='$bg'><table>";
	foreach ($refinetypes as $type) {
		if (array_key_exists($type,$badprtls)) {
			$prtlsused=$stackparticles-$badprtls[$type];
			$html .= "<TR><td bgcolor='$bg'>\n"
			."$type </TD></TR>\n";
			if ($prtlsused != $goodprtls[$type]) 
				$html .= "<TR><td bgcolor='$bg'>Not all prtls accounted for!!!</TD></TR>";
			$html .= "<TR><td bgcolor='$bg'>\n"
			."<a target='stackview' HREF='viewstack.php?refinement=$refinementData[DEF_id]&substack=good&refinetype=$type'>[$goodprtls[$type]-good]</A><BR/></TD></TR><TR><td bgcolor='$bg'>"
			."<a target='stackview' HREF='viewstack.php?refinement=$refinementData[DEF_id]&substack=bad&refinetype=$type'>[$badprtls[$type]-bad]</A></TD></TR>\n";
		}
	}	
	$html .= "</table></TD>";
  
	// postproc/makegoodaverages
	$html .= "<td bgcolor='$bg'>$iteration[volumeDensity]<br />\n";
	$html .= "<A HREF='postproc.php?expId=$expId&refinement=$refinementData[DEF_id]'><FONT CLASS='sf'>[post processing]</FONT></a><br />\n";
	$html .= "<A HREF='makegoodavg.php?expId=$expId&refId=$refinementData[DEF_id]&reconId=$reconId&iter=$iteration[iteration]'><FONT CLASS='sf'>[new averages]</FONT></a><br />\n";
	if ($refinementData['exemplar']) $html .= "<input class='edit' type='submit' name='notExemplar".$refinementData['DEF_id']."' value='not exemplar'>";
	else $html .= "<input class='edit' type='submit' name='exemplar".$refinementData['DEF_id']."' value='exemplar'>";
	$html .= "</td>\n";

	// snapshot images
	$html .= "<td bgcolor='$bg'>\n";
	foreach ($pngimages['pngfiles'] as $snapshot) {
		if (eregi($iteration['volumeDensity'],$snapshot)) {
			$snapfile = $refinerun['path'].'/'.$snapshot;
			$html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>"
				."<IMG SRC='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'></a>\n";
		}
	}
	"</td></tr>\n";
	// check for post procs
	$postprocs = $particle->getPostProcsFromRefId($refinementData['DEF_id']);
	if ($postprocs[0]) {
		$html .= "<tr>\n";
		foreach ($postprocs as $p) {
			# get list of png files in directory
	  		$procimgs = getPngList($p['path']);
			$html .= "<td bgcolor='$bg' colspan='".($numcols-1)."'>\n";
			$html .= "<b>Post Processing of ".$iteration['volumeDensity']."</b>\n";
			if ($p['handflip']) $html .= "(handedness flipped)\n";
			$html .= "<table border='0' cellpadding='0' cellspacing='0'>\n";
			$html .= "<tr><td><b>path: </b></td><td>".$p['path']."</td></td>\n";
			$html .= "<tr><td><b>name: </b></td><td>".$p['name']."</td></td>\n";
			if ($p['ampName']) $html .= "<tr><td><b>ampcor file: </b></td><td>".$p['amppath']."/".$p['ampName']."</td></tr>\n";
			if ($p['lowpass']) $html .= "<tr><td><b>low pass filter: </b></td><td>".$p['lowpass']." angstroms</td></tr>\n";
			if ($p['highpass']) $html .= "<tr><td><b>high pass filter: </b></td><td>".$p['highpass']." angstroms</td></tr>\n";
			if ($p['mask']) {
			  	// convert to pixels
			  	$boxang = $p['mask']*$apix;
			  	$html .= "<tr><td><b>Mask: </b></td><td>$boxang Angstroms (".$p['mask']." pixels)</td></tr>\n";
			}
			if ($p['imask']) {
			  	// convert to pixels
			  	$boxang = $p['imask']*$apix;
				$boxang = sprintf("%.1f",$boxang);
			  	$html .= "<tr><td><b>Inner Mask: </b></td><td>$boxang Angstroms (".$p['imask']." pixels)</td></tr>\n";
			}
			$html .= "</table>\n";
			$html .= "</td><td>\n";
			foreach ($procimgs['pngfiles'] as $s) {
			  	if (eregi($p['name'],$s)) {
					$sfile = $p['path'].'/'.$s;
					$html .= "<a href='loadimg.php?filename=$sfile' target='snapshot'>"
						."<img src='loadimg.php?s=80&filename=$sfile' height='80'></a>\n";
				}
			}
			$html .= "</td>\n";
			$html .= "</tr>\n";
		}
	}	  
}
$html .= "</form>\n";
$html.="</TABLE>\n";

echo "<P><FORM NAME='compareparticles' METHOD='POST' ACTION='compare_eulers.php'>
Compare Iterations:
<select name='comp_param'>\n";
echo "<option>Eulers</option>\n";
echo "<option>Inplane rotation</option>\n";
echo "<option>Shifts</option>\n";
echo "<option>Quality Factor</option>\n";
echo "</select>\n";
echo "Iteration 1: <select name='iter1'>\n";
foreach ($iterations as $iteration){
        echo "<option>$iteration[iteration]</option>\n";
}
echo "</select>\n";
echo "Iteration 2: <select name='iter2'>\n";
foreach ($iterations as $iteration){
        echo "<option>$iteration[iteration]</option>\n";
}
echo "</select>\n";
echo "<br />";
echo "download: <input type='checkbox' name='dwd' >\n";
echo "<input type='submit' name='compare' value='compare'>\n";
echo "<input type='hidden' name='reconId' value='$reconId'>\n";
echo "</FORM>\n";

$comm_param = ($_POST[comm_param]) ? $_POST[comm_param] : 'bad';
$iter1 = ($_POST[iter1]) ? $_POST[iter1] : $iterations[0][iteration];
$iter2 = ($_POST[iter2]) ? $_POST[iter2] : $iterations[0][iteration];
$formaction =  'viewstack.php?recon='.$reconId.'&substack='.$comm_param.'&itr1='.$iter1.'&itr2='.$iter2;
echo "<P><FORM NAME='commonparticles' target='stackview' METHOD='POST' ACTION=$formaction>
Show Common Particles Between Iterations:";
echo "
	<select name='comm_param'>\n";
$comm_params = array('bad'=>'Bad by EMAN refine',
	'good'=>'Good by EMAN refine');
if ($refinerun['package']=='EMAN/MsgP') { 
		$comm_params_msgp = array('msgpbad'=>'Bad by Msg Passing');
		$comm_params = array_merge($comm_params,$comm_params_msgp);
}
foreach (array_keys($comm_params) as $key) {
	$s = ($comm_param==$key) ? 'selected' : '';
	echo "<option value=$key $s>$comm_params[$key]</option>\n";
}
echo "</select>\n";
echo "From Iteration: <select name='iter1'>\n";
foreach ($iterations as $iteration){
	$s = ($iter1==$iteration[iteration]) ? 'selected' : '';
	echo "<option $s>$iteration[iteration]</option>\n";
}
echo "</select>\n";
echo "To: <select name='iter2'>\n";
foreach ($iterations as $iteration){
	$s = ($iter2==$iteration[iteration]) ? 'selected' : '';
	echo "<option $s>$iteration[iteration]</option>\n";
}
echo "</select>\n";
echo "<input type='submit' name='common particles' value='Show Common Particles' >\n";
echo "<br />";
echo "</FORM>\n";

echo $html;

processing_footer();
?>
