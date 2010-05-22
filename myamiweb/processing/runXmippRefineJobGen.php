<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create a Xmipp Job for submission to a cluster
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['cluster']) {
	$selectedcluster=$_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

if ($_POST['write']) {
	// write job file
	$particle = new particledata();

	if (!$_POST['nodes']) jobForm("ERROR: No nodes specified, setting default=".C_NODES_DEF);
	if (!$_POST['ppn']) jobForm("ERROR: No processors per node specified, setting default=".C_PPN_DEF);
	if ($_POST['ppn'] > C_PPN_MAX ) jobForm("ERROR: Max processors per node is ".C_PPN_MAX);
	if ($_POST['nodes'] > C_NODES_MAX ) jobForm("ERROR: Max nodes on ".C_NAME." is ".C_NODES_MAX);
	if (!$_POST['walltime']) jobForm("ERROR: No walltime specified, setting default=".C_WALLTIME_DEF);
	if ($_POST['walltime'] > C_WALLTIME_MAX ) jobForm("ERROR: Max walltime is ".C_WALLTIME_MAX);
	if (!$_POST['cput']) jobForm("ERROR: No CPU time specified, setting default=".C_CPUTIME_DEF);
	if ($_POST['cput'] > C_CPUTIME_MAX) jobForm("ERROR: Max CPU time is ".C_CPUTIME_MAX);
	if (!$_POST['rprocs']) jobForm("ERROR: No reconstruction ppn specified, setting default=".C_RPROCS_DEF);
	if ($_POST['rprocs'] > $_POST['ppn'])
	  jobForm("ERROR: Asking to reconstruct on more processors than available");

	// check that job file doesn't already exist
	$outdir = formatEndPath($_POST['outdir']);
	$outdir .= $_POST['jobname'];

	// jobname ends with .job
	$jobname = $_POST['jobname'];
	$jobname .= '.job';
	$exists = $particle->getJobFileFromPath($outdir,$jobname);
	writeJobFile();
}

elseif ($_POST['submitstackmodel'] || $_POST['import']) {
	// create job form
	## make sure a stack and model were selected
	if (!$_POST['model']) stackModelForm("ERROR: no initial model selected");
	if (!$_POST['stackval']) stackModelForm("ERROR: no stack selected");

	jobForm();
}

elseif ($_POST['submitjob']) {
	// submit job
	$particle = new particledata();
	$clusterdata->post_data();

	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$host = $_POST['clustername'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	if (!($user && $pass)) writeJobFile("<B>ERROR:</B> Enter a user name and password");

	$jobname = $_POST['jobname'];
	$outdir = $_POST['outdir'].$jobname;

	$dmfpath=null;
	if (!empty($_POST['dmfpath'])) {
		$dmfpath=$_POST['dmfpath'].$jobname;
	}

	$clusterpath=$_POST['clusterpath'].$jobname;
	$jobfile="$jobname.job";
	$tmpjobfile = "/tmp/$jobfile";
	
	$jobid=$particle->insertClusterJobData($host,$outdir,$dmfpath,$clusterpath,$jobfile,$expId,'xmipprecon',$user);

	// add header & job id to the beginning of the script
	// convert /\n's back to \n for the script
	$header = explode('|--|',$_POST['header']);
	$clusterjob = "## $jobname\n";
	foreach ($header as $l) $clusterjob.="$l\n";

	$clusterjob.= C_APPION_BIN."updateAppionDB.py $jobid R $projectId\n\n";
	$clusterjob.= "# jobId: $jobid\n";
	$clusterjob.= "# projectId: $projectId\n";
	$clusterlastline.= C_APPION_BIN."updateAppionDB.py $jobid D $projectId\nexit\n\n";
	$f = file_get_contents($tmpjobfile);
	file_put_contents($tmpjobfile, $clusterjob . $f . $clusterlastline);

	processing_header("Xmipp Job Submitted","Xmipp Job Submitted",$javafunc);
	echo "<table width='600'>\n";

	// create appion directory & copy job file
	$cmd = "mkdir -p $outdir;\n";
	$cmd.= "cp $tmpjobfile $outdir/$jobfile;\n";
	exec_over_ssh($_SERVER['SERVER_ADDR'], $user, $pass, $cmd, True);

	$clusterdata->cluster_cmd($host, $user, $pass);
	// if on guppy, clusterpath is same as outdir
	$path = formatEndPath($clusterdata->get_path()).$jobname;

	echo "<tr><td>Appion Directory</td><td>$outdir</td></tr>\n";
	echo "<tr><td>Cluster Job File</td><td>$path.job</td></tr>\n";
	echo "<tr><td>Job File Name</td><td>$jobname.job</td></tr>\n";
  
	// submit job on host
	$cmd = "cd $path; qsub $jobfile;\n";
	
	$jobnumstr = exec_over_ssh($host, $user, $pass, $cmd, True);
  
	$jobnum = trim($jobnumstr);
	echo "<tr><td>Cluster Job Id</td><td>$jobnum</td></tr>\n";
	$jobnum = ereg_replace('\..*','',$jobnum);
	if (!is_numeric($jobnum)) {
		echo "</table><p>\n";
		echo "<hr>\n<font color='#CC3333' size='+1'>ERROR: job submission failed</font>\n";
		processing_footer();
		exit;
	}

	// insert cluster job id into row that was just created
	$particle->updateClusterQueue($jobid,$jobnum,'Q');

	echo "<tr><td>Cluster Directory</td><td>$clusterpath</td></tr>\n";
	echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
	echo "</table>\n";

	// check jobs that are running on the cluster
	echo "<P>Jobs currently running on the cluster:\n";
	$subjobs = checkClusterJobs($host,$user,$pass);
	if ($subjobs) {echo "<PRE>$subjobs</PRE>\n";}
	else {echo "<FONT COLOR='RED'>No Jobs on the cluster, check your settings</FONT>\n";}
	echo "<p><a href='checkRefineJobs.php?expId=$expId'>[Check Status of Jobs Associated with this Experiment]</a><p>\n";
	echo "<P><hr>\n<font color='#CC3333' size='+1'>Do not hit 'reload' - it will re-submit job</FONT><P>\n";

	processing_footer(True, True);
	exit;
}

else stackModelForm();

function stackModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	$javafunc="<script src='../js/viewer.js'></script>\n";
	processing_header("Eman Job Generator","EMAN Job Generator",$javafunc);

	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}

	$particle = new particledata();

	// get initial models associated with project
	$models = $particle->getModelsFromProject($projectId);

	// find each stack entry in database
	$stackIds = $particle->getStackIds($expId);
	$stackinfo = explode('|--|', $_POST['stackval']);
	$stackidval = $stackinfo[0];
	$apix = $stackinfo[1];
	$box = $stackinfo[2];

	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	echo"<b>Stack:</b><br>";
	$particle->getStackSelector($stackIds, $stackidval, '');

	// show initial models
	echo "<P><B>Model:</B><br><A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><br>\n";
	echo "<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'><br>\n";

	$minf = explode('|--|',$_POST['model']);
	if (is_array($models) && count($models)>0) {
		echo "<table class='tableborder' border='1'>\n";
		foreach ($models as $model) {
			echo "<tr><td>\n";
			$modelid = $model['DEF_id'];
			$symdata = $particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
			$modelvals = "$model[DEF_id]|--|$model[path]|--|$model[name]|--|$model[boxsize]|--|$symdata[symmetry]";
			echo "<input type='radio' NAME='model' value='$modelvals' ";
			// check if model was selected
			if ($modelid == $minf[0]) echo " CHECKED";
			echo ">\n";
			echo"Use<br/>Model\n";

			echo "</td><td>\n";

			echo modelsummarytable($modelid, true);

			echo "</td></tr>\n";
		}
		echo "</table>\n\n";
		echo "<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'></FORM>\n";
	}
	else echo "No initial models in database";

	echo referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 2004, "Sorzano CO, Marabini R, Velázquez-Muriel J, Bilbao-Castro JR, Scheres SH, Carazo JM, Pascual-Montano A.", "J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");

	processing_footer();
	exit;
}

