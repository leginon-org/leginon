<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Frealign Job for submission to a cluster
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
	if (!$_POST['radius']) jobForm("ERROR: Enter an outer radius");
	writeJobFile();
}

elseif ($_POST['submitstackmodel'] || $_POST['import']) {
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
		$projectId = $_POST['projectId'];
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
		processing_header("Frealign Job Generator","Frealign Job Generator",$javafunc);
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
	//  show initial models
	echo "<P><B>Model:</B><BR><A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><BR/>\n";
	if (!$modelonly) echo"<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'><BR/>\n";
	echo "<P>\n";
	$minf = explode('|--|',$_POST['model']);
	if (is_array($models) && count($models)>0) {
	  foreach ($models as $model) {
	    echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
	    // get list of png files in directory
	    $pngfiles=array();
	    $modeldir= opendir($model['path']);
	    while ($f = readdir($modeldir)) {
	      if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;
	    }
	    sort($pngfiles);
	    
	    // display starting models
	    $sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
	    echo "<tr><TD COLSPAN=2>\n";
	    $modelvals="$model[DEF_id]|--|$model[path]|--|$model[name]|--|$model[boxsize]|--|$sym[symmetry]";
	    if (!$modelonly) {
	      echo "<input type='RADIO' NAME='model' VALUE='$modelvals' ";
	      // check if model was selected
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
	$projectId = $_POST['projectId'];
  
	## get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = $sessiondata['Image path'];
	$sessionpath = ereg_replace("leginon","appion",$sessionpath);
	$sessionpath = ereg_replace("rawdata","recon/",$sessionpath);

	$particle = new particledata();
	$reconruns = count($particle->getJobIdsFromSession($expId));
	$defrunid = 'frealign_recon'.($reconruns+1);

	## get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$nump=$particle->getNumStackParticles($stackidval);
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
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];
	$dmfmod = $modelinfo[2];
	$syminfo = explode(' ',$modelinfo[4]);
	$modsym=$syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	$jobname = ($_POST['jobname']) ? $_POST['jobname'] : $defrunid;
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$refcycles = ($_POST['refcycles']) ? $_POST['refcycles'] : '';

	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : 1;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : 8;

	// preset information from stackid
	$presetinfo = $particle->getPresetFromStackId($stackidval);
	$kv = $presetinfo['hightension']/1e3;
	$cs = 2.0;

	$javafunc .= defaultReconValues($box,$apix);
	$javafunc .= writeJavaPopupFunctions('frealign');
	processing_header("Frealign Job Generator","Frealign Job Generator",$javafunc);
	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";

	echo "<form name='frealignjob' method='post' action='$formaction'><br />\n";
	echo "<p>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>\n";
	echo "<td><b>Job Run Name:</b></td>\n";
	echo "<td><input type='text' name='jobname' value='$jobname' size=20></td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td><B>Output Directory:</B></td>\n";
	echo "<td><input type='text' NAME='outdir' VALUE='$outdir' SIZE=50></td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td>Starting Model (mrc):</td>\n";
	echo "<td>$modelpath/$modelname</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td>Stack:</td>\n";
	echo "<td>$stackpath/$stackname1</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td>Nodes:</td>\n";
	echo "<td><input type='text' NAME='nodes' VALUE='$nodes' SIZE='4' MAXCHAR='4'></td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td>Proc/Node:</td>\n";
	echo "<td><input type='text' NAME='ppn' VALUE='$ppn' SIZE='3'></td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo closeRoundBorder();


	###set default values that iterate
	//$magrefine= $_POST["magrefine"];
	//$defocusrefine=$_POST[$defocusrefinen];
	//$astigrefine=() ? $_POST["astigrefine"] : $_POST[$astigrefinen];
	//$fliptilt=() ? $_POST["fliptilt"] : $_POST[$fliptiltn];
	//$ewald=() ? $_POST["ewald"] : $_POST[$ewaldn];
	//$matches=() ? $_POST["matches"] : $_POST[$matchesn];
	//$history=() ? $_POST["history"] : $_POST[$historyn];
	//$finalsym=() ? $_POST["finalsym"] : $_POST[$finalsymn];
	//$fomfilter=() ? $_POST["fomfilter"] : $_POST[$fomfiltern];
	//$fsc=() ? $_POST["fsc"] : $_POST[$fscn];
	$radius=$_POST["radius"];
	$iradius=$_POST["iradius"];
	$ampcontrast=$_POST["ampcontrast"];
	$maskthresh=$_POST['maskthresh'];
	$phaseconstant=$_POST['phaseconstant'];
	$avgresidual=$_POST['avgresidual'];
	$ang=$_POST['ang'];
	$itmax=$_POST['itmax'];
	$maxmatch=$_POST['maxmatch'];
	//$psi=$_POST[$psin];
	//$theta=$_POST[$thetan];
	//$phi=$_POST[$phin];
	//$deltax=$_POST[$deltaxn];
	//$deltay=$_POST[$deltayn];
	$targetresidual=$_POST['targetresidual'];
	$residualthresh=$_POST['residualthresh'];
	//$beamtiltx=$_POST[$beamtiltxn];
	//$beamtilty=$_POST[$beamtiltyn];
	$hp=$_POST['hp'];
	$lp=$_POST['lp'];
	$bfactor=$_POST['bfactor'];
	$sym = ($_POST['sym']) ? $_POST['sym'] : $modsym;
	$angcheck = ($_POST['initorientmethod']=='projmatch' || !$_POST['write']) ? 'checked' : '';
	$inparfilecheck = ($_POST['initorientmethod']=='inparfile') ? 'checked' : '';

	$bgcolor="#E8E8E8";
	echo "<br />\n";
	echo "<h4 style='align=\'center\' >Frealign Reconstruction Parameters</h4>\n";
	echo "<hr />\n";
	echo "<input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults'>\n";
	echo "<br />\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td>\n";
	echo "<b>Initial Orientations</b><br />\n";
	echo "<input type='radio' name='initorientmethod' value='projmatch' $angcheck>\n";
	echo docpop('ang',"Determine with Frealign - Ang incr:");
	echo " <input type='type' name='ang' value='$ang' size='4'>\n";
	echo "<br />\n";
	echo "<input type='radio' name='initorientmethod' value='inparfile' $inparfilecheck>\n";
	echo docpop('inpar',"Use input Frealign parameter file:");
	echo " <input type='type' name='inparfile' value='$inparfile' size='50'>\n";
	echo "</td></tr>\n";
	echo "</table>\n";
	echo closeRoundBorder();
	echo "<br />\n";
	$reslimit=($_POST['reslimit']) ? $_POST['reslimit'] : (ceil($apix*20))/10;

	//$magrefine=($_POST[$magrefinen]=='on') ? 'CHECKED' : '';
	//$defocusrefine=($_POST[$defocusrefinen]=='on') ? 'CHECKED' : '';
	//$astigrefine=($_POST[$astigrefinen]=='on') ? 'CHECKED' : '';
	//$fliptilt=($_POST[$fliptiltn]=='on') ? 'CHECKED' : '';
	//$matches=($_POST[$matchesn]=='on') ? 'CHECKED' : '';
	//$history=($_POST[$historyn]=='on') ? 'CHECKED' : '';
	//$finalsym=($_POST[$finalsymn]=='on') ? 'CHECKED' : '';
	//$fomfilter=($_POST[$fomfiltern]=='on') ? 'CHECKED' : '';
	//$psi=($_POST[$psin]=='on') ? 'CHECKED' : '';
	//$theta=($_POST[$thetan]=='on') ? 'CHECKED' : '';
	//$phi=($_POST[$phin]=='on') ? 'CHECKED' : '';
	//$deltax=($_POST[$deltaxn]=='on') ? 'CHECKED' : '';
	//$deltay=($_POST[$deltayn]=='on') ? 'CHECKED' : '';

	// commenting out lots of the advanced options for now
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l2\" onMouseOver='popLayer(\"magrefine\", \"l2\")' onMouseOut='hideLayer()'>magrefine</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$magrefinen' $magrefine></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l3\" onMouseOver='popLayer(\"defocusrefine\", \"l3\")' onMouseOut='hideLayer()'>defocusrefine</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$defocusrefinen' $defocusrefine></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l5\" onMouseOver='popLayer(\"fliptilt\", \"l5\")' onMouseOut='hideLayer()'>fliptilt</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$fliptiltn' $fliptilt></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l4\" onMouseOver='popLayer(\"astigrefine\", \"l4\")' onMouseOut='hideLayer()'>astigrefine</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$astigrefinen' $astigrefine></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l6\" onMouseOver='popLayer(\"ewald\", \"l6\")' onMouseOut='hideLayer()'>ewald</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='text' NAME='$ewaldn' SIZE='3' VALUE='$ewald'></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l7\" onMouseOver='popLayer(\"matches\", \"l7\")' onMouseOut='hideLayer()'>matches</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$matchesn' $matches></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l8\" onMouseOver='popLayer(\"history\", \"l8\")' onMouseOut='hideLayer()'>history</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$historyn' $history></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l9\" onMouseOver='popLayer(\"finalsym\", \"l8\")' onMouseOut='hideLayer()'>finalsym</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$finalsymn' $finalsym></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l10\" onMouseOver='popLayer(\"fomfilter\", \"l10\")' onMouseOut='hideLayer()'>fomfilter</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$fomfiltern' $fomfilter></td>\n";
	//echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l11\" onMouseOver='popLayer(\"fsc\", \"l11\")' onMouseOut='hideLayer()'>fsc</a></font></td>\n";
	//echo "<td bgcolor='$rcol'><input type='text' NAME='$fscn' SIZE='3' VALUE='$fsc'></td>\n";
	echo "<table class='tableborder' border='1' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>\n";
	echo "<td>\n";

	$paramlist = array('radius','iradius','ampcontrast','maskthresh','phaseconstant','avgresidual','itmax','maxmatch','sym','targetresidual','residualthresh','reslimit','hp','lp','bfactor');

	echo "<table>\n";
	echo "<tr>\n";

	foreach ($paramlist as $p) {
		echo "<td align='center' bgcolor='$bgcolor'><font class='sf'>\n";
		echo docpop($p,$p);
		echo "</font></td>\n";
	}
	echo "</tr>\n";
	echo "<tr>\n";
	foreach ($paramlist as $p) {
		echo "<td bgcolor='$rcol'><input type='text' NAME='$p' SIZE='4' VALUE='${$p}'></td>\n";
	}
	echo "</tr>\n";

      //echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l22\" onMouseOver='popLayer(\"psi\", \"l22\")' onMouseOut='hideLayer()'>psi</a></font></td>\n";
      //echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$psin' $psi></td>\n";
      //echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l23\" onMouseOver='popLayer(\"theta\", \"l23\")' onMouseOut='hideLayer()'>theta</a></font></td>\n";
      //echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$thetan' $theta></td>\n";
      //echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l24\" onMouseOver='popLayer(\"phi\", \"l24\")' onMouseOut='hideLayer()'>phi</a></font></td>\n";
      //echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$phin' $phi></td>\n";
      //echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l25\" onMouseOver='popLayer(\"deltax\", \"l25\")' onMouseOut='hideLayer()'>deltax</a></font></td>\n";
      //echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$deltaxn' $deltax></td>\n";
      //echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l26\" onMouseOver='popLayer(\"deltay\", \"l26\")' onMouseOut='hideLayer()'>deltay</a></font></td>\n";
      //echo "<td bgcolor='$rcol'><input type='checkbox' NAME='$deltayn' $deltay></td>\n";
      //echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l36\" onMouseOver='popLayer(\"beamtiltx\", \"l36\")' onMouseOut='hideLayer()'>beamtiltx</a></font></td>\n";
      //echo "<td bgcolor='$rcol'><input type='text' NAME='$beamtiltxn' SIZE='3' VALUE='$beamtiltx'></td>\n";
      //echo "<td align='center' bgcolor='$bgcolor'><font class='sf'><a href='#' id=\"l37\" onMouseOver='popLayer(\"beamtilty\", \"l37\")' onMouseOut='hideLayer()'>beamtilty</a></font></td>\n";
      //echo "<td bgcolor='$rcol'><input type='text' NAME='$beamtiltyn' SIZE='3' VALUE='$beamtilty'></td>\n";
	echo "</table>\n";
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "<br />\n";
	echo "Refinement Cycles: ";
	echo "<input type='text' name='refcycles' value='$refcycles' size='3'>\n";
	echo "
  <input type='hidden' NAME='cs' value='$cs'>
  <input type='hidden' NAME='kv' value='$kv'>
  <input type='hidden' NAME='last' value='$nump'>
  <input type='hidden' NAME='apix' value='$apix'>
  <input type='hidden' name='projectId' value='$projectId'><P>
  <input type='submit' name='write' value='Create Job File'>
  </form>\n";
	if ($guppycheck) echo "<script language='javascript'>enableGaribaldi('false')</script>\n";
	processing_footer();
	exit;
}

function writeJobFile ($extra=False) {
	$expId = $_GET['expId'];
	$projectId = $_POST['projectId'];
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
	processing_header("Frealign Job Generator","Frealign Job Generator", $javafunc);

	$pad=intval($box*1.25);
	// make sure $pad value is even int
	$pad = ($pad%2==1) ? $pad+=1 : $pad;

	$apix=$_POST["apix"];
	$last=$_POST['last'];
	$cs=$_POST['cs'];
	$kv=$_POST['kv'];
	
	//$magrefine=$_POST["magrefine"];
	//$defocusrefine=$_POST["defocusrefine"];
	//$astigrefine=$_POST["astigrefine"];
	//$fliptilt=$_POST["fliptilt"];
	//$ewald=$_POST["ewald"];
	//$matches=$_POST["matches"];
	//$history=$_POST["history"];
	//$finalsym=$_POST["finalsym"];
	//$fomfilter=$_POST["fomfilter"];
	//$fsc=$_POST["fsc"];
	$radius=$_POST["radius"];
	$iradius=$_POST["iradius"];
	$ampcontrast=$_POST["ampcontrast"];
	$maskthresh=$_POST["maskthresh"];
	$phaseconstant=$_POST["phaseconstant"];
	$avgresidual=$_POST["avgresidual"];
	$ang = ($_POST['initorientmethod']=='projmatch') ? $_POST["ang"] : '';
	$itmax=$_POST["itmax"];
	$maxmatch=$_POST["maxmatch"];
	//$psi=$_POST["psi"];
	//$theta=$_POST["theta"];
	//$phi=$_POST["phi"];
	//$deltay=$_POST["deltay"];
	//$deltax=$_POST["deltax"];
	$sym=$_POST["sym"];
	$targetresidual=$_POST["targetresidual"];
	$residualthresh=$_POST["residualthresh"];
	//$beamtiltx=$_POST["beamtiltx"];
	//$beamtilty=$_POST["beamtilty"];
	$reslimit=$_POST['reslimit'];
	$hp=$_POST["hp"];
	$lp=$_POST["lp"];
	$bfactor=$_POST["bfactor"];
	$setuponly=$_POST["setuponly"];
	$refcycles=$_POST['refcycles'];
	
	$line="\nrunfrealign.py -n $jobname --radius=$radius --iradius=$iradius --apix=$apix ";
	$line.="--ampcontrast=$ampcontrast --maskthresh=$maskthresh --phaseconstant=$phaseconstant --avgresidual=$avgresidual --itmax=$itmax ";
	$line.="--maxmatch=$maxmatch --last=$last --sym=$sym --targetresidual=$targetresidual --residualthresh=$residualthresh ";
	$line.="--cs=$cs --kv=$kv --reslimit=$reslimit --hp=$hp --lp=$lp --bfactor=$bfactor";
	if ($ang) $line.= " --ang=$ang";
	//if ($magrefine=='on') $line.=" --magrefine='T'";
	//if ($defocusrefine=='on') $line.=" --defocusrefine='T'";
	//if ($astigrefine=='on') $line.=" --astigrefine='T'";
	//if ($fliptilt=='on') $line.=" --fliptilt='T'";
	//if ($matches=='on') $line.=" --matches='T'";
	//if ($history=='on') $line.=" --history='T'";
	//if ($finalsym=='on') $line.=" --finalsym='T'";
	//if ($fomfilter=='on') $line.=" --fomfilter='T'";
	//if ($psi=='on') $line.=" --psi=1";
	//if ($phi=='on') $line.=" --phi=1";
	//if ($theta=='on') $line.=" --theta=1";
	//if ($deltax=='on') $line.=" --deltax=1";
	//if ($deltay=='on') $line.=" --deltay=1";
	if ($refcycles) $line.= " --refcycles=$refcycles";
	if ($setuponly=='on') $line.=" --setuponly";
	//
	//appion specific options
	//
	
	$line .=" --stackid=$stackidval";
	$line.=" --modelid=$modelid";
	$line.=" --project=$projectId";
	
	$line.=" > runfrealign".$i.".txt\n";
	$clusterjob.= $line;
 
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
	echo "<FORM NAME='frealignjob' METHOD='POST' ACTION='$formAction'><BR>\n";
	echo "<input type='hidden' name='clustername' value='$clustername'>\n";
	echo "<input type='HIDDEN' NAME='clusterpath' VALUE='$clusterpath'>\n";
	echo "<input type='HIDDEN' NAME='dmfpath' VALUE='$dmfpath'>\n";
	echo "<input type='HIDDEN' NAME='jobname' VALUE='$jobname'>\n";
	echo "<input type='HIDDEN' NAME='outdir' VALUE='$outdir'>\n";
	// convert \n to /\n's for script
	$header_conv=preg_replace('/\n/','|--|',$header);
	echo "<input type='HIDDEN' NAME='header' VALUE='$header_conv'>\n";
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

function defaultReconValues ($box, $apix) {
  $rad = ($box/2)-2;
  $lp1val = (ceil($apix*40))/10;
  $javafunc = "
  <script type='text/javascript'>
    function setDefaults(obj) {\n";
  //obj.magrefine1.checked = false;
  //obj.defocusrefine1.checked = false;
  //obj.astigrefine1.checked = false;
  //obj.fliptilt1.checked = false;
  //obj.ewald1.value = '0';
  //obj.matches1.checked = true;
  //obj.history1.checked = false;
  //obj.finalsym1.checked = true;
  //obj.fomfilter1.checked = true;
  //obj.fsc1.value = '0';
  //obj.psi1.checked = true;
  //obj.theta1.checked = true;
  //obj.phi1.checked = true;
  //obj.deltax1.checked = true;
  //obj.deltay1.checked = true;
  //obj.beamtiltx1.value = '0.0';
  //obj.beamtilty1.value = '0.0';
  $javafunc.="obj.iradius.value = '0';
      obj.ampcontrast.value = '0.07';
      obj.maskthresh.value = '0.0';
      obj.phaseconstant.value = '3.0';
      obj.avgresidual.value = '75';
      obj.ang.value = '5';
      obj.itmax.value = '10';
      obj.maxmatch.value = '0';
      obj.targetresidual.value = '10.0';
      obj.residualthresh.value = '90.0';
      obj.hp.value = '100.0';
      obj.lp.value = '".$lp1val."';
      obj.bfactor.value = '0.0';
      obj.setuponly.value = false;
      return;
    }
  </SCRIPT>\n";
  return $javafunc;
};

