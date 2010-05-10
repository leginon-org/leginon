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

showReport();

function getNumClassesFromFile ($imagicfile) {
	$hedfile = $imagicfile;
	if (substr($imagicfile, -4) == ".img")
		$hedfile = substr($imagicfile, 0, -4).".hed";
	if (!file_exists($hedfile)) {
		echo "MISSING HED FILE: $hedfile<br/>";
		return 0;
	}
	$size = filesize($hedfile);
	//echo "SIZE $size<br/>";
	$numclass = ceil($size/1024.0/2.0);
	return $numclass;
}


function showReport () {
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
		$javascript.="                        newwindow.document.write('<TR><td>$param</TD>');\n";
		$javascript.="                        newwindow.document.write('<td>'+$param+'</TD></tr>');\n";
		$javascript.="                }\n";
	}
	$javascript.="                newwindow.document.write('</table></BODY></HTML>');\n";
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
	$stackparticles= $particle->getNumStackParticles($stackId);

	$html .= "<form name='iterations' method='post' action='$formAction'>\n";
	$html .= "<br>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'iter', 'ang', 'fsc', 'classes', '# particles', 'density','snapshot');
	$numcols = count($display_keys);
	foreach($display_keys as $key) {
	        $html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	$html .= "</tr>\n";

	$refinerun=$particle->getRefinementRunInfo($reconId);
	$initmodel=$particle->getInitModelInfo($refinerun['REF|ApInitialModelData|initialModel']);

	$stackfile=$stackparams['path']."/".$stackparams['name'];
	$res = $particle->getHighestResForRecon($refinerun['DEF_id']);
	$avgmedjump = $particle->getAverageMedianJump($refinerun['DEF_id']);
	if ($avgmedjump['count'] > 0) {
		$avgmedjumpstr .= "<A HREF='eulergraph.php?expId=$expId&hg=1&recon=$refinerun[DEF_id]' starget='snapshot'>";
		$avgmedjumpstr .= sprintf("%2.2f &plusmn; %2.1f </A>", $avgmedjump['average'], $avgmedjump['stdev']);
		$avgmedjumpstr .= "&nbsp;&nbsp;<font size=-2><A HREF='jumpSubStack.php?expId=$expId&reconId=$refinerun[DEF_id]'>[make substack]</a></font>";
	} else
		$avgmedjumpstr = NULL;

	$title = "recon info";
	//print_r($refinerun);

	$reconinfo = array(
		'id'=>"<A HREF='reconsummary.php?expId=$expId'>$refinerun[DEF_id]</A>",
		'name'=>$refinerun['runname'],
		'description'=>$refinerun['description'],
		'path'=>$refinerun['path'],
		'refine package'=>$refinerun['package'],
		'best resolution'=>	sprintf("% 2.2f / % 2.2f &Aring; (%d)", $res[half],$res[rmeas],$res[iter]),
		'median euler jump'=>$avgmedjumpstr,
	);

	if ($refinerun['package']=='EMAN/SpiCoran') {
		$corankeepplotfile = $refinerun['path']."/corankeepplot-".$refinerun['DEF_id'].".png";
		if (file_exists($corankeepplotfile)) {
			echo "<table><TR><td>\n";
			$particle->displayParameters($title,$reconinfo,array(),$expId);
			echo "</TD><td>";
			echo "<A HREF='loadimg.php?filename=$corankeepplotfile' target='snapshot'>"
				."<img src='loadimg.php?filename=$corankeepplotfile&s=180' HEIGHT='180'><br>\nCoran Keep Plot</A>";
			echo "</TD></tr></table>";
		} else {
			$particle->displayParameters($title,$reconinfo,array(),$expId);
		}
	} else {
		$particle->displayParameters($title,$reconinfo,array(),$expId);
	}

	// use summarytables.inc
	echo ministacksummarytable($stackId);
	$mpix = $particle->getStackPixelSizeFromStackId($stackId);

	echo modelsummarytable($initmodel['DEF_id']);

	$misc = $particle->getMiscInfoFromReconId($reconId);
	if ($misc) echo "<A HREF='viewmisc.php?reconId=$reconId'>[Related Images, Movies, etc]</A><br>\n"; 

	$iterations = $particle->getIterationInfo($reconId);

	# get starting model png files
	$initpngs = array();
	$initdir = opendir($initmodel['path']);

	$initpngs = glob($initdir."/".$initmodelname.'.*\.png');

	sort($initpngs);

	# get list of png files in directory
	$pngimages = getPngList($refinerun['path']);

	# display starting model
	$html .= "<TR>\n";
	foreach ($display_keys as $p) {
		$html .= "<td>";
		if ($p == 'iteration') $html .= "0";
		elseif ($p == 'snapshot') {
			foreach ($initpngs as $snapshot) {
				$snapfile = $snapshot;
				$html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>"
					."<img src='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'></A>\n";
			}
		}
		$html .= "</TD>";
	}
	$html .= "</tr>\n";

	//************************
	//************************
	// show info for each iteration
	foreach ($iterations as $iteration){

		//************************
		// Get iteration info
		$iternum = $iteration['iteration'];
		$ref=$particle->getRefinementData($refinerun['DEF_id'], $iternum);
		$refineIterData=$ref[0];
		$refineIterId = $refineIterData['DEF_id'];


		//************************
		// Set as exemplar if submitted
		if ($_POST['exemplar'.$refineIterId]) {
			$particle->updateExemplar('ApRefineIterData',$refineIterId, 1);
			$refineIterData['exemplar'] = true;
		}
		elseif ($_POST['notExemplar'.$refineIterId]) {
			$particle->updateExemplar('ApRefineIterData',$refineIterId, 0);
			$refineIterData['exemplar'] = false;
		}

		//************************
		// Set background color of line based on exemplar
		$bg = ($refineIterData['exemplar']) ? "#EEEEEE" : "#FFFFFF";
		$html .= "<tr>\n";

		//************************
		// Link to recon params
		$html .= "<td bgcolor='$bg'>\n";
		$html .="<a class='aptitle' href='iterationreport.php?expId=$expId&rId=".$reconId."&itr=".$iternum."'\n";
		$html .=")\">$iternum</A></TD>\n";

		//************************
		// Show ang increment
		$html .= "<TD bgcolor='$bg'>$iteration[ang]&deg;</TD>\n";

		//************************
		// Resolution fields
		$res = $particle->getResolutionInfo($iteration['REF|ApResolutionData|resolution']);
		$RMeasure = $particle->getRMeasureInfo($iteration['REF|ApRMeasureData|rMeasure']);
		$fscid = ($res) ? $refineIterId : False;
		$fscfile = ($res) ? $refinerun['path'].'/'.$res['fscfile'] : "None" ;
		$halfres = ($res) ? sprintf("%.2f",$res['half']) : "None" ;
		$rmeasureres = ($RMeasure) ? sprintf("%.2f",$RMeasure['rMeasure']) : "None" ;
		if ($halfres!='None' && $fscid) {
			$html .= "<td bgcolor='$bg'><a href='fscplot.php?expId=$expId&fscid=$fscid&width=800&height=600&apix=$apix&box=$boxsz'"
				." target='snapshot'><img src='fscplot.php?expId=$expId&fscid=$fscid&width=100&height=80&nomargin=TRUE'></a><br />\n";
		} elseif ($halfres!='None' && $fscfile) {
			$html .= "<td bgcolor='$bg'><a href='fscplot.php?expId=$expId&fscfile=$fscfile&width=800&height=600&apix=$apix&box=$boxsz'"
				." target='snapshot'><img src='fscplot.php?expId=$expId&fscfile=$fscfile&width=100&height=80&nomargin=TRUE'></a><br />\n";
		} else {
			$html .= "<td bgcolor='$bg'>\n";
		}
		$html .= "<I>FSC&frac12;:</I><br />$halfres &Aring;<br />\n";
		if ($rmeasureres!='None') {
			$html .= "<I>Rmeas:</I><br>$rmeasureres &Aring;\n";
		}
		$html .= "</TD>";

		//************************
		// Class averages, Euler plots
		$html .="<td bgcolor='$bg'><table>";
		$html .= "<TR><td bgcolor='$bg'>";

		$refineClassAverages = $refinerun['path'].'/'.$refineIterData['refineClassAverages'];
		$html .= "<a target='stackview' href='viewstack.php?file="
			.$refineClassAverages.'&ps='.$mpix."'>".$refineIterData['refineClassAverages']."</a><br>";

		if ($refineIterData['postRefineClassAverages']) {
			$postRefineClassAverages = $refinerun['path'].'/'.$refineIterData['postRefineClassAverages'];
			$html .= "<a target='stackview' href='viewstack.php?file="
				.$postRefineClassAverages.'&ps='.$mpix."'>".$refineIterData['postRefineClassAverages']."</a><br>";
		}

		$numclasses = getNumClassesFromFile($refineClassAverages);
		$html .= "$numclasses classes<br />\n";

		//Euler plots
		$firsteulerimg='';
		$eulerSelect = "<select name='eulerplot$iternum' onChange='switchEulerImg($iternum, this.options(this.selectedIndex).value)'>\n";
		$eulerPngFiles = glob($refinerun['path']."/euler*_$iternum.png");
		foreach ($eulerPngFiles as $eulername) {
			if (eregi($reconId."_".$iternum."\.png$", $eulername)) {
				$eulerfile = $eulername;
				$opname = ereg_replace("euler","",basename($eulername));
				$opname = ereg_replace("-.*$","",$opname);
				if (file_exists($eulerfile)) {
					$eulerSelect.= "<option value='$eulerfile'>$opname</option>\n";
					// set the first image as the default
					if (!$firsteulerimg) $firsteulerimg = $eulerfile;
				}
			}
		}
		$eulerSelect .= "</select>\n";
		
		$eulerhtml = "<a id='eulerlink".$iternum
			."' href='loadimg.php?filename=".$firsteulerimg."' target='snapshot'>"
			."<img name='eulerimg".$iternum."' width='64' height='64' src='loadimg.php?w=64&filename=".$firsteulerimg."'>"
			."</a><br />\n";
		$eulerhtml .= $eulerSelect;
		// add euler plots to iteration if exist
		if ($firsteulerimg) $html .=$eulerhtml;

		$html .= "</td></tr>\n";
		$html .= "</table></td>\n";

		//************************
		// Refine type, # particles
		$html .= "<td bgcolor='$bg'><table>";
		$partcounts = $particle->getRefineParticleCounts($refineIterId);
		$numbad = $partcounts['bad_refine'];
		$numgood = $partcounts['good_refine'];

		if ($numbad + $numgood != $stackparticles) 
				$html .= "<tr><td bgcolor='$bg'><font size='-1' color='#dd3333'><b>Particles are missing!!!</b></font></td></tr>";


		$html .= "<tr><td bgcolor='$bg'>Normal Refine</td></tr>\n";
		$html .= "<tr><td bgcolor='$bg'>\n";
			$html .= "<a target='stackview' "
				."href='viewstack.php?expId=$expId&refineIter=$refineIterId&substack=good&refinetype=refine'>"
				."[$numgood&nbsp;good]</a><br/>";
		$html .= "</td></tr><tr><td bgcolor='$bg'>";
			$html .= "<a target='stackview' "
				."href='viewstack.php?expId=$expId&refineIter=$refineIterId&substack=bad&refinetype=refine'>"
				."[$numbad&nbsp;bad]</a><br/>";
		$html .= "</td></tr>";

		if ($refineIterData['postRefineClassAverages']) {
			$numpostbad = $partcounts['bad_postRefine'];
			$numpostgood = $partcounts['good_postRefine'];
			$html .= "<tr><td bgcolor='$bg'>Post-Refine</td></tr>\n";
			$html .= "<tr><td bgcolor='$bg'>\n";
				$html .= "<a target='stackview' "
					."href='viewstack.php?expId=$expId&refineIter=$refineIterId&substack=good&refinetype=postrefine'>"
					."[$numgood&nbsp;good]</a><br/>";
			$html .= "</td></tr><tr><td bgcolor='$bg'>";
				$html .= "<a target='stackview' "
					."href='viewstack.php?expId=$expId&refineIter=$refineIterId&substack=bad&refinetype=postrefine'>"
					."[$numbad&nbsp;bad]</a><br/>";
			$html .= "</td></tr>";
		}

		$html .= "</table></td>";

		//************************
		// Volume density
		// download link
		$html .= "<td bgcolor='$bg'>\n";

		$mrcfile = $refinerun['path']."/".$iteration['volumeDensity'];
		$html .= "<a href='download.php?file=$mrcfile'>\n";
		$html .= "  <img src='../img/dwd_bt_off.gif' border='0' width='15' height='15' alt='download mrc'>\n";
		$html .= "</a>\n";

		// name of density
		$html .= "$iteration[volumeDensity]<br/>\n";
		
		// buttons
		$html .= "<input class='edit' type='button' onClick=\"parent.location='postproc.php?expId=$expId&refinement=$refineIterId'\" value='Post Processing'><br />\n";
		$html .= "<input class='edit' type='button' onClick=\"parent.location='makegoodavg.php?expId=$expId&refId=$refineIterId&reconId=$reconId&iter=$iternum'\" value='Remove Jumpers'><br />\n";
		if ($refinerun['package']=='EMAN/SpiCoran') $html .= "<input class='edit' type='button' onClick=\"parent.location='coranSubStack.php?expId=$expId&refId=$refineIterId&reconId=$reconId&iter=$iternum'\" value='Coran Substack'><br />\n";
		if ($refineIterData['exemplar']) $html .= "<input class='edit' type='submit' name='notExemplar".$refineIterId."' value='not exemplar'>";
		else $html .= "<input class='edit' type='submit' name='exemplar".$refineIterId."' value='Make Exemplar'>";

		$html .= "</td>\n";

		// snapshot images
		$html .= "<td bgcolor='$bg'>\n";
		foreach ($pngimages['pngfiles'] as $snapshot) {
			if (eregi($iteration['volumeDensity'],$snapshot)) {
				$snapfile = $snapshot;
				$html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>"
					."<img src='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'></a>\n";
			}

		}

		"</td></tr>\n";
		// check for post procs
		$postprocs = $particle->getPostProcsFromRefId($refineIterId);
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
				  	$html .= "<tr><td><b>mask: </b></td><td>$boxang Angstroms (".$p['mask']." pixels)</td></tr>\n";
				}
				if ($p['imask']) {
				  	// convert to pixels
				  	$boxang = $p['imask']*$apix;
					$boxang = sprintf("%.1f",$boxang);
				  	$html .= "<tr><td><b>inner mask: </b></td><td>$boxang Angstroms (".$p['imask']." pixels)</td></tr>\n";
				}
				if ($p['maxjump']) $html .= "<tr><td><b>jumper cutoff: </b></td><td>".$p['maxjump']."&deg;</td></tr>\n";
				if ($p['sigma']) $html .= "<tr><td><b>sigma cutoff: </b></td><td>".$p['sigma']."</td></tr>\n";
				if ($p['resolution']) $html .= "<tr><td><b>FSC 0.5: </b></td><td>".sprintf("%.2f",$p['resolution'])."</td></tr>\n";
				if ($p['rmeasure']) $html .= "<tr><td><b>Rmeas 0.5: </b></td><td>".sprintf("%.2f",$p['rmeasure'])."</td></tr>\n";
				$html .= "</table>\n";
				$html .= "</td><td>\n";
				foreach ($procimgs['pngfiles'] as $s) {
				  	if (eregi($p['name'],$s)) {
						$sfile = $s;
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
	$html.="</table>\n";

	echo "<P><FORM NAME='compareparticles' METHOD='POST' ACTION='compare_eulers.php?expId=$expId'>
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
	$formaction =  'viewstack.php?expId='.$expId.'&recon='.$reconId.'&subtype='.$comm_param.'&refinetype='.$rtype;
	echo "<P><FORM NAME='showcommon' target='stackview' METHOD='POST' ACTION=$formaction>
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
};
?>
