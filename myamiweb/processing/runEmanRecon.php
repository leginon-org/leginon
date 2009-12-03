<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Eman Job for submission to a cluster
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

if ($_POST['write']) {
	$particle = new particledata();
	if (!$_POST['nodes']) jobForm("ERROR: No nodes specified, setting default=4");
	if (!$_POST['ppn']) jobForm("ERROR: No processors per node specified, setting default=4");
	if ($_POST['ppn'] > 4 && $_POST['clustername']=='garibaldi') jobForm("ERROR: Max processors per node is 4");
	if ($_POST['ppn'] > 8 && $_POST['clustername']=='guppy') jobForm("ERROR: Max processors per node is 4");
	if ($_POST['nodes'] > 10 && $_POST['clustername']=='guppy') jobForm("ERROR: Max nodes on guppy is 10");
	if (!$_POST['walltime']) jobForm("ERROR: No walltime specified, setting default=240");
	if ($_POST['walltime'] > 240) jobForm("ERROR: Max walltime is 240");
	if (!$_POST['cput']) jobForm("ERROR: No CPU time specified, setting default=240");
	if ($_POST['cput'] > 240) jobForm("ERROR: Max CPU time is 240");
	if (!$_POST['rprocs']) jobForm("ERROR: No reconstruction ppn specified, setting default=4");
	if ($_POST['rprocs'] > $_POST['ppn'])
	  jobForm("ERROR: Asking to reconstruct on more processors than available");
	if ($_POST['clustername']=='garibaldi') {
		if (!$_POST['dmfpath']) jobForm("ERROR: No DMF path specified");
		if (!$_POST['dmfmod']) jobForm("ERROR: No starting model");
		if (!$_POST['dmfstack']) jobForm("ERROR: No stack file");
	}
  	for ($i=1; $i<=$_POST['numiters']; $i++) {
		if (!$_POST['ang'.$i]) jobForm("ERROR: no angular increment set for iteration $i");
		if (!$_POST['mask'.$i]) jobForm("ERROR: no mask set for iteration $i");
		// if amask is used, then xfiles must also be used
		if ($_POST['amask1'.$i] || $_POST['amask2'.$i] || $_POST['amask3'.$i]) {
			if (!($_POST['amask1'.$i] && $_POST['amask2'.$i] && $_POST['amask3'.$i])) jobForm("ERROR: All 3 amask values of amask must be entered for iteration $i");
			if (!$_POST['xfiles'.$i]) jobForm ("ERROR: amask requires the use of xfiles for iteration $i");
		} 
	}
	// check that job file doesn't already exist
	$outdir = $_POST['outdir'];
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$outdir .= $_POST['jobname'];

	// jobname ends with .job
	$jobname = $_POST['jobname'];
	$jobname .= '.job';
	$exists = $particle->getJobFileFromPath($outdir,$jobname);
	//  if ($exists[0]) jobForm("ERROR: This job name already exists");
	writeJobFile();
}	

elseif ($_POST['submitstackmodel'] || $_POST['duplicate'] || $_POST['import']) {
	## make sure a stack and model were selected
	if (!$_POST['model']) stackModelForm("ERROR: no initial model selected");
	if (!$_POST['stackval']) stackModelForm("ERROR: no stack selected");

	// make sure that box sizes are the same
	// get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$stackbox = $stackinfo[2];
	// get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$modbox = $modelinfo[3];
	if ($stackbox != $modbox) stackModelForm("ERROR: model and stack must have same box size");
	jobForm();
}