function jobForm($extra=false) {
	global $clusterdata, $CLUSTER_CONFIGS, $selectedcluster;
	$expId = $_GET['expId'];

	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = $sessiondata['Image path'];
	ereg("(.*)leginon(.*)rawdata", $sessionpath, $reg_match);
	$rootpath = "appion".$reg_match[2]."recon/";
	$sessionpath=$reg_match[1].$rootpath;

	$clusterdata->set_rootpath($rootpath);
	$clusterdata->post_data();

	$particle = new particledata();

	// get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$box = $stackinfo[2];

	// get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$syminfo = explode(' ',$modelinfo[4]);
	$modsym=$syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	$clusterdefaults = ($selectedcluster==$_POST['clustermemo']) ? true : false;
	
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$reconruns = count($particle->getReconIdsFromSession($expId));
	while (glob($outdir.'*recon'.($reconruns+1))) {
		$reconruns += 1;
	}
	$defrunid = 'xmipprecon'.($reconruns+1);
	$jobname = ($_POST['jobname']) ? $_POST['jobname'] : $defrunid;

	$nodes = ($_POST['nodes'] && $clusterdefaults) ? $_POST['nodes'] : C_NODES_DEF;
	$ppn = ($_POST['ppn'] && $clusterdefaults) ? $_POST['ppn'] : C_PPN_DEF;
	$rprocs = ($_POST['rprocs'] && $clusterdefaults) ? $_POST['rprocs'] : C_RPROCS_DEF;
	$walltime = ($_POST['walltime'] && $clusterdefaults) ? $_POST['walltime'] : C_WALLTIME_DEF;
	$cput = ($_POST['cput'] && $clusterdefaults) ? $_POST['cput'] : C_CPUTIME_DEF;

	$javafunc .= defaultReconValues($box);
	$javafunc .= writeJavaPopupFunctions('appion');
	processing_header("Xmipp Job Generator","Xmipp Job Generator",$javafunc);
	// write out errors, if any came up:
	if (!($user && $pass)) echo "<font color='red'><B>WARNING!!!</B> You are not logged in!!!</font><br />";
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<form name='xmippjob' method='post' action='$formaction'><br />\n";
	echo "<input type='hidden' name='clustermemo' value='".$selectedcluster."'>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";

	echo "<table border='0' cellpadding='0' cellspacing='0' width='600'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>
    <td><b>Cluster:</b></td>
		<td><select name='cluster' onchange='xmippjob.submit()'>
		";
		foreach ($CLUSTER_CONFIGS as $cluster) {
			$s = ($cluster == $_POST['cluster']) ? 'selected' : '';
			echo '<option value="'.$cluster.'" '.$s.' >'.$cluster.'</option>'."\n";
		}
	echo "
		</select></td>
  </tr>
  <tr>
    <td><B>Job Run Name:</B></td>
    <td><input type='text' name='jobname' value='$jobname' size='20'></td>
  </tr>
  <tr>
    <td><B>Output Directory:</B></td>
    <td><input type='text' NAME='outdir' value='$outdir' size='50'></td>
  </tr>
  </table>\n";
	echo closeRoundBorder();
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<p>\n";

	//--- overall PBS tables
	echo "<table border='0'><tr><td valign='top'>"; 

	//--- Cluster Parameters
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>\n";
	echo "<td colspan='4' align='center'>\n";
	echo "<h4>PBS Cluster Parameters</h4>\n";
	echo "</td>\n";
	echo "</tr>\n";
	echo "<tr>
      <td><a href='#' id='lcp1' onMouseOver='popLayer(\"nodes\", \"lcp1\")' onMouseOut='hideLayer()'>Nodes:</A></td>
      <td><input type='text' NAME='nodes' VALUE='$nodes' SIZE='4' MAXCHAR='4'></td>
      <td><a href='#' id='lcp2' onMouseOver='popLayer(\"procpernode\", \"lcp2\")' onMouseOut='hideLayer()'>Proc/Node:</A></td>
      <td><input type='text' NAME='ppn' VALUE='$ppn' SIZE='3'></td>
    </tr>
    <tr>
      <td><a href='#' id='lcp3' onMouseOver='popLayer(\"walltime\", \"lcp3\")' onMouseOut='hideLayer()'>Wall Time:</A></td>
      <td><input type='text' NAME='walltime' VALUE='$walltime' SIZE='4'></td>
      <td><a href='#' id='lcp4' onMouseOver='popLayer(\"cputime\", \"lcp4\")' onMouseOut='hideLayer()'>CPU Time</A></td>
      <td><input type='text' NAME='cput' VALUE='$cput' SIZE='4'></td>
    </tr>
    <tr>
      <td colspan='4'>
      Reconstruction procs per node:<input type='text' NAME='rprocs' VALUE='$rprocs' SIZE='3'>
      </td>
    </tr>
    </table>\n";
	echo $clusterdata->cluster_parameters();
	echo closeRoundBorder();
	echo"</td></tr></table>"; //overall table

	$bgcolor="#E8E8E8";
	$display_keys = array('copy','itn','ang','mask','imask','amask','sym','maxshift','hard','clskeep','clsiter','filt3d','xfiles','shrink','euler2','median','phscls','refine','tree','coran','coranCC','coranmask','coranlp','coranhp','eotest','copy');  
	echo"
  <br />
  <H4 style='align=\'center\' >Xmipp Reconstruction Parameters</H4>
  <hr />
	";

	// import values from previous uploaded reconstruction
	$projectId=getProjectId();
	$sessions = $leginondata->getSessions("",$projectId);
	if (is_array($sessions)) {
	  	$ropt = "";
		foreach ($sessions as $s) {
			$recons = $particle->getReconIdsFromSession($s['id']);
			if (is_array($recons)) {
				foreach ($recons as $r) {
					$ropt.= "<option value='".$r['DEF_id']."'>";
					$ropt.= $s['name']." : ";
					$ropt.= $r['name']." - ".$r['description'];
					$ropt.= "</option>\n";
				}
			}
		}
	}
	
	echo "<input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults'>\n";
	echo "<select name='import' onChange='xmippjob.submit()'>\n";
	echo "<option>Import parameters</option>\n";
	echo "<option value='asymm'>Asymmetric particles</option>\n";
	echo "<option value='low'>Low symmetry particles</option>\n";
	echo "<option value='icos'>Icosahedral particles</option>\n";
	echo "<option value=''>------------------------------</option>\n";
	echo $ropt;
	echo "</select>\n";
	echo "<br />\n";
	echo "<br />\n";

	if ($_POST['import']=='asymm' || $_POST['import']=='low' || $_POST['import']=='icos') {
      $MaskRadius = $_POST['MaskRadius'];
      $InnerRadius = $_POST['InnerRadius'];
      $OuterRadius = $_POST['OuterRadius'];
      $Mask = '';
      $MaxChangeOffset = '1000';
      $Search5DShift = '4x5 0';
      $Search5DStep = '2';
      $DiscardPercentage = '10';
      $ReconstructionMethod = 'fourier';
      $ARTLambda = '0.15';
      $FourierMaxFrequencyOfInterest = '0.25';
      $DoComputeResolution = 'CHECKED';
      $DoLowPassFilter = 'CHECKED';
      $DontUseFscForFilter = '';
      $ConstantToAddToFiltration = '0.1';
    }
	if ($_POST['import']=='asymm') {
      $SymmetryGroup = 'c1';
      $NumberOfIterations = '10';
      $AngularSteps = '4x10 2x5 2x3 2x2';
      $MaxAngularChange = '4x1000 2x20 2x9 2x6';
	} elseif ($_POST['import']=='low') {
      $SymmetryGroup = '*** Fill this ***';
      $NumberOfIterations = '15';
      $AngularSteps = '4x8 3x6 3x4 3x2 2x1';
      $MaxAngularChange = '4x1000 2x20 2x9 2x6 5x4';
	} elseif ($_POST['import']=='icos') {
      $SymmetryGroup = 'i1';
      $NumberOfIterations = '15';
      $AngularSteps = '4x5 3x3 3x2 5x1';
      $MaxAngularChange = '4x1000 2x10 2x8 2x6 5x4';
    }

	echo "<b>Particle dependent parameters</b>\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='MaskRadius' SIZE='4' VALUE='$MaskRadius'>\n";
	echo docpop('mask','Mask radius');
	echo "<font size='-2'>(pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='InnerRadius' VALUE='$InnerRadius' SIZE='4'>\n";
	echo docpop('innerradius','Inner radius for alignment');
	echo "<font size='-2'>(pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='OuterRadius' VALUE='$OuterRadius' SIZE='4'>\n";
	echo docpop('Outerradius','Outer radius for alignment');
	echo "<font size='-2'>(pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='SymmetryGroup' VALUE='$SymmetryGroup' SIZE='4'>\n";
	echo docpop('symmetrygroup','Symmetry Group');
	echo "<br/>\n";

	echo "<br />\n";
	echo "<br />\n";

	echo "<b>Other parameters</b> (Usually the default values should do)\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='NumberOfIterations' SIZE='4' VALUE='$NumberOfIterations'>\n";
	echo docpop('niterrec','Number of iterations');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='Mask' VALUE='$Mask' SIZE='20'>\n";
	echo docpop('maskfile','Mask filename');
	echo "<font size='-2'>(if you use this field you cannot use Mask Radius)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='AngularSteps' VALUE='$AngularSteps' SIZE='20'>\n";
	echo docpop('angularsteps','Angular sampling rate');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='MaxAngularChange' VALUE='$MaxAngularChange' SIZE='20'>\n";
	echo docpop('maxangularchange','Max. Angular change');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='MaxChangeOffset' VALUE='$MaxChangeOffset' SIZE='20'>\n";
	echo docpop('maxchangeoffset','Maximum change offset');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='Search5DShift' VALUE='$Search5DShift' SIZE='20'>\n";
	echo docpop('search5dshift','Search range for 5D translational search');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='Search5DStep' VALUE='$Search5DStep' SIZE='20'>\n";
	echo docpop('search5dstep','Step size for 5D translational search');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='DiscardPercentage' VALUE='$DiscardPercentage' SIZE='20'>\n";
	echo docpop('discardpercentage','Discard percentage of images with CCF below');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='ReconstructionMethod' VALUE='$ReconstructionMethod' SIZE='20'>\n";
	echo docpop('reconstructionmethod','Reconstruction method');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='ARTLambda' VALUE='$ARTLambda' SIZE='20'>\n";
	echo docpop('artlambda','Values of lambda for ART');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='FourierMaxFrequencyOfInterest' VALUE='$FourierMaxFrequencyOfInterest' SIZE='4'>\n";
	echo docpop('fouriermaxfrequencyofinterest','Initial maximum frequency used by reconstruct fourier');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='DoComputeResolution' $DoComputeResolution>\n";
	echo docpop('docomputeresolution','Compute resolution?');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='DoLowPassFilter' $DoLowPassFilter>\n";
	echo docpop('dolowpassfilter','Low-pass filter the reference?');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='DontUseFscForFilter' $DontUseFscForFilter>\n";
	echo docpop('dontusefscforfilter','Do not use estimated resolution for low-pass filtering?');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='ConstantToAddToFiltration' VALUE='$ConstantToAddToFiltration' SIZE='20'>\n";
	echo docpop('constanttoaddtofiltration','Constant to by add to the estimated resolution');
	echo "<br/>\n";

	echo "<br/>\n";

    echo "<br/>\n";
    echo "<input type='SUBMIT' NAME='write' VALUE='Create Job File'>\n";
    echo "</form>\n";

	echo referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 2004, "Sorzano CO, Marabini R, Velázquez-Muriel J, Bilbao-Castro JR, Scheres SH, Carazo JM, Pascual-Montano A.", "J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");

	processing_footer();
	exit;
}

