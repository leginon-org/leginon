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
//if (TRUE) {
  $particle = new particledata();
  //jobForm();
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
    processing_header("Eman Job Generator","EMAN Job Generator",$javafunc);
  }

  else {
    processing_header("Rescale/Resize Model","Rescale/Resize Model",$javafunc);
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
  processing_footer();
  exit;
}

function jobForm($extra=false) {
  $expId = $_GET['expId'];
  
  ## for now, strongly encourage the user to use the EMAN convention (i.e. "threed") as the root for the volume names
  $modelname = "threed";
  $parname="params";
  
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
  $stackidval=$stackinfo[0];
  $apix=$stackinfo[1];
  $box=$stackinfo[2];
  $stackpath=$stackinfo[3];
  $stackname1=$stackinfo[4];
  $stackname2=$stackinfo[5];
  
  $stack=$stackname1 ;

  ## figure out ctf params here
  
  
  $rootpathdata = explode('/', $sessionpath);
  $dmfpath = '/home/'.$_SESSION['username'].'/';
  $clusterpath = '~'.$_SESSION['username'].'/';
  for ($i=3 ; $i<count($rootpathdata); $i++) {
    $rootpath .= "$rootpathdata[$i]";
    if ($i+1<count($rootpathdata)) $rootpath.='/';
  }

  ## get model data
  $modelinfo = explode('|--|',$_POST['model']);
  $dmfmod = $modelinfo[2];
  $syminfo = explode(' ',$modelinfo[4]);
  $modsym=$syminfo[0];
  if ($modsym == 'Icosahedral') $modsym='icos';

  $jobname = ($_POST['jobname']) ? $_POST['jobname'] : $defrunid;
  $outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
  $numiters= ($_POST['numiters']) ? $_POST['numiters'] : 1;
  if ($_POST['duplicate']) {
    $numiters+=1;
    $j=$_POST['duplicate'];
  }
  else $j=$numiters;

  $javafunc .= defaultReconValues($box);
  $javafunc .= writeJavaPopupFunctions('frealign');
  $javafunc .= garibaldiFun();
  processing_header("Frealign Job Generator","Frealign Job Generator",$javafunc);
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
	echo "<form name='emanjob' method='post' action='$formaction'><br />\n";
	echo "<p>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";


  $bgcolor="#E8E8E8";
  echo"
  <br />
  <H4 style='align=\'center\' >Frealign Reconstruction Parameters</H4>
  <hr />
	";
	echo "
  <input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults for Iteration 1'>
 	";
	echo "
  <br />
  <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
    <tr>\n";
/*  foreach ($display_keys as $k=>$key) {
			$id="l$k";
      echo"<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"$id\" onMouseOver='popLayer(\"$key\", \"$id\")' onMouseOut='hideLayer()'>$key</a></font></td>\n";
  }*/
  echo"  </tr>\n";

  // otherwise use previously set values
  for ($i=1; $i<=$numiters; $i++) {
    $formatn="format".$i;
    $moden="mode".$i;
    $magrefinen="magrefine".$i;
    $defocusrefinen="defocusrefine".$i;
    $astigrefinen="astigrefine".$i;
    $fliptiltn="fliptilt".$i;
    $ewaldn="ewald".$i;
    $matchesn="matches".$i;
    $historyn="history".$i;
    $finalsymn="finalsym".$i;
    $fomfiltern="fomfilter".$i;
    $fscn="fsc".$i;
    $radiusn="radius".$i;
    $iradiusn="iradius".$i;
    $apixn="apix".$i;
    $ampcontrastn="ampcontrast".$i;
    $maskthreshn="maskthresh".$i;
    $phaseconstantn="phaseconstant".$i;
    $avgresidualn="avgresidual".$i;
    $angn="ang".$i;
    $itmaxn="itmax".$i;
    $maxmatchn="maxmatch".$i;
    $psin="psi".$i;
    $thetan="theta".$i;
    $phin="phi".$i;
    $deltayn="deltay".$i;
    $deltaxn="deltax".$i;
    $firstn="first".$i;
    $lastn="last".$i;
    $symn="sym".$i;
    $relmagn="relmag".$i;
    $dstepn="dstep".$i;
    $targetresidualn="targetresidual".$i;
    $residualthreshn="residualthresh".$i;
    $csn="cs".$i;
    $kvn="kv".$i;
    $beamtiltxn="beamtiltx".$i;
    $beamtiltyn="beamtilty".$i;
    $reslimitn="reslimit".$i;
    $hpn="hp".$i;
    $lpn="lp".$i;
    $bfactorn="bfactor".$i;
    $stackn="stack".$i;
    $matchstackn="matchstack".$i;
    $inparn="inpar".$i;
    $outparn="outpar".$i;
    $outshiftparn="outshiftpar".$i;
    $involn="invol".$i;
    $weight3dn="weight3d".$i;
    $oddvoln="oddvol".$i;
    $evenvoln="evenvol".$i;
    $outresidualn="outresidual".$i;
    $pointspreadvoln="pointspreadvol".$i;

      //ones that don't change go here
      if ($i==1) {
      	$apix=$apix;
	$stack=$stackname1;
      }
      else {
      	$apix=($i>$j) ? $_POST["apix".($i-1)] : $_POST[$apixn];
      	$stack=($i>$j) ? $_POST["stack".($i-1)] : $_POST[$stackn];
      }

      ###set default values that iterate
      $invol=$modelname.".".($i-1).".mrc";
      $inpar=$parname.".".($i-1).".par";
      $outpar=$parname.".".($i).".par";

      $format=($i>$j) ? $_POST["format".($i-1)] : $_POST[$formatn];
      $mode=($i>$j) ? $_POST["mode".($i-1)] : $_POST[$moden];
      $magrefine=($i>$j) ? $_POST["magrefine".($i-1)] : $_POST[$magrefinen];
      $defocusrefine=($i>$j) ? $_POST["defocusrefine".($i-1)] : $_POST[$defocusrefinen];
      $astigrefine=($i>$j) ? $_POST["astigrefine".($i-1)] : $_POST[$astigrefinen];
      $fliptilt=($i>$j) ? $_POST["fliptilt".($i-1)] : $_POST[$fliptiltn];
      $ewald=($i>$j) ? $_POST["ewald".($i-1)] : $_POST[$ewaldn];
      $matches=($i>$j) ? $_POST["matches".($i-1)] : $_POST[$matchesn];
      $history=($i>$j) ? $_POST["history".($i-1)] : $_POST[$historyn];
      $finalsym=($i>$j) ? $_POST["finalsym".($i-1)] : $_POST[$finalsymn];
      $fomfilter=($i>$j) ? $_POST["fomfilter".($i-1)] : $_POST[$fomfiltern];
      $fsc=($i>$j) ? $_POST["fsc".($i-1)] : $_POST[$fscn];
      $radius=($i>$j) ? $_POST["radius".($i-1)] : $_POST[$radiusn];
      $iradius=($i>$j) ? $_POST["iradius".($i-1)] : $_POST[$iradiusn];
      $ampcontrast=($i>$j) ? $_POST["ampcontrast".($i-1)] : $_POST[$ampcontrastn];
      $maskthresh=($i>$j) ? $_POST["maskthresh".($i-1)] : $_POST[$maskthreshn];
      $phaseconstant=($i>$j) ? $_POST["phaseconstant".($i-1)] : $_POST[$phaseconstantn];
      $avgresidual=($i>$j) ? $_POST["avgresidual".($i-1)] : $_POST[$avgresidualn];
      $ang=($i>$j) ? $_POST["ang".($i-1)] : $_POST[$angn];
      $itmax=($i>$j) ? $_POST["itmax".($i-1)] : $_POST[$itmaxn];
      $maxmatch=($i>$j) ? $_POST["maxmatch".($i-1)] : $_POST[$maxmatchn];
      $psi=($i>$j) ? $_POST["psi".($i-1)] : $_POST[$psin];
      $theta=($i>$j) ? $_POST["theta".($i-1)] : $_POST[$thetan];
      $phi=($i>$j) ? $_POST["phi".($i-1)] : $_POST[$phin];
      $deltax=($i>$j) ? $_POST["deltax".($i-1)] : $_POST[$deltaxn];
      $deltay=($i>$j) ? $_POST["deltay".($i-1)] : $_POST[$deltayn];
      $first=($i>$j) ? $_POST["first".($i-1)] : $_POST[$firstn];
      $last=($i>$j) ? $_POST["last".($i-1)] : $_POST[$lastn];
      $sym=($i>$j) ? $_POST["sym".($i-1)] : $_POST[$symn];
      $relmag=($i>$j) ? $_POST["relmag".($i-1)] : $_POST[$relmagn];
      $dstep=($i>$j) ? $_POST["dstep".($i-1)] : $_POST[$dstepn];
      $targetresidual=($i>$j) ? $_POST["targetresidual".($i-1)] : $_POST[$targetresidualn];
      $residualthresh=($i>$j) ? $_POST["residualthresh".($i-1)] : $_POST[$residualthreshn];
      $cs=($i>$j) ? $_POST["cs".($i-1)] : $_POST[$csn];
      $kv=($i>$j) ? $_POST["kv".($i-1)] : $_POST[$kvn];
      $beamtiltx=($i>$j) ? $_POST["beamtiltx".($i-1)] : $_POST[$beamtiltxn];
      $beamtilty=($i>$j) ? $_POST["beamtilty".($i-1)] : $_POST[$beamtiltyn];
      $reslimit=($i>$j) ? $_POST["reslimit".($i-1)] : $_POST[$reslimitn];
      $hp=($i>$j) ? $_POST["hp".($i-1)] : $_POST[$hpn];
      $lp=($i>$j) ? $_POST["lp".($i-1)] : $_POST[$lpn];
      $bfactor=($i>$j) ? $_POST["bfactor".($i-1)] : $_POST[$bfactorn];
      $matchstack=($i>$j) ? $_POST["matchstack".($i-1)] : $_POST[$matchstackn];
      $outshiftpar=($i>$j) ? $_POST["outshiftpar".($i-1)] : $_POST[$outshiftparn];
      $weight3d=($i>$j) ? $_POST["weight3d".($i-1)] : $_POST[$weight3dn];
      $oddvol=($i>$j) ? $_POST["oddvol".($i-1)] : $_POST[$oddvoln];
      $evenvol=($i>$j) ? $_POST["evenvol".($i-1)] : $_POST[$evenvoln];
      $outresidual=($i>$j) ? $_POST["outresidual".($i-1)] : $_POST[$outresidualn];
      $pointspreadvol=($i>$j) ? $_POST["pointspreadvol".($i-1)] : $_POST[$pointspreadvoln];

      ## use symmetry of model by default, but you can change it
      if ($i==1 && !$_POST['duplicate']) $sym=$modsym;

      if ($i>$j) {
    	  $magrefine=($_POST["magrefine".($i-1)]=='on') ? 'CHECKED' : '';
    	  $defocusrefine=($_POST["defocusrefine".($i-1)]=='on') ? 'CHECKED' : '';
    	  $astigrefine=($_POST["astigrefine".($i-1)]=='on') ? 'CHECKED' : '';
    	  $fliptilt=($_POST["fliptilt".($i-1)]=='on') ? 'CHECKED' : '';
    	  $matches=($_POST["matches".($i-1)]=='on') ? 'CHECKED' : '';
    	  $history=($_POST["history".($i-1)]=='on') ? 'CHECKED' : '';
    	  $finalsym=($_POST["finalsym".($i-1)]=='on') ? 'CHECKED' : '';
    	  $fomfilter=($_POST["fomfilter".($i-1)]=='on') ? 'CHECKED' : '';
    	  $psi=($_POST["psi".($i-1)]=='on') ? 'CHECKED' : '';
    	  $theta=($_POST["theta".($i-1)]=='on') ? 'CHECKED' : '';
    	  $phi=($_POST["phi".($i-1)]=='on') ? 'CHECKED' : '';
    	  $deltax=($_POST["deltax".($i-1)]=='on') ? 'CHECKED' : '';
    	  $deltay=($_POST["deltay".($i-1)]=='on') ? 'CHECKED' : '';
      }
      else {
   	   $magrefine=($_POST[$magrefinen]=='on') ? 'CHECKED' : '';
	   $defocusrefine=($_POST[$defocusrefinen]=='on') ? 'CHECKED' : '';
   	   $astigrefine=($_POST[$astigrefinen]=='on') ? 'CHECKED' : '';
   	   $fliptilt=($_POST[$fliptiltn]=='on') ? 'CHECKED' : '';
   	   $matches=($_POST[$matchesn]=='on') ? 'CHECKED' : '';
   	   $history=($_POST[$historyn]=='on') ? 'CHECKED' : '';
   	   $finalsym=($_POST[$finalsymn]=='on') ? 'CHECKED' : '';
   	   $fomfilter=($_POST[$fomfiltern]=='on') ? 'CHECKED' : '';
   	   $psi=($_POST[$psin]=='on') ? 'CHECKED' : '';
   	   $theta=($_POST[$thetan]=='on') ? 'CHECKED' : '';
   	   $phi=($_POST[$phin]=='on') ? 'CHECKED' : '';
   	   $deltax=($_POST[$deltaxn]=='on') ? 'CHECKED' : '';
   	   $deltay=($_POST[$deltayn]=='on') ? 'CHECKED' : '';

      }
    $rcol = ($i % 2) ? '#FFFFFF' : '#FFFDCC';
     echo"
      <tr>
   		<tr>
			<td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i' onclick='emanjob.submit()'></td>
			<td bgcolor='$rcol'><b>$i</b></td>
			<td>
   				<table>
				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l0\" onMouseOver='popLayer(\"format\", \"l0\")' onMouseOut='hideLayer()'>format</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l1\" onMouseOver='popLayer(\"mode\", \"l1\")' onMouseOut='hideLayer()'>mode</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l2\" onMouseOver='popLayer(\"magrefine\", \"l2\")' onMouseOut='hideLayer()'>magrefine</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l3\" onMouseOver='popLayer(\"defocusrefine\", \"l3\")' onMouseOut='hideLayer()'>defocusrefine</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l4\" onMouseOver='popLayer(\"astigrefine\", \"l4\")' onMouseOut='hideLayer()'>astigrefine</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l5\" onMouseOver='popLayer(\"fliptilt\", \"l5\")' onMouseOut='hideLayer()'>fliptilt</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l6\" onMouseOver='popLayer(\"ewald\", \"l6\")' onMouseOut='hideLayer()'>ewald</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l7\" onMouseOver='popLayer(\"matches\", \"l7\")' onMouseOut='hideLayer()'>matches</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l8\" onMouseOver='popLayer(\"history\", \"l8\")' onMouseOut='hideLayer()'>history</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l9\" onMouseOver='popLayer(\"finalsym\", \"l8\")' onMouseOut='hideLayer()'>finalsym</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l10\" onMouseOver='popLayer(\"fomfilter\", \"l10\")' onMouseOut='hideLayer()'>fomfilter</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l11\" onMouseOver='popLayer(\"fsc\", \"l11\")' onMouseOut='hideLayer()'>fsc</a></font></td>
				</tr>
				<tr>
        				 <td bgcolor='$rcol'><input type='text' NAME='$formatn' SIZE='3' VALUE='$format'></td>
        				 <td bgcolor='$rcol'><input type='text' NAME='$moden' SIZE='3' VALUE='$mode'></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$magrefinen' $magrefine></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$defocusrefinen' $defocusrefine></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$astigrefinen' $astigrefine></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$fliptiltn' $fliptilt></td>
        				 <td bgcolor='$rcol'><input type='text' NAME='$ewaldn' SIZE='3' VALUE='$ewald'></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$matchesn' $matches></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$historyn' $history></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$finalsymn' $finalsym></td>
        				 <td bgcolor='$rcol'><input type='checkbox' NAME='$fomfiltern' $fomfilter></td>
        				 <td bgcolor='$rcol'><input type='text' NAME='$fscn' SIZE='3' VALUE='$fsc'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l12\" onMouseOver='popLayer(\"radius\", \"l12\")' onMouseOut='hideLayer()'>radius</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l13\" onMouseOver='popLayer(\"iradius\", \"l13\")' onMouseOut='hideLayer()'>iradius</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l14\" onMouseOver='popLayer(\"apix\", \"l14\")' onMouseOut='hideLayer()'>apix</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l15\" onMouseOver='popLayer(\"ampcontrast\", \"l15\")' onMouseOut='hideLayer()'>ampcontrast</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l16\" onMouseOver='popLayer(\"maskthresh\", \"l16\")' onMouseOut='hideLayer()'>maskthresh</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l17\" onMouseOver='popLayer(\"phaseconstant\", \"l17\")' onMouseOut='hideLayer()'>phaseconstant</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l18\" onMouseOver='popLayer(\"avgresidual\", \"l18\")' onMouseOut='hideLayer()'>avgresidual</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l19\" onMouseOver='popLayer(\"ang\", \"l19\")' onMouseOut='hideLayer()'>ang</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l20\" onMouseOver='popLayer(\"itmax\", \"l20\")' onMouseOut='hideLayer()'>itmax</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l21\" onMouseOver='popLayer(\"maxmatch\", \"l21\")' onMouseOut='hideLayer()'>maxmatch</a></font></td>
				</tr>
				<tr>
        				<td bgcolor='$rcol'><input type='text' NAME='$radiusn' SIZE='3' VALUE='$radius'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$iradiusn' SIZE='3' VALUE='$iradius'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$apixn' SIZE='3' VALUE='$apix'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$ampcontrastn' SIZE='3' VALUE='$ampcontrast'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$maskthreshn' SIZE='3' VALUE='$maskthresh'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$phaseconstantn' SIZE='3' VALUE='$phaseconstant'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$avgresidualn' SIZE='3' VALUE='$avgresidual'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$angn' SIZE='3' VALUE='$ang'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$itmaxn' SIZE='3' VALUE='$itmax'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$maxmatchn' SIZE='3' VALUE='$maxmatch'></td>
				</tr>
				
				
				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l22\" onMouseOver='popLayer(\"psi\", \"l22\")' onMouseOut='hideLayer()'>psi</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l23\" onMouseOver='popLayer(\"theta\", \"l23\")' onMouseOut='hideLayer()'>theta</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l24\" onMouseOver='popLayer(\"phi\", \"l24\")' onMouseOut='hideLayer()'>phi</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l25\" onMouseOver='popLayer(\"deltax\", \"l25\")' onMouseOut='hideLayer()'>deltax</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l26\" onMouseOver='popLayer(\"deltay\", \"l26\")' onMouseOut='hideLayer()'>deltay</a></font></td>
				</tr>
				<tr>
        				<td bgcolor='$rcol'><input type='checkbox' NAME='$psin' $psi></td>
        				<td bgcolor='$rcol'><input type='checkbox' NAME='$thetan' $theta></td>
        				<td bgcolor='$rcol'><input type='checkbox' NAME='$phin' $phi></td>
        				<td bgcolor='$rcol'><input type='checkbox' NAME='$deltaxn' $deltax></td>
        				<td bgcolor='$rcol'><input type='checkbox' NAME='$deltayn' $deltay></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l27\" onMouseOver='popLayer(\"first\", \"l27\")' onMouseOut='hideLayer()'>first</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l28\" onMouseOver='popLayer(\"last\", \"l28\")' onMouseOut='hideLayer()'>last</a></font></td>
				</tr>
				<tr>
        				<td bgcolor='$rcol'><input type='text' NAME='$firstn' SIZE='3' VALUE='$first'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$lastn' SIZE='3' VALUE='$last'></td>
				</tr>	

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l29\" onMouseOver='popLayer(\"sym\", \"l29\")' onMouseOut='hideLayer()'>sym</a></font></td>
		        		<td bgcolor='$rcol'><input type='text' NAME='$symn' SIZE='3' VALUE='$sym'></td>
				</tr>
				
				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l30\" onMouseOver='popLayer(\"relmag\", \"l30\")' onMouseOut='hideLayer()'>relmag</a></font></td>
		        		<td bgcolor='$rcol'><input type='text' NAME='$relmagn' SIZE='3' VALUE='$relmag'></td>
        			</tr>
				
				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l31\" onMouseOver='popLayer(\"dstep\", \"l31\")' onMouseOut='hideLayer()'>dstep</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l32\" onMouseOver='popLayer(\"targetresidual\", \"l32\")' onMouseOut='hideLayer()'>targetresidual</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l33\" onMouseOver='popLayer(\"residualthresh\", \"l33\")' onMouseOut='hideLayer()'>residualthresh</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l34\" onMouseOver='popLayer(\"cs\", \"l34\")' onMouseOut='hideLayer()'>cs</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l35\" onMouseOver='popLayer(\"kv\", \"l35\")' onMouseOut='hideLayer()'>kv</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l36\" onMouseOver='popLayer(\"beamtiltx\", \"l36\")' onMouseOut='hideLayer()'>beamtiltx</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l37\" onMouseOver='popLayer(\"beamtilty\", \"l37\")' onMouseOut='hideLayer()'>beamtilty</a></font></td>
				</tr>				
				<tr>	
					<td bgcolor='$rcol'><input type='text' NAME='$dstepn' SIZE='3' VALUE='$dstep'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$targetresidualn' SIZE='3' VALUE='$targetresidual'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$residualthreshn' SIZE='3' VALUE='$residualthresh'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$csn' SIZE='3' VALUE='$cs'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$kvn' SIZE='3' VALUE='$kv'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$beamtiltxn' SIZE='3' VALUE='$beamtiltx'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$beamtiltyn' SIZE='3' VALUE='$beamtilty'></td>
				</tr>
				
				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l38\" onMouseOver='popLayer(\"reslimit\", \"l38\")' onMouseOut='hideLayer()'>reslimit</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l39\" onMouseOver='popLayer(\"hp\", \"l39\")' onMouseOut='hideLayer()'>hp</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l40\" onMouseOver='popLayer(\"lp\", \"l40\")' onMouseOut='hideLayer()'>lp</a></font></td>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l41\" onMouseOver='popLayer(\"bfactor\", \"l41\")' onMouseOut='hideLayer()'>bfactor</a></font></td>
				</tr>
				<tr>
        				<td bgcolor='$rcol'><input type='text' NAME='$reslimitn' SIZE='3' VALUE='$reslimit'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$hpn' SIZE='3' VALUE='$hp'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$lpn' SIZE='3' VALUE='$lp'></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$bfactorn' SIZE='3' VALUE='$bfactor'></td>
				</tr>
				</table>
				<table>
				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l42\" onMouseOver='popLayer(\"stack\", \"l42\")' onMouseOut='hideLayer()'>stack</a></font></td>
	        			<td bgcolor='$rcol'><input type='text' NAME='$stackn' SIZE='10' VALUE='$stack'></td>
				</tr>
				
				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l43\" onMouseOver='popLayer(\"matchstack\", \"l43\")' onMouseOut='hideLayer()'>matchstack</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$matchstackn' SIZE='10' VALUE='$matchstack'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l44\" onMouseOver='popLayer(\"inpar\", \"l44\")' onMouseOut='hideLayer()'>inpar</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$inparn' SIZE='10' VALUE='$inpar'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l45\" onMouseOver='popLayer(\"outpar\", \"l45\")' onMouseOut='hideLayer()'>outpar</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$outparn' SIZE='10' VALUE='$outpar'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l46\" onMouseOver='popLayer(\"outshiftpar\", \"l46\")' onMouseOut='hideLayer()'>outshiftpar</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$outshiftparn' SIZE='10' VALUE='$outshiftpar'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l47\" onMouseOver='popLayer(\"invol\", \"l47\")' onMouseOut='hideLayer()'>invol</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$involn' SIZE='10' VALUE='$invol'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l48\" onMouseOver='popLayer(\"weight3d\", \"l48\")' onMouseOut='hideLayer()'>weight3d</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$weight3dn' SIZE='10' VALUE='$weight3d'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l49\" onMouseOver='popLayer(\"oddvol\", \"l49\")' onMouseOut='hideLayer()'>oddvol</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$oddvoln' SIZE='10' VALUE='$oddvol'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l50\" onMouseOver='popLayer(\"evenvol\", \"l50\")' onMouseOut='hideLayer()'>evenvol</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$evenvoln' SIZE='10' VALUE='$evenvol'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l51\" onMouseOver='popLayer(\"outresidual\", \"l51\")' onMouseOut='hideLayer()'>outresidual</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$outresidualn' SIZE='10' VALUE='$outresidual'></td>
				</tr>

				<tr>
					<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l52\" onMouseOver='popLayer(\"pointspreadvol\", \"l52\")' onMouseOut='hideLayer()'>pointspreadvol</a></font></td>
        				<td bgcolor='$rcol'><input type='text' NAME='$pointspreadvoln' SIZE='10' VALUE='$pointspreadvol'></td>
				</tr>
				</table>
			</td>
  		</tr>

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
#          </TABLE>
#        <TD colspan=2 bgcolor='$bgcolor' ALIGN='CENTER'>
#      </tr>
  }
  echo"
  </TABLE>
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


  // get the stack info (pixel size, box size)
  $stackinfo=explode('|--|',$_POST['stackval']);
  $stackidval=$stackinfo[0];
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
  function setupFiles() {
    newwindow=window.open('','name','height=150', width=900')
    newwindow.document.write('<HTML><BODY>')
    newwindow.document.write('Please create a working directory and copy the initial model and stack to that directory')
    newwindow.document.write('<p>dmf put $stackpath/$stackname1 $stackname1</p>')\n";
    if ($stackname2) $javafunc.="    newwindow.document.write('<p>dmf put $stackpath/$stackname2 $stackname2</p>')\n";
    $javafunc.="
    newwindow.document.write('<p>dmf put $modelpath/$modelname threed.0a.mrc</p>');
    newwindow.document.write('<p>echo done');
    newwindow.document.write('<p>&nbsp;<BR></BODY></HTML>');
    newwindow.document.close();
  }
  </SCRIPT>\n";
  }
  processing_header("Eman Job Generator","EMAN Job Generator", $javafunc);

  $numiters=$_POST['numiters'];
  $pad=intval($box*1.25);
  // make sure $pad value is even int
  $pad = ($pad%2==1) ? $pad+=1 : $pad;
  for ($i=1; $i<=$numiters; $i++) {
    $format=$_POST["format".$i];
    $mode=$_POST["mode".$i];
    $magrefine=$_POST["magrefine".$i];
    $defocusrefine=$_POST["defocusrefine".$i];
    $astigrefine=$_POST["astigrefine".$i];
    $fliptilt=$_POST["fliptilt".$i];
    $ewald=$_POST["ewald".$i];
    $matches=$_POST["matches".$i];
    $history=$_POST["history".$i];
    $finalsym=$_POST["finalsym".$i];
    $fomfilter=$_POST["fomfilter".$i];
    $fsc=$_POST["fsc".$i];
    $radius=$_POST["radius".$i];
    $iradius=$_POST["iradius".$i];
    $apix=$_POST["apix".$i];
    $ampcontrast=$_POST["ampcontrast".$i];
    $maskthresh=$_POST["maskthresh".$i];
    $phaseconstant=$_POST["phaseconstant".$i];
    $avgresidual=$_POST["avgresidual".$i];
    $ang=$_POST["ang".$i];
    $itmax=$_POST["itmax".$i];
    $maxmatch=$_POST["maxmatch".$i];
    $psi=$_POST["psi".$i];
    $theta=$_POST["theta".$i];
    $phi=$_POST["phi".$i];
    $deltay=$_POST["deltay".$i];
    $deltax=$_POST["deltax".$i];
    $first=$_POST["first".$i];
    $last=$_POST["last".$i];
    $sym=$_POST["sym".$i];
    $relmag=$_POST["relmag".$i];
    $dstep=$_POST["dstep".$i];
    $targetresidual=$_POST["targetresidual".$i];
    $residualthresh=$_POST["residualthresh".$i];
    $cs=$_POST["cs".$i];
    $kv=$_POST["kv".$i];
    $beamtiltx=$_POST["beamtiltx".$i];
    $beamtilty=$_POST["beamtilty".$i];
    $reslimit=$_POST["reslimit".$i];
    $hp=$_POST["hp".$i];
    $lp=$_POST["lp".$i];
    $bfactor=$_POST["bfactor".$i];
    $stack=$_POST["stack".$i];
    $matchstack=$_POST["matchstack".$i];
    $inpar=$_POST["inpar".$i];
    $outpar=$_POST["outpar".$i];
    $outshiftpar=$_POST["outshiftpar".$i];
    $invol=$_POST["invol".$i];
    $weight3d=$_POST["weight3d".$i];
    $oddvol=$_POST["oddvol".$i];
    $evenvol=$_POST["evenvol".$i];
    $outresidual=$_POST["outresidual".$i];
    $pointspreadvol=$_POST["pointspreadvol".$i];

    $line="\nrunfrealign.py $i --format=$format  --mode=$mode --ewald=$ewald --fsc=$fsc  --radius=$radius  --iradius=$iradius  --apix=$apix  --ampcontrast=$ampcontrast  --maskthresh=$maskthresh  --phaseconstant=$phaseconstant  --avgresidual=$avgresidual  --ang=$ang  --itmax=$itmax  --maxmatch=$maxmatch --first=$first  --last=$last  --sym=$sym  --relmag=$relmag  --dstep=$dstep  --targetresidual=$targetresidual  --residualthresh=$residualthresh  --cs=$cs  --kv=$kv  --beamtiltx=$beamtiltx  --beamtilty=$beamtilty  --reslimit=$reslimit  --hp=$hp  --lp=$lp  --bfactor=$bfactor  --stack=$stack  --matchstack=$matchstack  --inpar=$inpar  --outpar=$outpar  --outshiftpar=$outshiftpar  --invol=$invol  --weight3d=$weight3d  --oddvol=$oddvol  --evenvol=$evenvol  --outresidual=$outresidual  --pointspreadvol=$pointspreadvol";
    if ($magrefine=='on') $line.=" --magrefine='T'";
    if ($defocusrefine=='on') $line.=" --defocusrefine='T'";
    if ($astigrefine=='on') $line.=" --astigrefine='T'";
    if ($fliptilt=='on') $line.=" --fliptilt='T'";
    if ($matches=='on') $line.=" --matches='T'";
    if ($history=='on') $line.=" --history='T'";
    if ($finalsym=='on') $line.=" --finalsym='T'";
    if ($fomfilter=='on') $line.=" --fomfilter='T'";
    if ($psi=='on') $line.=" --psi=1";
    if ($phi=='on') $line.=" --phi=1";
    if ($theta=='on') $line.=" --theta=1";
    if ($deltax=='on') $line.=" --deltax=1";
    if ($deltay=='on') $line.=" --deltay=1";

    $line.=" > runfrealign".$i.".txt\n";
    $clusterjob.= $line;
  }

	
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
  if (!$extra) {
    if ($clustername=='garibaldi') {
      echo "Please review your job below.<BR>";
      echo "If you are satisfied:<BR>\n";
      echo "1) Place files in DMF<BR>\n";
      echo "2) Once this is done, click the button to launch your job.<BR>\n";
      echo"<input type='button' NAME='dmfput' VALUE='Put files in DMF' onclick='displayDMF()'><P>\n";
      echo"<input type='hidden' NAME='dmfpath' VALUE=''>\n";
    }
    else echo "Review your job, and submit.<br />\n";
  }
  else {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo "<FORM NAME='emanjob' METHOD='POST' ACTION='$formAction'><BR>\n";
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
      obj.format1.value = 'M';
      obj.mode1.value = '1';
      obj.magrefine1.checked = false;
      obj.defocusrefine1.checked = false;
      obj.astigrefine1.checked = false;
      obj.fliptilt1.checked = false;
      obj.ewald1.value = '0';
      obj.matches1.checked = false;
      obj.history1.checked = false;
      obj.finalsym1.checked = true;
      obj.fomfilter1.checked = false;
      obj.fsc1.value = '0';
      obj.radius1.value = '146';
      obj.iradius1.value = '0';
      obj.ampcontrast1.value = '0.07';
      obj.maskthresh1.value = '0.0';
      obj.phaseconstant1.value = '100';
      obj.avgresidual1.value = '35';
      obj.ang1.value = '200';
      obj.itmax1.value = '50';
      obj.maxmatch1.value = '10';
      obj.psi1.checked = true;
      obj.theta1.checked = true;
      obj.phi1.checked = true;
      obj.deltax1.checked = true;
      obj.deltay1.checked = true;
      obj.first1.value = '1';
      obj.last1.value = '200';
      obj.relmag1.value = '1';
      obj.dstep1.value = '14.0';
      obj.targetresidual1.value = '25.0';
      obj.residualthresh1.value = '90.0';
      obj.beamtiltx1.value = '0.0';
      obj.beamtilty1.value = '0.0';
      obj.reslimit1.value = '10.0';
      obj.hp1.value = '100.0';
      obj.lp1.value = '35';
      obj.bfactor1.value = '0.0';
      obj.matchstack1.value = 'match.mrc';
      obj.inpar1.value = 'inpar.par';
      obj.outpar1.value = 'outpar.par';
      obj.outshiftpar1.value = 'shift.par';
      obj.weight3d1.value = 'weights.mrc';
      obj.oddvol1.value = 'odd.mrc';
      obj.evenvol1.value = 'even.mrc';
      obj.outresidual1.value = 'phasediffs.mrc';
      obj.pointspreadvol1.value = 'pointspread.mrc';
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