elseif ($_POST['submitjob']) {
	$particle = new particledata();

	$expId = $_GET['expId'];

	$host =$_POST['clustername'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	if (!($user && $pass)) writeJobFile("<B>ERROR:</B> Enter a user name and password");

	$jobname=$_POST['jobname'];
	$outdir=$_POST['outdir'].$_POST['jobname'];
	if ($host=='garibaldi') {
		$dmfpath=$_POST['dmfpath'].$jobname;
	}
	$clusterpath=$_POST['clusterpath'].$jobname;
	$jobfile="$jobname.job";
	$tmpjobfile = "/tmp/$jobfile";
	
	$jobid=$particle->insertClusterJobData($host,$outdir,$dmfpath,$clusterpath,$jobfile,$expId,'recon',$user);

	// add header & job id to the beginning of the script
	// convert /\n's back to \n for the script
	$header = explode('|--|',$_POST['header']);
	$clusterjob = "## $jobname\n";
	foreach ($header as $l) $clusterjob.="$l\n";
	$clusterjob.= "updateAppionDB.py $jobid R\n\n";
	$clusterjob.= "# jobId: $jobid\n";
	$clusterlastline.= "updateAppionDB.py $jobid D\nexit\n\n";
	$f = file_get_contents($tmpjobfile);
	file_put_contents($tmpjobfile, $clusterjob . $f . $clusterlastline);

	processing_header("Eman Job Submitted","EMAN Job Submitted",$javafunc);
	echo "<TABLE WIDTH='600'>\n";

	// create appion directory & copy job file
	$cmd = "mkdir -p $outdir;\n";
	$cmd.= "cp $tmpjobfile $outdir/$jobfile;\n";
	exec_over_ssh($_SERVER['HTTP_HOST'], $user, $pass, $cmd, True);

	// if running on garibaldi:
	if ($host=='garibaldi') {
		// create directory on cluster and copy job file over
		$cmd = "mkdir -p $clusterpath;\n";
		$cmd .= "cp $outdir/$jobfile $clusterpath/$jobfile;\n";
		$jobnum = exec_over_ssh($host, $user, $pass, $cmd, True);
	}
	// if on guppy, clusterpath is same as outdir
	else $clusterpath=$outdir;

	echo "<tr><td>Appion Directory</td><td>$outdir</td></tr>\n";
	echo "<tr><td>Job File Name</td><td>$jobname.job</td></tr>\n";
  
	// submit job on host
	$cmd = "cd $clusterpath; qsub $jobname.job;\n";
	$jobnum = exec_over_ssh($host, $user, $pass, $cmd, True);
  
	$jobnum=trim($jobnum);
	$jobnum = ereg_replace('\.'.$host.'.*','',$jobnum);
	if (!is_numeric($jobnum)) {
		echo "</table><P>\n";
		echo "ERROR in job submission.  Check the cluster\n";
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
	echo "<p><a href='checkjobs.php?expId=$expId'>[Check Status of Jobs Associated with this Experiment]</a><p>\n";
	echo "<P><FONT COLOR='RED'>Do not hit 'reload' - it will re-submit job</FONT><P>\n";
	processing_footer(True, True);
	exit;
}

else stackModelForm();

function stackModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectFromExpId($expId);

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
			$symdata = $particle->getSymInfo($modeldata['REF|ApSymmetryData|symmetry']);
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
	processing_footer();
	exit;
}

function emanForm($extra=false) {
	// get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$box=$stackinfo[2];

	// get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$syminfo = explode(' ',$modelinfo[4]);
	$modsym=$syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	$numiters= ($_POST['numiters']) ? $_POST['numiters'] : 1;
	if ($_POST['duplicate']) {
		$numiters+=1;
		$j=$_POST['duplicate'];
	}
	else $j=$numiters;

	$javafunc .= defaultReconValues($box);
	$javafunc .= writeJavaPopupFunctions('eman');

	processing_header("Eman Job Generator","EMAN Job Generator",$javafunc);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo "<form name='emanjob' method='post' action='$formaction'><br />\n";
	echo "<table border='0' cellpadding='0' cellspacing='0' width='600'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td><B>Job Run Name:</B></td>
    <td><input type='text' NAME='jobname' VALUE='$jobname' SIZE=20></td></tr>
  <tr><td><B>Output Directory:</B></td>
    <td><input type='text' NAME='outdir' VALUE='$outdir' SIZE=50></td></tr>
  </table>\n";

	echo closeRoundBorder();
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<p>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";

	$bgcolor="#E8E8E8";
	$display_keys = array('copy','itn','ang','mask','imask','amask','sym','hard','clskeep','clsiter','filt3d','xfiles','shrink','euler2','median','phscls','fscls','refine','perturb','goodbad','tree','coran','eotest','copy');  
	echo"
  <br />
  <H4 style='align=\'center\' >EMAN Reconstruction Parameters</H4>
  <hr />
	";

	// import values from previous uploaded reconstruction
	$projectId=getProjectFromExpId($expId);
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
	if (is_numeric($_POST['import'])) {
		$iterinfo = $particle->getIterationInfo($_POST['import']);
		// get initial model info
		$refinfo = $particle->getRefinementRunInfo($_POST['import']);
		$initmodel = $particle->getInitModelInfo($refinfo['REF|ApInitialModelData|initialModel']);
		// get scaling factor for box sizes
		$boxscale = $box / $initmodel['boxsize'];
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
		$hardn="hard".$i;
		$classkeepn="classkeep".$i;
		$classitern="classiter".$i;
		$filt3dn="filt3d".$i;
		$shrinkn="shrink".$i;
		$euler2n="euler2".$i;
		$xfilesn="xfiles".$i;
		$perturbn="perturb".$i;
		$treen="tree".$i;
		$mediann="median".$i;
		$phaseclsn="phasecls".$i;
		$fsclsn="fscls".$i;
		$refinen="refine".$i;
		$goodbadn="goodbad".$i;
		$eotestn="eotest".$i;
		$corann="coran".$i;
		$msgpn="msgp".$i;
		$msgp_corcutoffn="msgp_corcutoff".$i;
		$msgp_minptclsn="msgp_minptcls".$i;

		// if importing values, set them here
		if (is_numeric($_POST['import'])) {
			foreach ($iterinfo as $iter) {
				if ($iter['iteration'] == $i) {
					$ang=$iter['ang'];
					$mask=ceil($boxscale*$iter['mask']);
					$imask=$iter['imask'];
					$amask1=$iter['EMAN_amask1'];
					$amask2=$iter['EMAN_amask2'];
					$amask3=$iter['EMAN_amask3'];
					$hard=$iter['EMAN_hard'];
					$classiter=$iter['EMAN_classiter'];
					$classkeep=$iter['EMAN_classkeep'];
					$filt3d=$iter['EMAN_filt3d'];
					$shrink=$iter['EMAN_shrink'];
					$euler2=$iter['EMAN_euler2'];
					$xfiles=$iter['EMAN_xfiles'];
					$median = ($iter['EMAN_median']) ? 'CHECKED' : '';
					$phasecls = ($iter['EMAN_phasecls']) ? 'CHECKED' : '';
					$fscls = ($iter['EMAN_fscls']) ? 'CHECKED' : '';
					$refine = ($iter['EMAN_refine']) ? 'CHECKED' : '';
					$goodbad = ($iter['EMAN_goodbad']) ? 'CHECKED' : '';
					$coran = ($iter['SpiCoranGoodClassAvg']) ? 'CHECKED' : '';
					$perturb = ($iter['EMAN_perturb']) ? 'CHECKED' : '';
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
			$hard=($i>$j) ? $_POST["hard".($i-1)] : $_POST[$hardn];
			$classkeep=($i>$j) ? $_POST["classkeep".($i-1)] : $_POST[$classkeepn];
			$classiter=($i>$j) ? $_POST["classiter".($i-1)] : $_POST[$classitern];
			$filt3d=($i>$j) ? $_POST["filt3d".($i-1)] : $_POST[$filt3dn];
			$shrink=($i>$j) ? $_POST["shrink".($i-1)] : $_POST[$shrinkn];
			$euler2=($i>$j) ? $_POST["euler2".($i-1)] : $_POST[$euler2n];
			$xfiles=($i>$j) ? $_POST["xfiles".($i-1)] : $_POST[$xfilesn];
			$msgp_corcutoff=($i>$j) ? $_POST["msgp_corcutoff".($i-1)] : $_POST[$msgp_corcutoffn];
			$msgp_minptcls=($i>$j) ? $_POST["msgp_minptcls".($i-1)] : $_POST[$msgp_minptclsn];
			// use symmetry of model by default, but you can change it
			if ($i==1 && !$_POST['duplicate']) $sym=$modsym;
			
			if ($i>$j) {
				$median=($_POST["median".($i-1)]=='on') ? 'CHECKED' : '';
				$phasecls=($_POST["phasecls".($i-1)]=='on') ? 'CHECKED' : '';
				$fscls=($_POST["fscls".($i-1)]=='on') ? 'CHECKED' : '';
				$refine=($_POST["refine".($i-1)]=='on') ? 'CHECKED' : '';
				$goodbad=($_POST["goodbad".($i-1)]=='on') ? 'CHECKED' : '';
				$eotest=($_POST["eotest".($i-1)]=='on') ? 'CHECKED' : '';
				$coran=($_POST["coran".($i-1)]=='on') ? 'CHECKED' : '';
				$perturb=($_POST["perturb".($i-1)]=='on') ? 'CHECKED' : '';
				$msgp=($_POST["msgp".($i-1)]=='on') ? 'CHECKED' : '';
				$treetwo=($_POST["tree".($i-1)]=='2') ? 'selected' : '';
				$treethree=($_POST["tree".($i-1)]=='3') ? 'selected' : '';
			}
			else {
				$median=($_POST[$mediann]=='on') ? 'CHECKED' : '';
				$phasecls=($_POST[$phaseclsn]=='on') ? 'CHECKED' : '';
				$fscls=($_POST[$fsclsn]=='on') ? 'CHECKED' : '';
				$refine=($_POST[$refinen]=='on') ? 'CHECKED' : '';
				$goodbad=($_POST[$goodbadn]=='on') ? 'CHECKED' : '';
				$eotest=($_POST[$eotestn]=='on') ? 'CHECKED' : '';
				$coran=($_POST[$corann]=='on') ? 'CHECKED' : '';
				$perturb=($_POST[$perturbn]=='on') ? 'CHECKED' : '';
				$msgp=($_POST[$msgpn]=='on') ? 'CHECKED' : '';
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
        <td bgcolor='$rcol'><input type='text' NAME='$hardn' SIZE='3' VALUE='$hard'></td>
        <td bgcolor='$rcol'><input type='text' NAME='$classkeepn' SIZE='4' VALUE='$classkeep'></td>
        <td bgcolor='$rcol'><input type='text' NAME='$classitern' SIZE='2' VALUE='$classiter'></td>
        <td bgcolor='$rcol'><input type='text' NAME='$filt3dn' SIZE='4' VALUE='$filt3d'></td>
        <td bgcolor='$rcol'><input type='text' size='5' name='$xfilesn' value='$xfiles'>
        <td bgcolor='$rcol'><input type='text' NAME='$shrinkn' SIZE='2' VALUE='$shrink'></td>
        <td bgcolor='$rcol'><input type='text' size='2' name='$euler2n' value='$euler2'>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$mediann' $median></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$phaseclsn' $phasecls></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$fsclsn' $fscls></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$refinen' $refine></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$perturbn' $perturb></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$goodbadn' $goodbad></td>
        <td bgcolor='$rcol'><select name='$treen'><option>-</option><option $treetwo>2</option><option $treethree>3</option></select></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$corann' $coran></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$eotestn' $eotest></td>
        <td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i' onclick='emanjob.submit()'></td>
      </tr>\n";
	}
	echo"
  </table>
  <input type='hidden' NAME='numiters' VALUE='$numiters'><P>
  <input type='SUBMIT' NAME='write' VALUE='Create Job File'>
  </FORM>\n";
	if ($guppycheck) echo "<script language='javascript'>enableGaribaldi('false')</script>\n";
	processing_footer();
	exit;
}

function jobForm($extra=false) {
	$expId = $_GET['expId'];

	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = $sessiondata['Image path'];
	$sessionpath = ereg_replace("leginon","appion",$sessionpath);
	$sessionpath = ereg_replace("rawdata","recon/",$sessionpath);

	$particle = new particledata();
	$reconruns = count($particle->getJobIdsFromSession($expId));
	$defrunid = 'recon'.($reconruns+1);

	// get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$dmfstack = $stackinfo[4];
	$box=$stackinfo[2];
	$rootpathdata = explode('/', $sessionpath);
	$dmfpath = '/home/'.$_SESSION['username'].'/';
	$clusterpath = '~'.$_SESSION['username'].'/';
	for ($i=3 ; $i<count($rootpathdata); $i++) {
		$rootpath .= "$rootpathdata[$i]";
		if ($i+1<count($rootpathdata)) $rootpath.='/';
	}
  
	$dmfpath .= $rootpath;
	$clusterpath .= $rootpath;

	// get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$dmfmod = $modelinfo[2];
	$syminfo = explode(' ',$modelinfo[4]);
	$modsym=$syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	// garibaldi is selected by default
	$garibaldicheck = ($_POST['clustername']=='garibaldi' || $_POST['model']) ? 'CHECKED' : '';
	$guppycheck = ($_POST['clustername']=='guppy') ? 'CHECKED' : '';

	$jobname = ($_POST['jobname']) ? $_POST['jobname'] : $defrunid;
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$clusterpath = ($_POST['clusterpath']) ? $_POST['clusterpath'] : $clusterpath;
	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : 4;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : 4;
	$rprocs = ($_POST['rprocs']) ? $_POST['rprocs'] : 4;
	$walltime = ($_POST['walltime']) ? $_POST['walltime'] : 240;
	$cput = ($_POST['cput']) ? $_POST['cput'] : 240;
	$dmfstack = ($_POST['dmfstack']) ? $_POST['dmfstack'] : $dmfstack;
	$dmfpath = ($_POST['dmfpath']) ? $_POST['dmfpath'] : $dmfpath;
	$dmfmod = ($_POST['dmfmod']) ? $_POST['dmfmod'] : $dmfmod;
	$dmfstorech = ($_POST['dmfstore']=='on' || $_POST['model']) ? 'CHECKED' : '';
	$numiters= ($_POST['numiters']) ? $_POST['numiters'] : 1;
	if ($_POST['duplicate']) {
		$numiters+=1;
		$j=$_POST['duplicate'];
	}
	else $j=$numiters;

	$javafunc .= defaultReconValues($box);
	$javafunc .= writeJavaPopupFunctions('eman');
	$javafunc .= garibaldiFun();
	processing_header("Eman Job Generator","EMAN Job Generator",$javafunc);
	// write out errors, if any came up:
	if (!($user && $pass)) echo "<font color='red'><B>WARNING!!!</B> You are not logged in!!!</font><br />";
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<form name='emanjob' method='post' action='$formaction'><br />\n";
	echo "<table border='0' cellpadding='0' cellspacing='0' width='600'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>
    <td rowspan='2'><b>Cluster:</b></td>
    <td><input type='radio' name='clustername' value='garibaldi' onClick=\"enableGaribaldi('true')\" $garibaldicheck>Garibaldi</td></tr>
    <tr><td><input type='radio' name='clustername' value='guppy' onClick=\"enableGaribaldi('false')\" $guppycheck>Guppy</td>
  </tr>
  <tr>
    <td><B>Job Run Name:</B></td>
    <td><input type='text' NAME='jobname' VALUE='$jobname' SIZE=20></td>
  </tr>
  <tr>
    <td><B>Output Directory:</B></td>
    <td><input type='text' NAME='outdir' VALUE='$outdir' SIZE=50></td>
  </tr>
  <tr>
    <td><B>Cluster Directory:</B></td>
    <td><input type='text' NAME='clusterpath' VALUE='$clusterpath' SIZE=50></td>
  </tr>
  </table>\n";
	echo closeRoundBorder();
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<p>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";

	//overall PBS & DMF tables
	echo "<table border='0'><tr><td valign='top'>"; 

	//Cluster Parameters
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
      <TD COLSPAN='4'>
      Reconstruction procs per node:<input type='text' NAME='rprocs' VALUE='$rprocs' SIZE='3'>
      </td>
    </tr>
    </table>\n";
	echo closeRoundBorder();

	echo"</td><td valign='top'>"; //overall table

	//DMF Parameters TABLE
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>
      <TD COLSPAN='4' ALIGN='CENTER'>
      <H4>DMF Parameters</H4>
      </td>
    </tr>
    <tr>
      <td>DMF Directory:</td>
      <td><input type='text' NAME='dmfpath' VALUE='$dmfpath' SIZE='40' ></td>
    </tr>
    <tr>
      <td>Starting Model (mrc):</td>
      <td><input type='text' NAME='dmfmod' VALUE='$dmfmod' SIZE='40' ></td>
    </tr>
    <tr>
      <td>Stack (img or hed):</td>
      <td><input type='text' NAME='dmfstack' VALUE='$dmfstack' SIZE='40' ></td>
    </tr>
    <tr>
      <td>Save results to DMF</td>
      <td><input type='checkbox' NAME='dmfstore' $dmfstorech></td>
    </tr>
    </table>\n";
	echo closeRoundBorder();
	echo"</td></tr></table>"; //overall table
	$bgcolor="#E8E8E8";
	$display_keys = array('copy','itn','ang','mask','imask','amask','sym','hard','clskeep','clsiter','filt3d','xfiles','shrink','euler2','median','phscls','fscls','refine','perturb','goodbad','tree','coran','eotest','copy');  
	echo"
  <br />
  <H4 style='align=\'center\' >EMAN Reconstruction Parameters</H4>
  <hr />
	";

	// import values from previous uploaded reconstruction
	$projectId=getProjectFromExpId($expId);
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
	elseif (is_numeric($_POST['import'])) {
		$iterinfo = $particle->getIterationInfo($_POST['import']);
		// get initial model info
		$refinfo = $particle->getRefinementRunInfo($_POST['import']);
		$initmodel = $particle->getInitModelInfo($refinfo['REF|ApInitialModelData|initialModel']);
		// get scaling factor for box sizes
		$boxscale = $box / $initmodel['boxsize'];
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
		$hardn="hard".$i;
		$classkeepn="classkeep".$i;
		$classitern="classiter".$i;
		$filt3dn="filt3d".$i;
		$shrinkn="shrink".$i;
		$euler2n="euler2".$i;
		$xfilesn="xfiles".$i;
		$perturbn="perturb".$i;
		$treen="tree".$i;
		$mediann="median".$i;
		$phaseclsn="phasecls".$i;
		$fsclsn="fscls".$i;
		$refinen="refine".$i;
		$goodbadn="goodbad".$i;
		$eotestn="eotest".$i;
		$corann="coran".$i;
		$msgpn="msgp".$i;
		$msgp_corcutoffn="msgp_corcutoff".$i;
		$msgp_minptclsn="msgp_minptcls".$i;

		// if importing values, set them here
		if ($_POST['import']=='groel1') {
			// values that don't change:
			$mask = $_POST['mask1'] ? $_POST['mask1'] : ($box/2)-2;
			$hard='25';
			$classkeep='0.8';
			$median = $_POST['median1']=='on' ? 'CHECKED' : '';
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
			$median='CHECKED';
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
		elseif (is_numeric($_POST['import'])) {
			foreach ($iterinfo as $iter) {
				if ($iter['iteration'] == $i) {
					$ang=$iter['ang'];
					$mask=ceil($boxscale*$iter['mask']);
					$imask=$iter['imask'];
					$amask1=$iter['EMAN_amask1'];
					$amask2=$iter['EMAN_amask2'];
					$amask3=$iter['EMAN_amask3'];
					$hard=$iter['EMAN_hard'];
					$classiter=$iter['EMAN_classiter'];
					$classkeep=$iter['EMAN_classkeep'];
					$filt3d=$iter['EMAN_filt3d'];
					$shrink=$iter['EMAN_shrink'];
					$euler2=$iter['EMAN_euler2'];
					$xfiles=$iter['EMAN_xfiles'];
					$median = ($iter['EMAN_median']) ? 'CHECKED' : '';
					$phasecls = ($iter['EMAN_phasecls']) ? 'CHECKED' : '';
					$fscls = ($iter['EMAN_fscls']) ? 'CHECKED' : '';
					$refine = ($iter['EMAN_refine']) ? 'CHECKED' : '';
					$goodbad = ($iter['EMAN_goodbad']) ? 'CHECKED' : '';
					$coran = ($iter['SpiCoranGoodClassAvg']) ? 'CHECKED' : '';
					$perturb = ($iter['EMAN_perturb']) ? 'CHECKED' : '';
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
			$hard=($i>$j) ? $_POST["hard".($i-1)] : $_POST[$hardn];
			$classkeep=($i>$j) ? $_POST["classkeep".($i-1)] : $_POST[$classkeepn];
			$classiter=($i>$j) ? $_POST["classiter".($i-1)] : $_POST[$classitern];
			$filt3d=($i>$j) ? $_POST["filt3d".($i-1)] : $_POST[$filt3dn];
			$shrink=($i>$j) ? $_POST["shrink".($i-1)] : $_POST[$shrinkn];
			$euler2=($i>$j) ? $_POST["euler2".($i-1)] : $_POST[$euler2n];
			$xfiles=($i>$j) ? $_POST["xfiles".($i-1)] : $_POST[$xfilesn];
			$msgp_corcutoff=($i>$j) ? $_POST["msgp_corcutoff".($i-1)] : $_POST[$msgp_corcutoffn];
			$msgp_minptcls=($i>$j) ? $_POST["msgp_minptcls".($i-1)] : $_POST[$msgp_minptclsn];
			// use symmetry of model by default, but you can change it
			if ($i==1 && !$_POST['duplicate']) $sym=$modsym;
			
			if ($i>$j) {
				$median=($_POST["median".($i-1)]=='on') ? 'CHECKED' : '';
				$phasecls=($_POST["phasecls".($i-1)]=='on') ? 'CHECKED' : '';
				$fscls=($_POST["fscls".($i-1)]=='on') ? 'CHECKED' : '';
				$refine=($_POST["refine".($i-1)]=='on') ? 'CHECKED' : '';
				$goodbad=($_POST["goodbad".($i-1)]=='on') ? 'CHECKED' : '';
				$eotest=($_POST["eotest".($i-1)]=='on') ? 'CHECKED' : '';
				$coran=($_POST["coran".($i-1)]=='on') ? 'CHECKED' : '';
				$perturb=($_POST["perturb".($i-1)]=='on') ? 'CHECKED' : '';
				$msgp=($_POST["msgp".($i-1)]=='on') ? 'CHECKED' : '';
				$treetwo=($_POST["tree".($i-1)]=='2') ? 'selected' : '';
				$treethree=($_POST["tree".($i-1)]=='3') ? 'selected' : '';
			}
			else {
				$median=($_POST[$mediann]=='on') ? 'CHECKED' : '';
				$phasecls=($_POST[$phaseclsn]=='on') ? 'CHECKED' : '';
				$fscls=($_POST[$fsclsn]=='on') ? 'CHECKED' : '';
				$refine=($_POST[$refinen]=='on') ? 'CHECKED' : '';
				$goodbad=($_POST[$goodbadn]=='on') ? 'CHECKED' : '';
				$eotest=($_POST[$eotestn]=='on') ? 'CHECKED' : '';
				$coran=($_POST[$corann]=='on') ? 'CHECKED' : '';
				$perturb=($_POST[$perturbn]=='on') ? 'CHECKED' : '';
				$msgp=($_POST[$msgpn]=='on') ? 'CHECKED' : '';
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
        <td bgcolor='$rcol'><input type='text' NAME='$hardn' SIZE='3' VALUE='$hard'></td>
        <td bgcolor='$rcol'><input type='text' NAME='$classkeepn' SIZE='4' VALUE='$classkeep'></td>
        <td bgcolor='$rcol'><input type='text' NAME='$classitern' SIZE='2' VALUE='$classiter'></td>
        <td bgcolor='$rcol'><input type='text' NAME='$filt3dn' SIZE='4' VALUE='$filt3d'></td>
        <td bgcolor='$rcol'><input type='text' size='5' name='$xfilesn' value='$xfiles'>
        <td bgcolor='$rcol'><input type='text' NAME='$shrinkn' SIZE='2' VALUE='$shrink'></td>
        <td bgcolor='$rcol'><input type='text' size='2' name='$euler2n' value='$euler2'>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$mediann' $median></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$phaseclsn' $phasecls></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$fsclsn' $fscls></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$refinen' $refine></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$perturbn' $perturb></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$goodbadn' $goodbad></td>
        <td bgcolor='$rcol'><select name='$treen'><option>-</option><option $treetwo>2</option><option $treethree>3</option></select></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$corann' $coran></td>
        <td bgcolor='$rcol'><input type='checkbox' NAME='$eotestn' $eotest></td>
        <td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i' onclick='emanjob.submit()'></td>
      </tr>\n";


### commented out for now, since  not working properly
#	<TD colspan=6 bgcolor='$bgcolor' CELLPADDING=0 CELLSPACING=0>
#	  <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4 WIDTH=100%>
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
  </FORM>\n";
	if ($guppycheck) echo "<script language='javascript'>enableGaribaldi('false')</script>\n";
	processing_footer();
	exit;
}

function writeJobFile ($extra=False) {
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$jobname = $_POST['jobname'];
	$jobfile ="$jobname.job";

	$clustername = $_POST['clustername'];
	$outdir = $_POST['outdir'];
	if (substr($outdir,-1,1)!='/') $outdir.='/';

	// clusterpath contains jobname, if running on guppy, cluster path is local
	$clusterpath = ($clustername=='guppy') ? $outdir : $_POST['clusterpath'];
	if (substr($clusterpath,-1,1)!='/') $clusterpath.='/';
	$clusterfullpath = $clusterpath.$jobname;

	// make sure dmf store dir ends with '/'
	$dmfpath=$_POST['dmfpath'];
	if (substr($dmfpath,-1,1)!='/') $dmfpath.='/';
	$dmffullpath = $dmfpath.$jobname;

	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
	$stackpath=$stackinfo[3];
	$stackname1=$stackinfo[4];
	$stackname2=$stackinfo[5];

	// get the model id
	$modelinfo=explode('|--|',$_POST['model']);
	$modelid=$modelinfo[0];
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];

	// insert the job file into the database
	if (!$extra) {
		// create dmf put javascript
		$javafunc.="
  <SCRIPT LANGUAGE='JavaScript'>
  function displayDMF() {
    newwindow=window.open('','name','height=150, width=900')
    newwindow.document.write('<HTML><BODY>')
    newwindow.document.write('dmf mkdir -p $dmffullpath');
    newwindow.document.write('<P>dmf put $stackpath/$stackname1 $dmffullpath/$stackname1')\n";
		if ($stackname2) $javafunc.="    newwindow.document.write('<P>dmf put $stackpath/$stackname2 $dmffullpath/$stackname2')\n";
		$javafunc.="
    newwindow.document.write('<P>dmf put $modelpath/$modelname $dmffullpath/$modelname');
    newwindow.document.write('<P>echo done');
    newwindow.document.write('<P>&nbsp;<br></BODY></HTML>');
    newwindow.document.close();
  }
  </SCRIPT>\n";
	}
	processing_header("Eman Job Generator","EMAN Job Generator", $javafunc);

	$header.= "#PBS -l nodes=".$_POST['nodes'].":ppn=".$_POST['ppn']."\n";
	$header.= "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
	$header.= "#PBS -l cput=".$_POST['cput'].":00:00\n";
	$header.= "#PBS -m e\n";
	$header.= "#PBS -r n\n\n";
	$header.= "#PBS -j oe\n";
	$clusterjob = "# stackId: $stackidval\n";
	$clusterjob.= "# modelId: $modelid\n\n";
	
	if ($clustername=='garibaldi') {
		$clusterjob.= "mkdir -p $clusterfullpath\n";
		$clusterjob.= "cd $clusterfullpath\n";
		$clusterjob.= "rm -f recon\n";
		$clusterjob.= "ln -s \$PBSREMOTEDIR recon\n";
		$clusterjob.= "chmod 755 recon\n"; 
		$clusterjob.= "cd recon\n";
		// get file name, strip extension
		$ext=strrchr($_POST['dmfstack'],'.');
		$stackname=substr($_POST['dmfstack'],0,-strlen($ext));
		$clusterjob.= "\ndmf get $dmffullpath/".$_POST['dmfmod']." threed.0a.mrc\n";
		$clusterjob.= "dmf get $dmffullpath/$stackname.hed start.hed\n";
		$clusterjob.= "dmf get $dmffullpath/$stackname.img start.img\n";
		$clusterjob.= "setenv RUNPAR_RSH 'rsh'\n\n";
	}
	else {
		$clusterjob.= "rm -rf $clusterfullpath/recon\n";
		$clusterjob.= "mkdir -p $clusterfullpath/recon\n";
		$clusterjob.= "cd $clusterfullpath/recon\n\n";
		$ext=strrchr($stackname1,'.');
		$stackname=substr($stackname1,0,-strlen($ext));
		$clusterjob.= "ln -s $stackpath/$stackname.hed start.hed\n";
		$clusterjob.= "ln -s $stackpath/$stackname.img start.img\n";
		$clusterjob.= "ln -s $modelpath/$modelname threed.0a.mrc\n";
		$clusterjob.= "setenv RUNPAR_RSH 'ssh'\n\n";
	}
	$procs=$_POST['nodes']*$_POST['rprocs'];
	$numiters=$_POST['numiters'];
	$pad=intval($box*1.25);
	// make sure $pad value is even int
	$pad = ($pad%2==1) ? $pad+=1 : $pad;
	for ($i=1; $i<=$numiters; $i++) {
		$ang=$_POST["ang".$i];
		$mask=$_POST["mask".$i];
		$imask=$_POST["imask".$i];
		$amask1=$_POST["amask1".$i];
		$amask2=$_POST["amask2".$i];
		$amask3=$_POST["amask3".$i];
		$sym=$_POST["sym".$i];
		$hard=$_POST["hard".$i];
		$classkeep=$_POST["classkeep".$i];
		$classiter=$_POST["classiter".$i];
		$filt3d=$_POST["filt3d".$i];
		$shrink=$_POST["shrink".$i];
		$euler2=$_POST["euler2".$i];
		$xfiles=$_POST["xfiles".$i];
		$perturb=$_POST["perturb".$i];
		$tree=$_POST["tree".$i];
		$median=$_POST["median".$i];
		$phasecls=$_POST["phasecls".$i];
		$fscls=$_POST["fscls".$i];
		$refine=$_POST["refine".$i];
		$goodbad=$_POST["goodbad".$i];
		$eotest=$_POST["eotest".$i];
		$coran=$_POST["coran".$i];
		$msgp=$_POST["msgp".$i];
		$msgp_corcutoff=$_POST["msgp_corcutoff".$i];
		$msgp_minptcls=$_POST["msgp_minptcls".$i];
		$line="\nrefine $i proc=$procs ang=$ang pad=$pad";
		if ($mask) $line.=" mask=$mask";
		if ($imask) $line.=" imask=$imask";
		if ($amask1) $line.=" amask=$amask1,$amask2,$amask3";
		if ($sym) $line.=" sym=$sym";
		if ($hard) $line.=" hard=$hard";
		if ($classkeep) $line.=" classkeep=$classkeep";
		if ($classiter) $line.=" classiter=$classiter";
		if ($filt3d) $line.=" filt3d=$filt3d";
		if ($shrink) $line.=" shrink=$shrink";
		if ($xfiles) $line.=" xfiles=$apix,$xfiles,99";
		if ($median=='on') $line.=" median";
		if ($perturb=='on') $line.=" perturb";
		if ($tree=='2' || $tree=='3') $line.=" tree=$tree";
		if ($fscls=='on') $line.=" fscls";
		if ($phasecls=='on') $line.=" phasecls";
		if ($refine=='on') $line.=" refine";
		if ($euler2) $line.=" euler2=$euler2";
		if ($goodbad=='on') $line.=" goodbad";
		$line.=" > refine".$i.".txt\n";
		$line.="mv classes.".$i.".hed classes_eman.".$i.".hed\n";
		$line.="ln -s classes_eman.".$i.".hed classes.".$i.".hed\n";
		$line.="mv classes.".$i.".img classes_eman.".$i.".img\n";
		$line.="ln -s classes_eman.".$i.".img classes.".$i.".img\n";
		$line.="getProjEulers.py proj.img proj.$i.txt\n";
		// if ref-free correllation analysis
		if ($coran=='on') {
			$line .= "coran_for_cls.py mask=$mask proc=$procs iter=$i";
			if ($sym) $line .= " sym=$sym";
			if ($hard) $line .= " hard=$hard";
			if ($eotest=='on') $line .= " eotest";
			$line .= " > coran".$i.".txt\n";
			$line.= "getRes.pl >> resolution.txt $i $box $apix\n";
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
			$line.="mv fsc.eotest fsc.eotest.".$i."\n";
			$line.= "getRes.pl >> resolution.txt $i $box $apix\n";
		}
		if ($msgp=='on') {
			$line .="msgPassing_subClassification.py mask=$mask iter=$i";
			if ($sym) $line .= " sym=$sym";
			if ($hard) $line .= " hard=$hard";
			if ($msgp_corcutoff) $line .= " corCutOff=$msgp_corcutoff";
			if ($msgp_minptcls) $line .= " minNumOfPtcls=$msgp_minptcls";
			$line .= "\n";
		}
		$line.="rm cls*.lst\n";
		$clusterjob.= $line;
	}
	
	
	if ($clustername=='garibaldi') {
		$clusterjob.= "\ncp $clusterfullpath/$jobname.job .\n";
		if ($_POST['dmfstore']=='on') {
			$clusterjob.= "\ntar -cvzf model.tar.gz threed.*a.mrc\n";
			$clusterjob.= "dmf put model.tar.gz $dmffullpath\n";
			$line = "\ntar -cvzf results.tar.gz fsc* cls* refine.* particle.* classes.* classes_*.* proj.* sym.* .emanlog *txt *.job";
			if ($msgp=='on') {
				$line .= "goodavgs.* ";
				$clusterjob.= "dmf put msgPassing.tar $dmffullpath\n";
			}
			$line .= "\n";
			$clusterjob.= $line;
			$clusterjob.= "dmf put results.tar.gz $dmffullpath\n";
		}
	}
	else {
		$clusterjob.= "\nmv $clusterfullpath/recon/* $clusterfullpath/.\n";
		$clusterjob.= "\nmv $clusterfullpath/recon/.* $clusterfullpath/.\n";
		$clusterjob.= "\nrm -rf $clusterfullpath/recon\n";
	}
	if (!$extra) {
		if ($clustername=='garibaldi') {
			echo "Please review your job below.<br>";
			echo "If you are satisfied:<br>\n";
			echo "1) Place files in DMF<br>\n";
			echo "2) Once this is done, click the button to launch your job.<br>\n";
			echo"<input type='button' NAME='dmfput' VALUE='Put files in DMF' onclick='displayDMF()'><P>\n";
			echo"<input type='hidden' NAME='dmfpath' VALUE=''>\n";
		}
		else echo "Review your job, and submit.<br />\n";
	}
	else {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<FORM NAME='emanjob' METHOD='POST' ACTION='$formAction'><br>\n";
	echo "<input type='hidden' name='clustername' value='$clustername'>\n";
	echo "<input type='HIDDEN' NAME='clusterpath' VALUE='$clusterpath'>\n";
	echo "<input type='HIDDEN' NAME='dmfpath' VALUE='$dmfpath'>\n";
	echo "<input type='HIDDEN' NAME='jobname' VALUE='$jobname'>\n";
	echo "<input type='HIDDEN' NAME='outdir' VALUE='$outdir'>\n";
	// convert \n to /\n's for script
	$header_conv=preg_replace('/\n/','|--|',$header);
	echo "<input type='HIDDEN' NAME='header' VALUE='$header_conv'>\n";
	echo "<input type='SUBMIT' NAME='submitjob' VALUE='Submit Job to Cluster'>\n";
	if (!$extra) {
		echo "<HR>\n";
		echo "<PRE>\n";
		echo $header;
		echo $clusterjob;
		echo "</PRE>\n";
		$tmpfile = "/tmp/$jobfile";
		// write file to tmp directory
		$f = fopen($tmpfile,'w');
		fwrite($f,$clusterjob);
		fclose($f);
	}	
	processing_footer();
	exit;
};

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
      obj.fscls1.checked = false;
      obj.refine1.checked = false;
      obj.goodbad1.checked = false;
      obj.perturb1.checked = false;
      obj.eotest1.checked = true;
      obj.coran1.checked = false;
      obj.msgp1.checked = false;
      obj.msgp_corcutoff1.value = '0.8';
      obj.msgp_minptcls1.value = '500';
      return;
    }
  </SCRIPT>\n";
	return $javafunc;
};

function garibaldiFun() {
	$javafunc="
  <script language='javascript'>
  function enableGaribaldi(i) {
    if (i=='true') {
      document.emanjob.clusterpath.disabled=false;
      document.emanjob.dmfpath.disabled=false;
      document.emanjob.dmfmod.disabled=false;
      document.emanjob.dmfstack.disabled=false;
      document.emanjob.dmfstore.disabled=false;
      document.emanjob.nodes.value=4;
      document.emanjob.ppn.value=4;
      document.emanjob.rprocs.value=4;
    }
    else {
      document.emanjob.clusterpath.disabled=true;
      document.emanjob.dmfpath.disabled=true;
      document.emanjob.dmfmod.disabled=true;
      document.emanjob.dmfstack.disabled=true;
      document.emanjob.dmfstore.disabled=true;
      document.emanjob.nodes.value=2;
      document.emanjob.ppn.value=8;
      document.emanjob.rprocs.value=8;
    }
  }
  </script>\n";
	return $javafunc;
}