function formatEndPath($path) {
	$path = ereg(DIRECTORY_SEPARATOR."$", $path) ? $path : $path.DIRECTORY_SEPARATOR;
	return $path;
}

function writeJobFile ($extra=False) {
	global $clusterdata;
	$particle = new particledata();
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$dmfpath = $_POST['dmfpath'];

	$jobname = $_POST['jobname'];
	$jobfile ="$jobname.job";

	$clustername = C_NAME;
	$outdir = formatEndPath($_POST['outdir']);

	$clusterpath=$clusterdata->get_path();
	$clusterpath = formatEndPath($clusterpath);

	$clusterdata->post_data();

	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$apix=$stackinfo[1];
	$box=$stackinfo[2];

	// get the model id
	$modelinfo=explode('|--|',$_POST['model']);
	$modelid=$modelinfo[0];
	$initmodel = $particle->getInitModelInfo($modelid);
	if ($initmodel['boxsize'] != $box) $rebox = True; 
	if (round($initmodel['pixelsize'],2) != round($apix,2)) $rescale = "scale=".$initmodel['pixelsize']/$apix;

	// Get the projectid
	$projectid=getProjectId();

	// insert the job file into the database
	if (!$extra) {
		$javafunc.=$clusterdata->get_javascript();
	}
	processing_header("Xmipp Job Generator","Xmipp Job Generator", $javafunc);
	$header.= "#PBS -l nodes=".$_POST['nodes'].":ppn=".$_POST['ppn']."\n";
	$header.= "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
	$header.= "#PBS -l cput=".$_POST['cput'].":00:00\n";
	$header.= "#PBS -l mem=2gb\n";
	$header.= "#PBS -m e\n";
	$header.= "#PBS -r n\n";
	$header.= "#PBS -j oe\n\n";
	$clusterjob = "# stackId: $stackidval\n";
	$clusterjob.= "# modelId: $modelid\n\n";
	
	$procs=$_POST['nodes']*$_POST['rprocs'];

    $ejob.='xmippRefine.py ';
    $ejob.='--projectid='.$projectid.' ';
    $ejob.='--stackid='.$stackidval.' ';
    $ejob.='--modelid='.$modelid.' ';
    $ejob.='--rundir=. ';
    $ejob.='--pixelSize='.$apix.' ';
    $ejob.='--boxSize='.$box.' ';
    $ejob.='--NumberOfIterations='.$_POST["NumberOfIterations"].' ';
    $ejob.='--MaskRadius='.$_POST["MaskRadius"].' ';
    $ejob.='--Mask="'.$_POST["Mask"].'" ';
    $ejob.='--InnerRadius='.$_POST["InnerRadius"].' ';
    $ejob.='--OuterRadius='.$_POST["OuterRadius"].' ';
    $ejob.='--AngularSteps="'.$_POST["AngularSteps"].'" ';
    $ejob.='--MaxAngularChange="'.$_POST["MaxAngularChange"].'" ';
    $ejob.='--MaxChangeOffset="'.$_POST["MaxChangeOffset"].'" ';
    $ejob.='--Search5DShift="'.$_POST["Search5DShift"].'" ';
    $ejob.='--Search5DStep="'.$_POST["Search5DStep"].'" ';
    $ejob.='--SymmetryGroup="'.$_POST["SymmetryGroup"].'" ';
    $ejob.='--DiscardPercentage="'.$_POST["DiscardPercentage"].'" ';
    $ejob.='--ReconstructionMethod="'.$_POST["ReconstructionMethod"].'" ';
    $ejob.='--ARTLambda="'.$_POST["ARTLambda"].'" ';
    $ejob.='--FourierMaxFrequencyOfInterest="'.$_POST["FourierMaxFrequencyOfInterest"].'" ';
    if ($DoComputeResolution.checked)
        $ejob.='--DoComputeResolution ';
    if ($DoLowPassFilter.checked)
        $ejob.='--DoLowPassFilter ';
    if ($DontUseFscForFilter.checked)
        $ejob.='--DontUseFscForFilter ';
    $ejob.='--ConstantToAddToFiltration="'.$_POST["ConstantToAddToFiltration"].'" ';
    $ejob.='--NumberOfMPIProcesses='.$_POST["nodes"].' ';
    $ejob.='--NumberOfThreads='.$_POST["rprocs"].' ';

	$clusterjob .= $clusterdata->cluster_job_file($ejob);
	
	if (!$extra) {
		echo $clusterdata->cluster_check_msg();
		echo "<p>";
	} else {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<form name='xmippjob' method='POST' action='$formAction'>\n";
	echo "<input type='hidden' name='clustername' value='".C_NAME."'>\n";
	echo "<input type='hidden' name='cluster' value='".C_NAME."'>\n";
	echo "<input type='hidden' NAME='clusterpath' value='$clusterpath'>\n";
	echo "<input type='hidden' NAME='dmfpath' value='$dmfpath'>\n";
	echo "<input type='hidden' NAME='jobname' value='$jobname'>\n";
	echo "<input type='hidden' NAME='outdir' value='$outdir'>\n";

	// convert \n to /\n's for script
	$header_conv=preg_replace('/\n/','|--|',$header);

	echo "<input type='hidden' NAME='header' VALUE='$header_conv'>\n";
	echo "<input type='submit' NAME='submitjob' VALUE='Submit Job to Cluster'>\n";
   echo "</form>\n";
	echo "</p>";
	if (!$extra) {
		echo "<hr>\n";
		echo "<pre>\n";
		echo $header;
		echo $clusterjob;
		echo "</pre>\n";
		$tmpfile = "/tmp/$jobfile";
		// write file to tmp directory
		$f = fopen($tmpfile,'w');
		fwrite($f,$clusterjob);
		fclose($f);
	}

	echo referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 2004, "Sorzano CO, Marabini R, Velázquez-Muriel J, Bilbao-Castro JR, Scheres SH, Carazo JM, Pascual-Montano A.", "J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");

	processing_footer();
	exit;
}

function defaultReconValues ($box) {
	$rad = ($box/2)-2;
	$javafunc = "
  <script type='text/javascript'>
    function setDefaults(obj) {
      obj.MaskRadius.value = $rad;
      obj.InnerRadius.value = '4';
      obj.OuterRadius.value = $rad;
      obj.SymmetryGroup.value = 'c1';
      obj.NumberOfIterations.value = '10';
      obj.Mask.value = '';
      obj.AngularSteps.value = '4x10 2x5 2x3 2x2';
      obj.MaxAngularChange.value = '4x1000 2x20 2x9 2x6';
      obj.MaxChangeOffset.value = '1000';
      obj.Search5DShift.value = '4x5 0';
      obj.Search5DStep.value = '2';
      obj.DiscardPercentage.value = '10';
      obj.ReconstructionMethod.value = 'fourier';
      obj.ARTLambda.value = '0.15';
      obj.FourierMaxFrequencyOfInterest.value = '0.25';
      obj.DoComputeResolution.checked = true;
      obj.DoLowPassFilter.checked = true;
      obj.DontUseFscForFilter.checked = false;
      obj.ConstantToAddToFiltration.value = '0.1';
      return;
    }
  </SCRIPT>\n";
	return $javafunc;
};

?>
