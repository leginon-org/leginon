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
  if ($_POST['ppn'] > 4) jobForm("ERROR: Max processors per node is 4");
  if (!$_POST['walltime']) jobForm("ERROR: No walltime specified, setting default=240");
  if ($_POST['walltime'] > 240) jobForm("ERROR: Max walltime is 240");
  if (!$_POST['cput']) jobForm("ERROR: No CPU time specified, setting default=240");
  if ($_POST['cput'] > 240) jobForm("ERROR: Max CPU time is 240");
  if (!$_POST['rprocs']) jobForm("ERROR: No reconstruction ppn specified, setting default=4");
  if ($_POST['rprocs'] > $_POST['ppn'])
    jobForm("ERROR: Asking to reconstruct on more processors than available");
  if (!$_POST['dmfpath']) jobForm("ERROR: No DMF path specified");
  if (!$_POST['dmfmod']) jobForm("ERROR: No starting model");
  if (!$_POST['dmfstack']) jobForm("ERROR: No stack file");
  for ($i=1; $i<=$_POST['numiters']; $i++) {
    if (!$_POST['ang'.$i]) jobForm("ERROR: no angular increment set for iteration $i");
    if (!$_POST['mask'.$i]) jobForm("ERROR: no mask set for iteration $i");
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

  ## make sure that box sizes are the same
  ## get stack data
  $stackinfo = explode('|--|',$_POST['stackval']);
  $stackbox = $stackinfo[2];
  ## get model data
  $modelinfo = explode('|--|',$_POST['model']);
  $modbox = $modelinfo[3];
  if ($stackbox != $modbox) stackModelForm("ERROR: model and stack must have same box size");
  jobForm();
}

elseif ($_POST['submitjob']) {
  $particle = new particledata();

  $expId = $_GET['expId'];

  $host = PROCESSING_HOST;
  $user = $_SESSION['username'];
  $pass = $_SESSION['password'];
  if (!($user && $pass)) writeJobFile("<B>ERROR:</B> Enter a user name and password");

  $jobname=$_POST['jobname'];
  $outdir=$_POST['outdir'].$jobname;
  $dmfpath=$_POST['dmfpath'].$jobname;
  $clusterpath=$_POST['clusterpath'].$jobname;

  $jobfile="$jobname.job";
  $tmpjobfile = "/tmp/$jobfile";

  $jobid=$particle->insertClusterJobData($outdir,$dmfpath,$clusterpath,$jobfile,$expId);

  // add header & job id to the beginning of the script
  // convert /\n's back to \n for the script
  $header = explode('|--|',$_POST['header']);
  $clusterjob = "## $jobname\n";
  foreach ($header as $l) $clusterjob.="$l\n";
  $clusterjob.= "\nupdateAppionDB.py $jobid R\n\n";
  $clusterjob.= "# jobId: $jobid\n";
  $clusterlastline.= "updateAppionDB.py $jobid D\nexit\n\n";
  $f = file_get_contents($tmpjobfile);
  file_put_contents($tmpjobfile, $clusterjob . $f . $clusterlastline);

  writeTop("Eman Job Submitted","EMAN Job Submitted",$javafunc);
  echo "<TABLE WIDTH='600'>\n";

  // create appion directory & copy job file
  $cmd = "mkdir -p $outdir;\n";
  $cmd.= "cp $tmpjobfile $outdir/$jobfile;\n";
  exec_over_ssh($_SERVER['HTTP_HOST'], $user, $pass, $cmd, True);
  echo "<tr><td>Appion Directory</td><td>$outdir</td></tr>\n";
  echo "<tr><td>Job File Name</td><td>$jobname.job</td></tr>\n";
  
  // create directory on cluster and copy job file over
  $cmd = "mkdir -p $clusterpath;\n";
  $cmd .= "cp $outdir/$jobfile $clusterpath/$jobfile;\n";
  $jobnum = exec_over_ssh(PROCESSING_HOST, $user, $pass, $cmd, True);

  // submit job on garibaldi
  $cmd = "cd $clusterpath; qsub $jobname.job;\n";
  $jobnum = exec_over_ssh(PROCESSING_HOST, $user, $pass, $cmd, True);
  
  $jobnum=trim($jobnum);
  $jobnum = ereg_replace('\.garibaldi','',$jobnum);
  if (!is_numeric($jobnum)) {
    echo "</TABLE><P>\n";
    echo "ERROR in job submission.  Check the cluster\n";
    writeBottom();
    exit;
  }

  // insert cluster job id into row that was just created
  $particle->updateClusterQueue($jobid,$jobnum);

  echo "<tr><td>Cluster Directory</td><td>$clusterpath</td></tr>\n";
  echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
  echo "</TABLE>\n";

  // check jobs that are running on garibaldi
  echo "<P>Jobs currently running on the cluster:\n";
  $subjobs = checkClusterJobs($user,$pass);
  if ($subjobs) {echo "<PRE>$subjobs</PRE>\n";}
  else {echo "<FONT COLOR='RED'>No Jobs on the cluster, check your settings</FONT>\n";}
  echo "<p><a href='checkjobs.php?expId=$expId'>[Check Status of Jobs Associated with this Experiment]</a><p>\n";
	echo "<P><FONT COLOR='RED'>Do not hit 'reload' it will re-submit job</FONT><P>\n";
  writeBottom(True, True);
  exit;
}

