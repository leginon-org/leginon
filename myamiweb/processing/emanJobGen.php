<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an EMAN Job for submission to a cluster
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

/*
******************************************
******************************************
******************************************
*/

if ($_POST['write']) {
	// third step: write job file and prepare to submit
	writeJobFile();
} elseif ($_POST['submitstackmodel'] || $_POST['duplicate'] || $_POST['import']) {
	// second step: create form to fill job parameters
	jobForm();
} elseif ($_POST['submitjob']) {
	// final step: submit job to cluster
	submitJob();
} else {
	// first step: select model and stack
	stackModelForm();
}

/*
******************************************
******************************************
******************************************
*/

function submitJob($extra=False) {
	// submit job
	global $clusterdata;
	$particle = new particledata();
	$clusterdata->post_data();

	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$host = $_POST['clustername'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	if (!($user && $pass))
		writeJobFile("<B>ERROR:</B> Enter a user name and password");

	$jobname = $_POST['jobname'];
	$outdir = $_POST['outdir'].$jobname;

	$dmfpath=null;
	if (!empty($_POST['dmfpath'])) {
		$dmfpath=$_POST['dmfpath'].$jobname;
	}

	$clusterpath=$_POST['clusterpath'].$jobname;
	$jobfile="$jobname.job";
	$tmpjobfile = "/tmp/$jobfile";
	if (!file_exists($tmpjobfile))
		writeJobFile("<B>ERROR:</B> Could not find temp jobfile: $tmpjobfile");

	$jobid=$particle->insertClusterJobData($host,$outdir,$dmfpath,$clusterpath,$jobfile,$expId,'emanrecon',$user);

	// add header & job id to the beginning of the script
	// convert /\n's back to \n for the script
	$header = explode('|--|',$_POST['header']);
	$clusterjob = "## $jobname\n";
	foreach ($header as $l) $clusterjob.="$l\n";

	$clusterjob.= C_APPION_BIN."updateAppionDB.py $jobid R $projectId\n\n";
	$clusterjob.= "# jobId: $jobid\n";
	$clusterjob.= "# projectId: $projectId\n";
	$clusterlastline.= "\n".C_APPION_BIN."updateAppionDB.py $jobid D $projectId\nexit\n\n";
	$f = file_get_contents($tmpjobfile);
	file_put_contents($tmpjobfile, $clusterjob . $f . $clusterlastline);

	processing_header("EMAN Job Submitted","EMAN Job Submitted",$javafunc);
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
	echo "<tr><td>Appion Job Id</td><td>$jobid</td></tr>\n";
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
		echo "message: '$jobnum'<br/>";
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

/*
******************************************
******************************************
******************************************
*/

function stackModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	$javafunc="<script src='../js/viewer.js'></script>\n";
	processing_header("EMAN Job Generator","EMAN Job Generator",$javafunc);

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
			$modelvals = "$model[DEF_id]|--|$model[path]|--|$model[name]|--|$model[boxsize]|--|$symdata[eman_name]";

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
	processing_footer();
	exit;
}

/*
******************************************
******************************************
******************************************
*/

function jobForm($extra=false) {
	global $clusterdata, $CLUSTER_CONFIGS, $selectedcluster;
	$expId = $_GET['expId'];

	if (!$_POST['model']) stackModelForm("ERROR: no initial model selected");
	if (!$_POST['stackval']) stackModelForm("ERROR: no stack selected");

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
	$stackid = $stackinfo[0];

	// get model data
	$modelinfo = explode('|--|',$_POST['model']);
	//echo print_r($modelinfo)."<br/>";
	$syminfo = explode(' ',$modelinfo[4]);
	//echo print_r($syminfo)."<br/>";
	$modsym = $syminfo[0];
	//echo print_r($modsym)."<br/>";
	if ($modsym == 'Icosahedral') $modsym='icos';
	$modelid = $modelinfo[0];

	$clusterdefaults = ($selectedcluster==$_POST['clustermemo']) ? true : false;


	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$reconruns = count($particle->getReconIdsFromSession($expId));
	while (glob($outdir.'*recon'.($reconruns+1))) {
		$reconruns += 1;
	}
	$defrunid = 'emanrecon'.($reconruns+1);
	$jobname = ($_POST['jobname']) ? $_POST['jobname'] : $defrunid;

	$nodes = ($_POST['nodes'] && $clusterdefaults) ? $_POST['nodes'] : C_NODES_DEF;
	$ppn = ($_POST['ppn'] && $clusterdefaults) ? $_POST['ppn'] : C_PPN_DEF;
	$rprocs = ($_POST['rprocs'] && $clusterdefaults) ? $_POST['rprocs'] : C_RPROCS_DEF;
	$walltime = ($_POST['walltime'] && $clusterdefaults) ? $_POST['walltime'] : C_WALLTIME_DEF;
	$cput = ($_POST['cput'] && $clusterdefaults) ? $_POST['cput'] : C_CPUTIME_DEF;

	$numiters= ($_POST['numiters']) ? $_POST['numiters'] : 1;
	if ($_POST['duplicate']) {
		$numiters+=1;
		$j=$_POST['duplicate'];
	}
	else $j=$numiters;

	$javafunc .= defaultReconValues($box);
	$javafunc .= writeJavaPopupFunctions('eman');
	processing_header("EMAN Job Generator","EMAN Job Generator",$javafunc);
	// write out errors, if any came up:
	if (!($user && $pass)) echo "<font color='#CC3333' size='+2'><B>WARNING!!!</B> You are not logged in!!!</font><br/>";

	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='emanjob' method='post' action='$formaction'><br />\n";
	echo "<input type='hidden' name='clustermemo' value='".$selectedcluster."'>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";

	echo "<table border='0' cellpadding='0' cellspacing='0' width='600'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>
		<td><b>Cluster:</b></td>
		<td><select name='cluster' onchange='emanjob.submit()'>
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
	echo "<tr><td>\n";
		echo docpop('nodes',"Nodes: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='nodes' VALUE='$nodes' SIZE='4' MAXCHAR='4'>";
	echo "</td><td>\n";
		echo docpop('procpernode',"Proc/Node: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='ppn' VALUE='$ppn' SIZE='3'>";
	echo "</td></tr><tr><td>\n";
		echo docpop('walltime',"Wall Time: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='walltime' VALUE='$walltime' SIZE='4'>";
	echo "</td><td>\n";
		echo docpop('cputime',"CPU Time: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='cput' VALUE='$cput' SIZE='4'>";
	echo "</td></tr><tr><td colspan='4'>";
		echo "Recon procs per node:<input type='text' NAME='rprocs' VALUE='$rprocs' SIZE='3'>";
	echo "</td></tr>\n";
	echo "</table>\n";
	echo $clusterdata->cluster_parameters();
	echo closeRoundBorder();
	echo "<br/>\n";
	echo "<br/>\n";

	echo"</td></tr></table>"; //overall table

	$bgcolor="#E8E8E8";
	$display_keys = array('copy','itn','ang','mask','imask','amask','sym','maxshift','hard','clskeep','clsiter','filt3d','xfiles','shrink','euler2','median','phscls','refine','tree','coran','eotest','copy');
	echo"
	<br />
	<h4> EMAN Reconstruction Parameters</h4>
	<input type='SUBMIT' NAME='write' VALUE='Create Job File'><br/><hr/>\n
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

	echo "<input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults for Iteration 1'>\n";
	echo "<select name='import' onChange='emanjob.submit()'>\n";
	echo "<option>Import parameters</option>\n";
	echo "<option value='groel1'>GroEL with 10,000+ particles</option>\n";
	echo "<option value='virusgood'>Icos Virus with good starting model</option>\n";
	echo "<option value='asymm'>Mostly asymmetric particle</option>\n";
	echo "<option value=''>------------------------------</option>\n";
	echo $ropt;
	echo "</select>\n";
	echo "<br />
	<TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
		<tr>\n";
	foreach ($display_keys as $k=>$key) {
		$id="l$k";
		echo"<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"$id\" onMouseOver='popLayer(\"$key\", \"$id\")' onMouseOut='hideLayer()'>$key</a></font></td>\n";
	}
	echo"  </tr>\n";

	// set number of iterations if importing:
	if ($_POST['import']=='groel1') $numiters=20;
	elseif ($_POST['import']=='virusgood') $numiters=14;
	elseif ($_POST['import']=='asymm') $numiters=9;
	elseif (is_numeric($_POST['import'])) {
		$iterinfo = $particle->getIterationInfo($_POST['import']);
		// get initial model info
		$refinfo = $particle->getRefinementRunInfo($_POST['import']);
		$initmodel = $particle->getInitModelInfo($refinfo['REF|ApInitialModelData|initialModel']);
		$stackinfo = $particle->getStackParams($refinfo['REF|ApStackData|stack']);
		// get scaling factor for box sizes
		$prevboxsize = ($stackinfo['bin']) ? $stackinfo['boxSize']/$stackinfo['bin'] : $stackinfo['boxSize'];
		$boxscale = $box / $prevboxsize;
		$numiters = count($iterinfo);
	}

	// otherwise use previously set values
	for ($i=1; $i<=$numiters; $i++) {
		$angn="ang".$i;
		$maskn="mask".$i;
		$imaskn="imask".$i;
		$amask1n="amask1".$i;
		$amask2n="amask2".$i;
		$amask3n="amask3".$i;
		$symn="sym".$i;
		$maxshiftn="maxshift".$i;
		$hardn="hard".$i;
		$classkeepn="classkeep".$i;
		$classitern="classiter".$i;
		$filt3dn="filt3d".$i;
		$shrinkn="shrink".$i;
		$euler2n="euler2".$i;
		$xfilesn="xfiles".$i;
		#$perturbn="perturb".$i;
		$treen="tree".$i;
		$mediann="median".$i;
		$phaseclsn="phasecls".$i;
		#$fsclsn="fscls".$i;
		$refinen="refine".$i;
		#$goodbadn="goodbad".$i;
		$eotestn="eotest".$i;
		$corann="coran".$i;
		$coranCCn="coranCC".$i;
		$coranmaskn="coranmask".$i;
		$coranlpn="coranlp".$i;
		$coranhpn="coranhp".$i;
		$affpropn="affprop".$i;
		$affpropCCn="affpropCC".$i;
		$affpropMPn="affpropMP".$i;

		// if importing values, set them here
		if ($_POST['import']=='groel1') {
			// values that don't change:
			$mask = $_POST['mask1'] ? $_POST['mask1'] : ($box/2)-2;
			$hard='25';
			$classkeep='0.8';
			$median = $_POST['median1']=='on' ? 'CHECKED' : '';
			$refine = $_POST['refine1']=='on' ? 'CHECKED' : '';
			$coran = $_POST['coran1']=='on' ? 'CHECKED' : '';
			$phasecls='CHECKED';
			$eotest='CHECKED';
			$sym=$modsym;
			$classiter=((($i+1) % 4) < 2) ? 3 : 8;
			if ($i < 5) $ang=5;
			elseif ($i < 9) $ang=4;
			elseif ($i < 13) $ang=3;
			elseif ($i < 17) $ang=2;
			else {
				$ang=1;
				$refine='CHECKED';
			}
		}
		elseif ($_POST['import']=='virusgood') {
			// values that don't change:
			$mask=($box/2)-2;
			$hard='25';
			$classkeep='0.8';
			$median = $_POST['median1']=='on' ? 'CHECKED' : '';
			$refine = $_POST['refine1']=='on' ? 'CHECKED' : '';
			$coran = $_POST['coran1']=='on' ? 'CHECKED' : '';
			$phasecls='CHECKED';
			$eotest='CHECKED';
			$sym=$modsym;
			$classiter=((($i+1) % 4) < 2) ? 3 : 8;
			if ($i < 5) $ang=3;
			elseif ($i < 9) $ang=2;
			elseif ($i < 12) {
				$ang=1;
				$classiter=3;
			}
			else {
				$classiter=3;
				$ang=0.8;
				$refine='CHECKED';
			}
		}
		elseif ($_POST['import']=='asymm') {
			// values that don't change:
			$mask=($box/2)-2;
			$hard='25';
			$classkeep='0.8';
			$phasecls='CHECKED';
			$median = $_POST['median1']=='on' ? 'CHECKED' : '';
			$refine = $_POST['refine1']=='on' ? 'CHECKED' : '';
			$coran = $_POST['coran1']=='on' ? 'CHECKED' : '';
			$eotest='CHECKED';
			$sym=$modsym;
			$classiter=((($i) % 3) < 1) ? 3 : 8;
			if ($i <= 3)
				$ang=10;
			elseif ($i <= 6)
				$ang=8;
			elseif ($i <= 9) {
				$ang=6;
				$refine='CHECKED';
			}
		}
		elseif (is_numeric($_POST['import'])) {
			foreach ($iterinfo as $iter) {
				if ($iter['iteration'] == $i) {
					$ang=$iter['ang'];
					$mask=ceil($iter['mask']*$boxscale);
					if (floor($iter['imask']*$boxscale) > 0)
						$imask=floor($iter['imask']*$boxscale);
					$amask1=$iter['EMAN_amask1'];
					$amask2=$iter['EMAN_amask2'];
					$amask3=$iter['EMAN_amask3'];
					$maxhsift=$iter['EMAN_maxshift'];
					$hard=$iter['EMAN_hard'];
					$classiter=$iter['EMAN_classiter'];
					$classkeep=$iter['EMAN_classkeep'];
					$filt3d=$iter['EMAN_filt3d'];
					$shrink=$iter['EMAN_shrink'];
					$euler2=$iter['EMAN_euler2'];
					$xfiles=$iter['EMAN_xfiles'];
					$median = ($iter['EMAN_median']) ? 'CHECKED' : '';
					$phasecls = ($iter['EMAN_phasecls']) ? 'CHECKED' : '';
					#$fscls = ($iter['EMAN_fscls']) ? 'CHECKED' : '';
					$refine = ($iter['EMAN_refine']) ? 'CHECKED' : '';
					#$goodbad = ($iter['EMAN_goodbad']) ? 'CHECKED' : '';
					$coran = ($iter['postRefineClassAverages']) ? 'CHECKED' : '';
					#$perturb = ($iter['EMAN_perturb']) ? 'CHECKED' : '';
					$eotest = ($iter['REF|ApResolutionData|resolution']) ? 'CHECKED' : '';
					$symmetry = $particle->getSymInfo($iter['REF|ApSymmetryData|symmetry']);
					if (!is_array($symmetry)) $sym=$modsym;
					else $sym = $symmetry['eman_name'];
					continue;
				}
			}
		}
		else {
			$ang=($i>$j) ? $_POST["ang".($i-1)] : $_POST[$angn];
			$mask=($i>$j) ? $_POST["mask".($i-1)] : $_POST[$maskn];
			$imask=($i>$j) ? $_POST["imask".($i-1)] : $_POST[$imaskn];
			$amask1=($i>$j) ? $_POST["amask1".($i-1)] : $_POST[$amask1n];
			$amask2=($i>$j) ? $_POST["amask2".($i-1)] : $_POST[$amask2n];
			$amask3=($i>$j) ? $_POST["amask3".($i-1)] : $_POST[$amask3n];
			$sym=($i>$j) ? $_POST["sym".($i-1)] : $_POST[$symn];
			$maxshift=($i>$j) ? $_POST['maxshift'.($i-1)] : $_POST[$maxshiftn];
			$hard=($i>$j) ? $_POST["hard".($i-1)] : $_POST[$hardn];
			$classkeep=($i>$j) ? $_POST["classkeep".($i-1)] : $_POST[$classkeepn];
			$classiter=($i>$j) ? $_POST["classiter".($i-1)] : $_POST[$classitern];
			$filt3d=($i>$j) ? $_POST["filt3d".($i-1)] : $_POST[$filt3dn];
			$shrink=($i>$j) ? $_POST["shrink".($i-1)] : $_POST[$shrinkn];
			$euler2=($i>$j) ? $_POST["euler2".($i-1)] : $_POST[$euler2n];
			$xfiles=($i>$j) ? $_POST["xfiles".($i-1)] : $_POST[$xfilesn];
			$coranCC=($i>$j) ? $_POST["coranCC".($i-1)] : $_POST[$coranCCn];
			$coranmask=($i>$j) ? $_POST["coranmask".($i-1)] : $_POST[$coranmaskn];
			$coranlp=($i>$j) ? $_POST["coranlp".($i-1)] : $_POST[$coranlpn];
			$coranhp=($i>$j) ? $_POST["coranhp".($i-1)] : $_POST[$coranhpn];
			$affpropCC=($i>$j) ? $_POST["affpropCC".($i-1)] : $_POST[$affpropCCn];
			$affpropMP=($i>$j) ? $_POST["affpropMP".($i-1)] : $_POST[$affpropMPn];
			// use symmetry of model by default, but you can change it
			if ($i==1 && !$_POST['duplicate']) $sym=$modsym;

			if ($i>$j) {
				$median=($_POST["median".($i-1)]=='on') ? 'CHECKED' : '';
				$phasecls=($_POST["phasecls".($i-1)]=='on') ? 'CHECKED' : '';
				#$fscls=($_POST["fscls".($i-1)]=='on') ? 'CHECKED' : '';
				$refine=($_POST["refine".($i-1)]=='on') ? 'CHECKED' : '';
				#$goodbad=($_POST["goodbad".($i-1)]=='on') ? 'CHECKED' : '';
				$eotest=($_POST["eotest".($i-1)]=='on') ? 'CHECKED' : '';
				$coran=($_POST["coran".($i-1)]=='on') ? 'CHECKED' : '';
				#$perturb=($_POST["perturb".($i-1)]=='on') ? 'CHECKED' : '';
				$affprop=($_POST["affprop".($i-1)]=='on') ? 'CHECKED' : '';
				$treetwo=($_POST["tree".($i-1)]=='2') ? 'selected' : '';
				$treethree=($_POST["tree".($i-1)]=='3') ? 'selected' : '';
			}
			else {
				$median=($_POST[$mediann]=='on') ? 'CHECKED' : '';
				$phasecls=($_POST[$phaseclsn]=='on') ? 'CHECKED' : '';
				#$fscls=($_POST[$fsclsn]=='on') ? 'CHECKED' : '';
				$refine=($_POST[$refinen]=='on') ? 'CHECKED' : '';
				#$goodbad=($_POST[$goodbadn]=='on') ? 'CHECKED' : '';
				$eotest=($_POST[$eotestn]=='on') ? 'CHECKED' : '';
				$coran=($_POST[$corann]=='on') ? 'CHECKED' : '';
				#$perturb=($_POST[$perturbn]=='on') ? 'CHECKED' : '';
				$affprop=($_POST[$affpropn]=='on') ? 'CHECKED' : '';
				$treetwo=($_POST[$treen]=='2') ? 'selected' : '';
				$treethree=($_POST[$treen]=='3') ? 'selected' : '';
			}
		}
		$rcol = ($i % 2) ? '#FFFFFF' : '#FFFDCC';
		echo"
		<tr>
			<td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i' onclick='emanjob.submit()'></td>
			<td bgcolor='$rcol'><b>$i</b></td>
			<td bgcolor='$rcol'><input type='text' NAME='$angn' SIZE='3' VALUE='$ang'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$maskn' SIZE='4' VALUE='$mask'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$imaskn' SIZE='4' VALUE='$imask'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$amask1n' SIZE='3' VALUE='$amask1'>
				<input type='text' NAME='$amask2n' SIZE='2' VALUE='$amask2'>
				<input type='text' NAME='$amask3n' SIZE='2' VALUE='$amask3'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$symn' SIZE='5' VALUE='$sym'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$maxshiftn' SIZE='3' VALUE='$maxshift'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$hardn' SIZE='3' VALUE='$hard'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$classkeepn' SIZE='4' VALUE='$classkeep'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$classitern' SIZE='2' VALUE='$classiter'></td>
			<td bgcolor='$rcol'><input type='text' NAME='$filt3dn' SIZE='4' VALUE='$filt3d'></td>
			<td bgcolor='$rcol'><input type='text' size='5' name='$xfilesn' value='$xfiles'>
			<td bgcolor='$rcol'><input type='text' NAME='$shrinkn' SIZE='2' VALUE='$shrink'></td>
			<td bgcolor='$rcol'><input type='text' size='2' name='$euler2n' value='$euler2'>
			<td bgcolor='$rcol'><input type='checkbox' NAME='$mediann' $median></td>
			<td bgcolor='$rcol'><input type='checkbox' NAME='$phaseclsn' $phasecls></td>\n";
	#echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$fsclsn' $fscls></td>\n";
	echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$refinen' $refine></td>\n";
	#echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$perturbn' $perturb></td>\n";
	#echo"<td bgcolor='$rcol'><input type='checkbox' NAME='$goodbadn' $goodbad></td>\n";
	echo "<td bgcolor='$rcol'><select name='$treen'><option>-</option><option $treetwo>2</option><option $treethree>3</option></select></td>\n";
	echo "<td bgcolor='$rcol'>\n";

 // Coran box
	echo "  <table class='tableborder' border='1' cellpadding='4' cellspacing='4'>";
	echo "  <tr>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('coran', 'Use Coran')."</font></td>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('coranCC', 'CC cut')."</font></td>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('coranmask', 'Mask')."</font></td>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('coranlp', 'LP')."</font></td>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('coranhp', 'HP')."</font></td>\n";
	echo "  </tr>\n";
	echo "  <tr>\n";
	echo "    <td bgcolor='$rcol'><input type='checkbox' NAME='$corann' $coran></td>\n";
	echo "    <td bgcolor='$rcol'><input type='text' size='2' name='$coranCCn' value='$coranCC'></td>\n";
	echo "    <td bgcolor='$rcol'><input type='text' size='3' name='$coranmaskn' value='$coranmask'></td>\n";
	echo "    <td bgcolor='$rcol'><input type='text' size='2' name='$coranlpn' value='$coranlp'></td>\n";
	echo "    <td bgcolor='$rcol'><input type='text' size='2' name='$coranhpn' value='$coranhp'></td>\n";
	echo "  </tr></table>\n";
	echo "</td>\n";

 // Affinity propagation box
	/*
	echo "<td bgcolor='$rcol'>\n";
	echo "  <table class='tableborder' border='1' cellpadding='4' cellspacing='4'>";
	echo "  <tr>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('affprop', 'Use AP')."</font></td>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('affpropMP', 'Min part')."</font></td>\n";
	echo "    <td bgcolor='$rcol'><font size='-2'>".docpop('affpropCC', 'CC cut')."</font></td>\n";
	echo "  </tr>\n";
	echo "  <tr>\n";
	echo "    <td bgcolor='$rcol'><input type='checkbox' name='$affpropn' $affprop></td>\n";
	echo "    <td bgcolor='$rcol'><input type='text' size='2' name='$affpropMPn' value='$coranCC'></td>\n";
	echo "    <td bgcolor='$rcol'><input type='text' size='3' name='$affpropCCn' value='$coranmask'></td>\n";
	echo "  </tr></table>\n";
	echo "</td>\n";
	*/
	echo "<input type='hidden' name='$affpropn' value='off'>\n";

	echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$eotestn' $eotest></td>\n";
	echo "<td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i' onclick='emanjob.submit()'></td>\n";
	echo "</tr>\n";

	// SETUP FILELIST TO COPY OVER FILES
	$stackdata = $particle->getStackParams($stackid);
	$modeldata = $particle->getInitModelInfo($modelid);
	$sendfilelist = "";
	$ext=strrchr($stackdata['name'],'.');
	$stackname=substr($stackdata['name'],0,-strlen($ext));
	$sendfilelist .= formatEndPath($stackdata['path']).$stackname.".hed";
	$sendfilelist .= "|--|";
	$sendfilelist .= formatEndPath($stackdata['path']).$stackname.".img";
	$sendfilelist .= "|--|";
	$sendfilelist .= formatEndPath($modeldata['path']).$modeldata['name'];
	echo "<input type='hidden' NAME='sendfilelist' value='$sendfilelist'>\n";
	$receivefilelist = "model.tar.gz|--|results.tar.gz";
	echo "<input type='hidden' NAME='receivefilelist' value='$receivefilelist'>\n";

### commented out for now, since  not working properly
#	<TD colspan=6 bgcolor='$bgcolor' CELLPADDING=0 CELLSPACING=0>
#	  <table class='tableborder' border='1' cellpadding=4 cellspacing=4 width=100%>
#            <tr>
#        <td bgcolor='$bgcolor'><input type='checkbox' NAME='$msgpn' $msgp><A HREF=\"javascript:refinfopopup('msgp')\">Subclassification by message passing:</A></td>
#        <td bgcolor='$bgcolor'><A HREF=\"javascript:refinfopopup('msgp_corcutoff')\">CorCutoff:</A>
#          <input type='text' NAME='$msgp_corcutoffn' SIZE='4' VALUE='$msgp_corcutoff'></td>
#        <td bgcolor='$bgcolor'><A HREF=\"javascript:refinfopopup('msgp_minptcls')\">MinPtcls:</A>
#          <input type='text' NAME='$msgp_minptclsn' SIZE='4' VALUE='$msgp_minptcls'></td>
#            </tr>
#          </table>
#        <TD colspan=2 bgcolor='$bgcolor' ALIGN='CENTER'>
#      </tr>
	}
	echo"
	  </table>
	  <input type='hidden' NAME='numiters' VALUE='$numiters'><P>
	  <input type='SUBMIT' NAME='write' VALUE='Create Job File'>
	  </form><br/>\n";

	//echo "StackID: $stackid -- ModelID: $modelid<br/>\n";
	echo "<table class='tablebubble'><tr><td>\n";
	echo stacksummarytable($stackid, true);
	echo "</td></tr><tr><td>\n";
	echo modelsummarytable($modelid, true);
	echo "</td></tr></table>\n";

	processing_footer();
	exit;
}

/*
******************************************
******************************************
******************************************
*/

function formatEndPath($path) {
	$path = ereg(DIRECTORY_SEPARATOR."$", $path) ? $path : $path.DIRECTORY_SEPARATOR;
	return $path;
}

/*
******************************************
******************************************
******************************************
*/

function getPBSMemoryNeeded() {
	$particle = new particledata();
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$boxsize = (int) $stackinfo[2];
	$ppn = (int) $_POST['ppn'];
	$numpart = $particle->getNumStackParticles($stackidval);
	$numiters=$_POST['numiters'];
	$startang=$_POST["ang1"];
	$endang=$_POST["ang".$numiters];
	$emansym=$_POST["sym".$numiters];
	#print "SYMMETRY: '$emansym'<br/>\n";
	$symdata = $particle->getSymmetryDataFromEmanName($emansym);
	#echo print_r($symdata);
	$foldsym = (int) $symdata['fold_symmetry'];
	#print "FOLD SYMMETRY: $foldsym<br/>\n";
	$endnumproj = 18000.0/($foldsym*$endang*$endang);
	// need to open all projections and 1024 particles in memory
	$numpartinmem = $endnumproj + 1024;
	$memneed = $numpartinmem*$boxsize*$boxsize*16.0*$ppn;
	//echo "endnumproj = $endnumproj * boxsize = $boxsize*$boxsize*16.0";
	$numgig = ceil($memneed/1073741824.0);
	//echo "numpart = $numpart /startnumproj = $startnumproj *boxsize = $boxsize\n";
	//echo sprintf("numgig1 = %dgb\n", $numgig1);
	//echo sprintf("numgig2 = %dgb\n", $numgig2);
	//echo sprintf("numgig3 = %dgb\n", $numgig3);
	//echo sprintf("numgig = %dgb\n", $numgig);
	$sizestr = sprintf("%dgb", $numgig);
	return $sizestr;
}

/*
******************************************
******************************************
******************************************
*/

function writeJobFile ($extra=False) {
	global $clusterdata;
	$particle = new particledata();

	// cluster settings
	if (!$_POST['nodes'])
		jobForm("ERROR: No nodes specified, setting default=".C_NODES_DEF);
	if (!$_POST['ppn'])
		jobForm("ERROR: No processors per node specified, setting default=".C_PPN_DEF);
	if ($_POST['ppn'] > C_PPN_MAX )
		jobForm("ERROR: Max processors per node is ".C_PPN_MAX);
	if ($_POST['nodes'] > C_NODES_MAX )
		jobForm("ERROR: Max nodes on ".C_NAME." is ".C_NODES_MAX);
	if (!$_POST['walltime'])
		jobForm("ERROR: No walltime specified, setting default=".C_WALLTIME_DEF);
	if ($_POST['walltime'] > C_WALLTIME_MAX )
		jobForm("ERROR: Max walltime is ".C_WALLTIME_MAX);
	if (!$_POST['cput'])
		jobForm("ERROR: No CPU time specified, setting default=".C_CPUTIME_DEF);
	if ($_POST['cput'] > C_CPUTIME_MAX)
		jobForm("ERROR: Max CPU time is ".C_CPUTIME_MAX);
	if (!$_POST['rprocs'])
		jobForm("ERROR: No reconstruction ppn specified, setting default=".C_RPROCS_DEF);
	if ($_POST['rprocs'] > $_POST['ppn'])
	  jobForm("ERROR: Asking to reconstruct on more processors than available");

	// iteration settings
	$minang = 100;
	for ($i=1; $i<=$_POST['numiters']; $i++) {
		if (!$_POST['ang'.$i])
			jobForm("ERROR: no angular increment set for iteration $i");
		if ($minang > $_POST['ang'.$i])
			$minang = $_POST['ang'.$i];
		if (!$_POST['sym'.$i])
			jobForm("ERROR: no symmetry set for iteration $i");
		if (!$_POST['mask'.$i])
			jobForm("ERROR: no mask set for iteration $i");
		
		// if amask is used, then xfiles must also be used
		if ($_POST['amask1'.$i] || $_POST['amask2'.$i] || $_POST['amask3'.$i]) {
			if (!($_POST['amask1'.$i] && $_POST['amask2'.$i] && $_POST['amask3'.$i]))
				jobForm("ERROR: All 3 amask values of amask must be entered for iteration $i");
			if (!$_POST['xfiles'.$i])
				jobForm("ERROR: amask requires the use of xfiles for iteration $i");
		}
	}

	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
	$numpart=$stackinfo[3];

	// get number of particle per class
	$sym = $_POST['sym'.$_POST['numiters']];
	$symdata = $particle->getSymmetryDataFromEmanName($sym);
	if ($symdata) {
		$foldsym = (float) $symdata['fold_symmetry'];
		$numclass = ceil(18000./$foldsym/$minang/$minang);
		if ($numclass > 2500)
			jobForm("ERROR: too many classes requested ($numclass)<br/>increase angular increment");
		$partperclass = floor($numpart/$numclass);
		if ($partperclass < 3)
			jobForm("ERROR: too few particles per class ($partperclass)<br/>$numpart particles for $numclass classes");
	}

	// check that job file doesn't already exist
	$outdir = formatEndPath($_POST['outdir']);
	$outdir .= $_POST['jobname'];

	// jobname ends with .job
	$jobname = $_POST['jobname'];
	$jobname .= '.job';
	$exists = $particle->getJobFileFromPath($outdir,$jobname);

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

	// get the model id
	$modelinfo=explode('|--|',$_POST['model']);
	$modelid=$modelinfo[0];
	$initmodel = $particle->getInitModelInfo($modelid);
	if ($initmodel['boxsize'] != $box) $rebox = True;
	$scalefactor = $initmodel['pixelsize']/$apix;
	if (abs($scalefactor - 1.0) > 0.01)
		$rescale = sprintf("scale=%.5f", $scalefactor);

	// insert the job file into the database
	if (!$extra) {
		$javafunc.=$clusterdata->get_javascript();
	}
	processing_header("EMAN Job Generator","EMAN Job Generator", $javafunc);
	$header.= "#PBS -l nodes=".$_POST['nodes'].":ppn=".$_POST['ppn']."\n";
	$header.= "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
	$header.= "#PBS -l cput=".$_POST['cput'].":00:00\n";
	$memneed = getPBSMemoryNeeded();
	$header.= "#PBS -l mem=$memneed\n";
	$header.= "#PBS -m e\n";
	$header.= "#PBS -r n\n";
	$header.= "#PBS -j oe\n\n";
	$clusterjob = "# stackId: $stackidval\n";
	$clusterjob.= "# modelId: $modelid\n\n";

	$procs=$_POST['nodes']*$_POST['rprocs'];
	$numiters=$_POST['numiters'];

	// calculate pad and make it even
	$pad = intval($box*1.25/2.0)*2;

	$ejob = "\n";

	// rescale initial model, if necessary:
	if ($rebox || $rescale) {
		$ejob .= "#rescale initial model\n";
		$ejob .= "proc3d ".$initmodel['name']." threed.0a.mrc \\\n"
			."  $rescale clip=$box,$box,$box norm=0,1 origin=0,0,0\n\n";
	} else {
		$ejob .= "mv -v ".$initmodel['name']." threed.0a.mrc\n\n";
	}

	// rename stack, if necessary:
	if ($stackinfo[5] != "start.hed") {
		$ejob .= "#rename stack\n";
		$ejob .= "ln -s ".$stackinfo[5]." start.hed\n";
		$ejob .= "ln -s ".$stackinfo[6]." start.img\n";
		$ejob .= "\n";
	}

	for ($i=1; $i<=$numiters; $i++) {
		$ang=$_POST["ang".$i];
		$mask=$_POST["mask".$i];
		$imask=$_POST["imask".$i];
		$amask1=ceil($_POST["amask1".$i]);
		$amask2=$_POST["amask2".$i];
		$amask3=ceil($_POST["amask3".$i]);
		$sym=$_POST["sym".$i];
		$maxshift=$_POST["maxshift".$i];
		$hard=$_POST["hard".$i];
		$classkeep=$_POST["classkeep".$i];
		$classiter=$_POST["classiter".$i];
		$filt3d=$_POST["filt3d".$i];
		$shrink=$_POST["shrink".$i];
		$euler2=$_POST["euler2".$i];
		$xfiles=$_POST["xfiles".$i];
		#$perturb=$_POST["perturb".$i];
		$tree=$_POST["tree".$i];
		$median=$_POST["median".$i];
		$phasecls=$_POST["phasecls".$i];
		#$fscls=$_POST["fscls".$i];
		$refine=$_POST["refine".$i];
		#$goodbad=$_POST["goodbad".$i];
		$eotest=$_POST["eotest".$i];
		$coran=$_POST["coran".$i];
		$coranCC=$_POST["coranCC".$i];
		$coranmask=$_POST["coranmask".$i];
		$coranlp=$_POST["coranlp".$i];
		$coranhp=$_POST["coranhp".$i];
		$affprop=$_POST["affprop".$i];
		$affpropCC=$_POST["affpropCC".$i];
		$affpropMP=$_POST["affpropMP".$i];
		$line="\nrefine $i proc=$procs ang=$ang pad=$pad";
		if ($mask) $line.=" mask=$mask";
		if ($imask) $line.=" imask=$imask";
		if ($amask2) $line.=" amask=$amask1,$amask2,$amask3";
		if ($sym) $line.=" sym=$sym";
		if ($hard) $line.=" hard=$hard";
		if ($maxshift) $line.=" maxshift=$maxshift";
		if ($classkeep) $line.=" classkeep=$classkeep";
		if ($classiter) $line.=" classiter=$classiter";
		if ($filt3d) $line.=" filt3d=$filt3d";
		if ($shrink) $line.=" shrink=$shrink";
		if ($xfiles) $line.=" xfiles=$apix,$xfiles,99";
		if ($median=='on') $line.=" median";
		#if ($perturb=='on') $line.=" perturb";
		if ($tree=='2' || $tree=='3') $line.=" tree=$tree";
		#if ($fscls=='on') $line.=" fscls";
		if ($phasecls=='on') $line.=" phasecls";
		if ($refine=='on') $line.=" refine";
		if ($euler2) $line.=" euler2=$euler2";
		#if ($goodbad=='on') $line.=" goodbad";
		$line.=" > refine".$i.".txt\n";
		$line.="mv -v classes.".$i.".hed classes_eman.".$i.".hed\n";
		$line.="ln -s classes_eman.".$i.".hed classes.".$i.".hed\n";
		$line.="mv -v classes.".$i.".img classes_eman.".$i.".img\n";
		$line.="ln -s classes_eman.".$i.".img classes.".$i.".img\n";
		$line.="getProjEulers.py proj.img proj.$i.txt\n";
		// if ref-free correllation analysis
		if ($coran=='on') {
			$line .= C_APPION_BIN."coran_for_cls.py mask=$mask proc=$procs iter=$i";
			if ($sym) $line .= " sym=$sym";
			if ($hard) $line .= " hard=$hard";
			if ($coranCC) $line .= " ccCutoff=$coranCC";
			if ($coranmask) $line .= " coranmask=$coranmask";
			if ($coranlp) $line .= " lp=$coranlp";
			if ($coranhp) $line .= " hp=$coranhp";
			if ($eotest=='on') $line .= " eotest";
			$line .= " > coran".$i.".txt\n";
			if ($resfile_init) { 
				$line.= C_APPION_BIN."getRes.pl $i $box $apix >> resolution.txt\n";
			} else {
				$line.= C_APPION_BIN."getRes.pl $i $box $apix >! resolution.txt\n";
				$resfile_init = true;
			}
			if ($amask1) {
				$line .= "volume threed.".$i."a.mrc $apix set=$xfiles\n";
				$line .= "mv threed.".$i."a.mrc threed.".$i."a.coran.mrc\n";
				$line .= "proc3d threed.".$i."a.coran.mrc threed.".$i."a.mrc automask2=$amask1,$amask2,$amask3\n";
			}
		}
		// if eotest specified with coran, don't do eotest here:
		elseif ($eotest=='on') {
			$line.="eotest proc=$procs pad=$pad";
			if ($mask) $line.=" mask=$mask";
			if ($imask) $line.=" imask=$imask";
			if ($sym) $line.=" sym=$sym";
			if ($hard) $line.=" hard=$hard";
			if ($classkeep) $line.=" classkeep=$classkeep";
			if ($classiter) $line.=" classiter=$classiter";
			if ($median=='on') $line.=" median";
			if ($refine=='on') $line.=" refine";
			$line.=" > eotest".$i.".txt\n";
			$line.="mv -v fsc.eotest fsc.eotest.".$i."\n";
			if ($resfile_init) { 
				$line.= C_APPION_BIN."getRes.pl $i $box $apix >> resolution.txt\n";
			} else {
				$line.= C_APPION_BIN."getRes.pl $i $box $apix >! resolution.txt\n";
				$resfile_init = true;
			}
		}
		if ($affprop=='on') {
			$line .="affPropSubClassify.py --mask=$mask --iter=$i";
			if ($sym) $line .= " --sym=$sym";
			if ($hard) $line .= " --hard=$hard";
			if ($affpropCC) $line .= " --cc-cut=$affpropCC";
			if ($affpropMP) $line .= " --minpart=$affpropMP";
			$line .= "\n";
		}
		$line.="rm -fv cls*.lst\n";
		$ejob.= $line;
	}

	### tar up files
	$ejob.= "\n";
	$ejob.= "tar -cvzf model.tar.gz threed.*a.mrc\n";
	$ejob.= "tar -cvzf results.tar.gz fsc* cls* refine.* particle.* "
		."classes.* classes_*.* proj.* sym.* .emanlog *txt *.job\n";

	### cluster specific info
	$clusterjob .= $clusterdata->cluster_job_file($ejob);

	if (!$extra) {
		echo $clusterdata->cluster_check_msg();
		echo "<p>";
	} else {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<form name='emanjob' method='POST' action='$formAction'>\n";
	echo "<input type='hidden' name='clustername' value='".C_NAME."'>\n";
	echo "<input type='hidden' name='cluster' value='".C_NAME."'>\n";
	echo "<input type='hidden' NAME='clusterpath' value='$clusterpath'>\n";
	echo "<input type='hidden' NAME='dmfpath' value='$dmfpath'>\n";
	echo "<input type='hidden' NAME='jobname' value='$jobname'>\n";
	echo "<input type='hidden' NAME='outdir' value='$outdir'>\n";
	echo "<input type='hidden' NAME='mem' value='$memneed'>\n";

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
	processing_footer();
	exit;
}

/*
******************************************
******************************************
******************************************
*/

function defaultReconValues ($box) {
	$rad = ($box/2)-2;
	$javafunc = "
  <script type='text/javascript'>
    function setDefaults(obj) {
      obj.ang1.value = '5.0';
      obj.mask1.value = '$rad';
      //obj.imask1.value = '';
      //obj.sym1.value = '';
      obj.hard1.value = '25';
      obj.classkeep1.value = '0.8';
      obj.classiter1.value = '8';
      //obj.filt3d1.value = '15.0';
      //obj.shrink1.value = '1';
      obj.median1.checked = false;
      obj.xfiles1.value = '';
      obj.euler21.checked = '';
      obj.phasecls1.checked = true;
      //obj.fscls1.checked = false;
      obj.refine1.checked = false;
      //obj.goodbad1.checked = false;
      //obj.perturb1.checked = false;
      obj.eotest1.checked = true;
      obj.coran1.checked = false;
      obj.affprop1.checked = false;
      obj.affpropCC1.value = '0.8';
      obj.affpropMP1.value = '500';
      return;
    }
  </SCRIPT>\n";
	return $javafunc;
};

?>