else stackModelForm();

function stackModelForm($extra=False) {
  // check if session provided
  $expId = $_GET['expId'];
  $modelonly = $_GET['modelonly'];
  if ($expId) {
    $sessionId=$expId;
    $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  }
  else {
    $sessionId=$_POST['sessionId'];
    $formAction=$_SERVER['PHP_SELF'];
  }


  // if user wants to use models from another project

  if($_POST['projectId'])
    $projectId = $_POST[projectId];
  else
    $projectId=getProjectFromExpId($expId);

  $projects=getProjectList();

  if (is_numeric($projectId)) {
    $particle = new particledata();
    // get initial models associated with project
    $models=$particle->getModelsFromProject($projectId);
  }
  if (!$modelonly) {
    // find each stack entry in database
    // THIS IS REALLY, REALLY SLOW
    $stackIds = $particle->getStackIds($sessionId);
    $stackinfo=explode('|--|',$_POST['stackval']);
    $stackidval=$stackinfo[0];
    $apix=$stackinfo[1];
    $box=$stackinfo[2];
  }
  $javafunc="<script src='../js/viewer.js'></script>\n";
  if (!$modelonly) {
    writeTop("Eman Job Generator","EMAN Job Generator",$javafunc);
  }

  else {
    writeTop("Rescale/Resize Model","Rescale/Resize Model",$javafunc);
  }
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo "<FORM NAME='viewerform' METHOD='POST' ACTION='$formAction'>\n";
  echo "
  <B>Select Project:</B><BR>
  <SELECT NAME='projectId' onchange='newexp()'>\n";

  foreach ($projects as $k=>$project) {
    $sel = ($project['id']==$projectId) ? "selected" : '';
    echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
  }
  echo"
  </select>
  <P>\n";
  if (!$modelonly) {
    echo"
    <B>Stack:</B><BR>";
    echo "<SELECT NAME='stackval'>\n";

    foreach ($stackIds as $stackid){
      // get stack parameters from database
      $s=$particle->getStackParams($stackid['stackid']);
      // get number of particles in each stack
      $nump=commafy($particle->getNumStackParticles($stackid['stackid']));
      // get pixel size of stack
      $apix=($particle->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
      // get box size
      $box=($s['bin']) ? $s['boxSize']/$s['bin'] : $s['boxSize'];
      // get stack path with name
      $opvals = "$stackid[stackid]|--|$apix|--|$box|--|$s[path]|--|$s[name]";
      // if imagic stack, send both hed & img files for dmf
      if (ereg('\.hed', $s['name'])) $opvals.='|--|'.ereg_replace('hed','img',$s['name']);
      if (ereg('\.img', $s['name'])) $opvals.='|--|'.ereg_replace('img','hed',$s['name']);
      echo "<OPTION VALUE='$opvals'";
      // select previously set stack on resubmit
      if ($stackid['stackid']==$stackidval) echo " SELECTED";
      echo">$s[shownstackname] ID: $stackid[stackid] ($nump particles, $apix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
    }
    echo "</SELECT>\n";
  }
  # show initial models
  echo "<P><B>Model:</B><BR><A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><BR/>\n";
  if (!$modelonly) echo"<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'><BR/>\n";
  echo "<P>\n";
  $minf = explode('|--|',$_POST['model']);
  if (is_array($models) && count($models)>0) {
    foreach ($models as $model) {
      echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
# get list of png files in directory
      $pngfiles=array();
      $modeldir= opendir($model['path']);
      while ($f = readdir($modeldir)) {
  if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;
      }
      sort($pngfiles);

# display starting models
      $sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
      echo "<tr><TD COLSPAN=2>\n";
      $modelvals="$model[DEF_id]|--|$model[path]|--|$model[name]|--|$model[boxsize]|--|$sym[symmetry]";
      if (!$modelonly) {
	echo "<input type='RADIO' NAME='model' VALUE='$modelvals' ";
	# check if model was selected
	if ($model['DEF_id']==$minf[0]) echo " CHECKED";
	echo ">\n";
      }
      echo"Use ";
      echo"Model ID: $model[DEF_id]\n";
      echo "<input type='BUTTON' NAME='rescale' VALUE='Rescale/Resize this model' onclick=\"parent.location='uploadmodel.php?expId=$expId&rescale=TRUE&modelid=$model[DEF_id]'\"><BR>\n";
      foreach ($pngfiles as $snapshot) {
  $snapfile = $model['path'].'/'.$snapshot;
  echo "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
      }
      echo "</td>\n";
      echo "</tr>\n";
      echo"<tr><TD COLSPAN=2>$model[description]</td></tr>\n";
      echo"<tr><TD COLSPAN=2>$model[path]/$model[name]</td></tr>\n";
      echo"<tr><td>pixel size:</td><td>$model[pixelsize]</td></tr>\n";
      echo"<tr><td>box size:</td><td>$model[boxsize]</td></tr>\n";
      echo"<tr><td>symmetry:</td><td>$sym[symmetry]</td></tr>\n";
      echo"<tr><td>resolution:</td><td>$model[resolution]</td></tr>\n";
      echo "</TABLE>\n";
      echo "<P>\n";
    }
    if (!$modelonly) echo"<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'></FORM>\n";
  }
  else {echo "No initial models in database";}
  writeBottom();
  exit;
}

function jobForm($extra=false) {
  $expId = $_GET['expId'];

  ## get path data for this session for output
  $leginondata = new leginondata();
  $sessiondata = $leginondata->getSessionInfo($expId);
  $sessionpath = $sessiondata['Image path'];
  $sessionpath = ereg_replace("leginon","appion",$sessionpath);
  $sessionpath = ereg_replace("rawdata","recon/",$sessionpath);

  $particle = new particledata();
  $reconruns = count($particle->getJobIdsFromSession($expId));
  $defrunid = 'recon'.($reconruns+1);

  ## get stack data
  $stackinfo = explode('|--|',$_POST['stackval']);
  $dmfstack = $stackinfo[4];
  $box=$stackinfo[2];
  $rootpathdata = explode('/', $sessionpath);
  $dmfpath = '/home/'.$_SESSION['username'].'/';
#  $clusterpath = '/garibaldi/people-a/'.$_SESSION['username'].'/';
  $clusterpath = '~'.$_SESSION['username'].'/';
  for ($i=3 ; $i<count($rootpathdata); $i++) {
    $rootpath .= "$rootpathdata[$i]";
    if ($i+1<count($rootpathdata)) $rootpath.='/';
  }
  
  $dmfpath .= $rootpath;
  $clusterpath .= $rootpath;

  ## get model data
  $modelinfo = explode('|--|',$_POST['model']);
  $dmfmod = $modelinfo[2];
  $syminfo = explode(' ',$modelinfo[4]);
  $modsym=$syminfo[0];
  if ($modsym == 'Icosahedral') $modsym='icos';

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
  $javafunc .= writeJavaPopupFunctions();
  writeTop("Eman Job Generator","EMAN Job Generator",$javafunc);
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo "
  <FORM NAME='emanjob' METHOD='POST' ACTION='$formAction'><BR/>
  <TABLE CLASS='tableborder' CELLPADDING=4 CELLSPACING=4>
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
  </TABLE>\n";
  echo "
  <P>
  <input type='hidden' NAME='model' VALUE='".$_POST['model']."'>
  <input type='hidden' NAME='stackval' VALUE='".$_POST['stackval']."'>";
  echo"<TABLE BORDER='0' WIDTH='99%'><tr><TD VALIGN='TOP'>"; //overall table

//Cluster Parameters
  echo"
    <TABLE CLASS='tableborder' CELLPADDING=4 CELLSPACING=4>
    <tr>
      <TD COLSPAN='4' ALIGN='CENTER'>
      <H4>PBS Cluster Parameters</H4>
      </td>
    </tr>
    <tr>
      <td><A HREF=\"javascript:refinfopopup('nodes')\">Nodes:</A></td>
      <td><input type='text' NAME='nodes' VALUE='$nodes' SIZE='4' MAXCHAR='4'></td>
      <td><A HREF=\"javascript:refinfopopup('procpernode')\">Proc/Node:</A></td>
      <td><input type='text' NAME='ppn' VALUE='$ppn' SIZE='3'></td>
    </tr>
    <tr>
      <td><A HREF=\"javascript:refinfopopup('walltime')\">Wall Time:</A></td>
      <td><input type='text' NAME='walltime' VALUE='$walltime' SIZE='4'></td>
      <td><A HREF=\"javascript:refinfopopup('cputime')\">CPU Time</A></td>
      <td><input type='text' NAME='cput' VALUE='$cput' SIZE='4'></td>
    </tr>
    <tr>
      <TD COLSPAN='4'>
      Reconstruction procs per node:<input type='text' NAME='rprocs' VALUE='$rprocs' SIZE='3'>
      </td>
    </tr>
    </TABLE>
    <BR/>";

  echo"</td><TD VALIGN='TOP'>"; //overall table

//DMF Parameters TABLE
  echo"
    <TABLE CLASS='tableborder' CELLPADDING=4 CELLSPACING=4>
    <tr>
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
    </TABLE>\n";
  echo"</td></tr></TABLE>"; //overall table
  $bgcolor="#E8E8E8";
  $display_keys = array('copy','itn','ang','mask','imask','sym','hard','clskeep','clsiter','filt3d','xfiles','shrink','euler2','median','phscls','fscls','refine','perturb','goodbad','tree','coran','eotest','copy');  
  echo"
  <BR/><CENTER>
  <H4>EMAN Reconstruction Parameters</H4>
  </CENTER><HR/>
  <input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults for Iteration 1'>
  <select name='import' onChange='emanjob.submit()'>
    <option>Import parameters</option>
    <option value='groel1'>GroEL with 10,000+ particles</option>
    <option value='virusgood'>Icos Virus with good starting model</option>
  </select>
  <br />
  <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
    <tr>\n";
  foreach ($display_keys as $key) {
      echo"<td bgcolor='$bgcolor'><font class='sf'><A HREF=\"javascript:refinfopopup('$key')\">$key</a><font></td>\n";
  }
  echo"  </tr>\n";

  // set number of iterations if importing:
  if ($_POST['import']=='groel1') $numiters=20;
  elseif ($_POST['import']=='virusgood') $numiters=14;

  // otherwise use previously set values
  for ($i=1; $i<=$numiters; $i++) {
    $angn="ang".$i;
    $maskn="mask".$i;
    $imaskn="imask".$i;
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
      $mask=($box/2)-2;
      $hard='25';
      $classkeep='0.8';
      $median='CHECKED';
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
    else {
      $ang=($i>$j) ? $_POST["ang".($i-1)] : $_POST[$angn];
      $mask=($i>$j) ? $_POST["mask".($i-1)] : $_POST[$maskn];
      $imask=($i>$j) ? $_POST["imask".($i-1)] : $_POST[$imaskn];
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
      ## use symmetry of model by default, but you can change it
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



#	<TD colspan=6 bgcolor='$bgcolor' CELLPADDING=0 CELLSPACING=0>
#	  <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4 WIDTH=100%>
#            <tr>
#        <td bgcolor='$bgcolor'><input type='checkbox' NAME='$msgpn' $msgp><A HREF=\"javascript:refinfopopup('msgp')\">Subclassification by message passing:</A></td>
#        <td bgcolor='$bgcolor'><A HREF=\"javascript:refinfopopup('msgp_corcutoff')\">CorCutoff:</A>
#          <input type='text' NAME='$msgp_corcutoffn' SIZE='4' VALUE='$msgp_corcutoff'></td>
#        <td bgcolor='$bgcolor'><A HREF=\"javascript:refinfopopup('msgp_minptcls')\">MinPtcls:</A>
#          <input type='text' NAME='$msgp_minptclsn' SIZE='4' VALUE='$msgp_minptcls'></td>
#            </tr>
#          </TABLE>
#        <TD colspan=2 bgcolor='$bgcolor' ALIGN='CENTER'>
#      </tr>
  }
  echo"
  </TABLE>
  <input type='hidden' NAME='numiters' VALUE='$numiters'><P>
  <input type='SUBMIT' NAME='write' VALUE='Create Job File'>
  </FORM>\n";
  writeBottom();
  exit;
}

function writeJobFile ($extra=False) {
  $expId = $_GET['expId'];
  $formAction=$_SERVER['PHP_SELF']."?expId=$expId";

  $jobname = $_POST['jobname'];
  $jobfile ="$jobname.job";

  $outdir = $_POST['outdir'];
  if (substr($outdir,-1,1)!='/') $outdir.='/';

  // clusterpath contains jobname
  $clusterpath = $_POST['clusterpath'];
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
    newwindow.document.write('<P>&nbsp;<BR></BODY></HTML>');
    newwindow.document.close();
  }
  </SCRIPT>\n";
  }
  writeTop("Eman Job Generator","EMAN Job Generator", $javafunc);

  $header.= "#PBS -l nodes=".$_POST['nodes'].":ppn=".$_POST['ppn']."\n";
  $header.= "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
  $header.= "#PBS -l cput=".$_POST['cput'].":00:00\n";
  $header.= "#PBS -m e\n";
  $header.= "#PBS -r n\n\n";
  $clusterjob = "# stackId: $stackidval\n";
  $clusterjob.= "# modelId: $modelid\n";
  $clusterjob.= "\nmkdir -p $clusterfullpath\n";
  $clusterjob.= "\ncd $clusterfullpath\n";
  $clusterjob.= "\nrm -f recon\n";
  $clusterjob.= "ln -s \$PBSREMOTEDIR recon\n";
  $clusterjob.= "chmod 755 recon\n"; 
  $clusterjob.= "cd recon\n";
  // get file name, strip extension
  $ext=strrchr($_POST['dmfstack'],'.');
  $stackname=substr($_POST['dmfstack'],0,-strlen($ext));
  $clusterjob.= "\ndmf get $dmffullpath/".$_POST['dmfmod']." threed.0a.mrc\n";
  $clusterjob.= "dmf get $dmffullpath/$stackname.hed start.hed\n";
  $clusterjob.= "dmf get $dmffullpath/$stackname.img start.img\n";
  $clusterjob.= "\nrm .mparm\nforeach i (`sort -u \$PBS_NODEFILE`)\n";
  $clusterjob.= "  echo 'rsh 1 ".$_POST['rprocs']."' \$i \$PBSREMOTEDIR >> .mparm\n";
  $clusterjob.= "end\n";
  $procs=$_POST['nodes']*$_POST['rprocs'];
  $numiters=$_POST['numiters'];
  $pad=intval($box*1.25);
  // make sure $pad value is even int
  $pad = ($pad%2==1) ? $pad+=1 : $pad;
  for ($i=1; $i<=$numiters; $i++) {
    $ang=$_POST["ang".$i];
    $mask=$_POST["mask".$i];
    $imask=$_POST["imask".$i];
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
    if ($goodbad=='on') $line.=" goodbad";
    $line.=" > refine".$i.".txt\n";
    $line.="getProjEulers.py proj.img proj.$i.txt\n";
    # if ref-free correllation analysis
    if ($coran=='on') {
      $line .="coran_for_cls.py mask=$mask proc=$procs iter=$i";
      if ($sym) $line .= " sym=$sym";
      if ($hard) $line .= " hard=$hard";
      if ($eotest=='on') $line .= " eotest";
      $line .= " > coran".$i.".txt\n";
      $line.="getRes.pl >> resolution.txt $i $box $apix\n";
    }
    # if eotest specified with coran, don't do eotest here:
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
      $line.="getRes.pl >> resolution.txt $i $box $apix\n";
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
  if ($_POST['dmfstore']=='on') {
    $clusterjob.= "\ntar -cvzf model.tar.gz threed.*a.mrc\n";
    $clusterjob.= "dmf put model.tar.gz $dmffullpath\n";
    $line = "\ntar -cvzf results.tar.gz fsc* cls* refine.* particle.* classes.* proj.* sym.* .emanlog *txt ";
    if ($msgp=='on') {
	$line .= "goodavgs.* ";
	$clusterjob.= "dmf put msgPassing.tar $dmffullpath\n";
    }
    $line .= "\n";
    $clusterjob.= $line;
    $clusterjob.= "dmf put results.tar.gz $dmffullpath\n";
  }
  if (!$extra) {
    echo "Please review your job below.<BR>";
    echo "If you are satisfied:<BR>\n";
    echo "1) Place files in DMF<BR>\n";
    echo "2) Once this is done, click the button to launch your job.<BR>\n";
    echo"<input type='button' NAME='dmfput' VALUE='Put files in DMF' onclick='displayDMF()'><P>\n";
    echo"<input type='hidden' NAME='dmfpath' VALUE=''>\n";
  }
  else {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo "<FORM NAME='emanjob' METHOD='POST' ACTION='$formAction'><BR>\n";
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
  writeBottom();
  exit;
};

function defaultReconValues ($box) {
  $rad = ($box/2)-2;
  $javafunc = "
  <SCRIPT LANGUAGE='JavaScript'>
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
      obj.median1.checked = true;
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


function writeJavaPopupFunctions () {
  $javafunc = "
  <style type='text/css'>
    input { border-style: solid; border-color: #9dae9b; }
    select { border-style: solid; border-color: #9dae9b; }
  </style>\n";

    $javafunc .= "
  <SCRIPT LANGUAGE='JavaScript'>
  function refinfopopup(infoname) {
    var newwindow=window.open('','name','height=250, width=400');
    newwindow.document.write('<HTML><BODY>');
    if (infoname=='nodes') {
      newwindow.document.write('Nodes refers to the number of computer to process on simultaneously. The more nodes you get the faster things will get process, but more nodes requires that you wait longer before being allowed to begin processing.');
    } else if (infoname=='walltime') {
      newwindow.document.write('Wall time, also called real-world time or wall-clock time, refers to elapsed time as determined by a chronometer such as a wristwatch or wall clock. (The reference to a wall clock is how the term originally got its name.)');
    } else if (infoname=='cputime') {
      newwindow.document.write('Wall time, also called real-world time or wall-clock time, refers to elapsed time as determined by a chronometer such as a wristwatch or wall clock. (The reference to a wall clock is how the term originally got its name.)');
    } else if (infoname=='procpernode') {
      newwindow.document.write('Processors per node. Each computer (node) or Garibaldi has 4 processors (procs), so proc/node=4. For some cases, you may want to use less processors on each node, leaving more memory and system resources for each process.');
    } else if (infoname=='ang') {
      newwindow.document.write('Angular step for projections (in degrees)');
    } else if (infoname=='itn') {
      newwindow.document.write('Iteration Number');
    } else if (infoname=='copy') {
      newwindow.document.write('Duplicate the parameters for this iteration');
    } else if (infoname=='mask') {
      newwindow.document.write('Radius of external mask');
    } else if (infoname=='imask') {
      newwindow.document.write('Radius of internal mask');
    } else if (infoname=='sym') {
      newwindow.document.write('Imposes symmetry on the model, omit this option for no/unknown symmetry<BR/>Examples: c1, c2, d7, etc.');
    } else if (infoname=='hard') {
      newwindow.document.write('Hard limit for <I>make3d</I> program. This specifies how well the class averages must match the model to be included, 25 is typical');
    } else if (infoname=='clskeep') {
      newwindow.document.write('<b>classkeep=[std dev multiplier]</b><br />This determines how many raw particles are discarded for each class-average. This is defined in terms of the standard-deviation of the self-similarity of the particle set. A value close to 0 (should not be exactly 0) will discard about 50% of the data. 1 is a typical value, and will typically discard 10-20% of the data.');
    } else if (infoname=='clsiter') {
      newwindow.document.write('Generation of class averages is an iterative process. Rather than just aligning the raw particles to a reference, they are iteratively aligned toeach other to produce a class-average representative of the data, not of the model, eliminating initial model bias. Typically set to 8 in the early rounds and 3 in later rounds - 0 may be used at the end, but model bias may result.');
    } else if (infoname=='filt3d') {
      newwindow.document.write('<b>fil3d=[rad]</b><br />Applies a gaussian low-pass filter to the 3D model between iterations. This can be used to correct problems that may result in high resolution terms being upweighted. [rad] is in pixels, not Angstroms');
    } else if (infoname=='shrink') {
      newwindow.document.write('<b>shrink=[n]</b><br /><i>Experimental</i>, Another option that can produce dramatic speed improvements. In some cases, this option can actually produce an improvement in classification accuracy. This option scales the particles and references down by a factor of [n] before classification. Since data is often heavily oversampled, and classification is dominated by low resolution terms, this can be both safe, and actually improve classification by \'filtering\' out high resolution noise. Generally shrink=2 is safe and effective especially for early refinement. In cases of extreme oversampling, larger values may be ok. This option should NOT be used for the final rounds of refinement at high resolution.');
    } else if (infoname=='euler2') {
      newwindow.document.write('<b>euler2=[oversample factor]</b><br /><i>Experimental</i>, This option should improve convergence and reconstruction quality, but has produced mixed results in the past. It adds an additional step to the refinement process in which class-averages orientations are redetermined by projection-matching. The parameter allows you to decrease the angular step (ang=) used to generateprojections. ie - 2 would produce projections with angular step of ang/2. It may be worth trying, but use it with caution on new projects.');
    } else if (infoname=='perturb') {
      newwindow.document.write('<i>Experimental</i>, potentially useful and at worst should be harmless. Has not been well characterized yet. Rather than generating Euler angles at evenly spaced positions, it adds some randomness to the positions. This should produce a more uniform distribution of data in 3D Fourier space and reduce Fourier artifacts');
    } else if (infoname=='xfiles') {
      newwindow.document.write('<b>xfiles=[mass in kD]</b><br />A convenience option.  For each 3D model it will produce a corresponding x-file (threed.1a.mrc -> x.1.mrc).  Based on the mass, the x-file will be scaled so an isosurface threshold of 1 will contain the specified mass.');
    } else if (infoname=='tree') {
      newwindow.document.write('This can be a risky option, but it can produce dramatic speedups in the refinement process. Rather than comparing each particle to every reference, this will decimate the reference population to 1/4 (if 2 is specified) or 1/9 (if 3 is specified) of its original size, classify, then locally determine which of the matches is best. Is is safest in conjunction with very small angular steps, ie - large numbers of projections. The safest way to use this is either:<br /><i>a)</i> for high-resolution, small-ang refinement or <br/><i>b)</i> for the initial iterations of refinement (then turn it off for the last couple of iterations).');
    } else if (infoname=='median') {
      newwindow.document.write('When creating class averages, use the median value for each pixel instead of the average.  If your dataset is noisy, this is recommended');
    } else if (infoname=='phscls') {
      newwindow.document.write('This option will use signal to noise ratio weighted phase residual as a classification criteria (instead of the default optimized real space variance). Over the last year or so, people working on cylindrical structures (like GroEL), have noticed that \'side views\' of this particle seem to frequently get classified as being tilted 4 or 5 degrees from the side view. While apparently this didn\'t effect the models significantly at the obtained resolution, it is quite irritating. This problem turns out to be due to resolution mismatch between the 3D model and the individual particles. Using phase residual solves this problem, although it\'s unclear if there is any resolution improvement. This option has a slight speed penalty');
    } else if (infoname=='fscls') {
      newwindow.document.write('An improvement, albeit an experimental one, over phasecls. phasecls ignores Fourier amplitude when making image comparisons. fscls will use a SNR weighted Fourier shell correlation as a similarity criteria. Preliminary tests have shown that this produces slightly better results than phasecls, but it should still be used with caution.');
    } else if (infoname=='refine') {
      newwindow.document.write('This will do subpixel alignment of the particle translations for classification and averaging. May have a significant impact at higher resolutions (with a speed penalty).');
    } else if (infoname=='goodbad') {
      newwindow.document.write('Saves good and bad class averages from 3D reconstruction. Overwrites each new iteration.');
    } else if (infoname=='eotest') {
      newwindow.document.write('Run the <I>eotest</I> program that performs a 2 way even-odd test to determine the resolution of a reconstruction.');
    } else if (infoname=='coran') {
      newwindow.document.write('Use correspondence analysis particle clustering algorithm');
    } else {
      newwindow.document.write('Missing help info');
    }
    newwindow.document.write('</BODY></HTML>');
    newwindow.document.close();
  }
  </SCRIPT>\n";
  return $javafunc;
};

