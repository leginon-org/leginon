<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Eman Job for submission to a cluster
 */

require ('inc/processing.inc');
require ('inc/viewer.inc');
require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');

if ($_POST['write']) {
  if (!$_POST['nodes']) jobForm("ERROR: No nodes specified, setting default=4");
  if (!$_POST['ppn']) jobForm("ERROR: No processors per node specified, setting default=4");
  if ($_POST['ppn'] > 4) jobForm("ERROR: Max processors per node is 4");
  if (!$_POST['walltime']) jobForm("ERROR: No walltime specified, setting default=240");
  if ($_POST['walltime'] > 240) jobForm("ERROR: Max walltime is 240");
  if (!$_POST['cput']) jobForm("ERROR: No CPU time specified, setting default=240");
  if ($_POST['cput'] > 240) jobForm("ERROR: Max CPU time is 240");
  if (!$_POST['rprocs']) jobForm("ERROR: No refinement ppn specified, setting default=4");
  if ($_POST['rprocs'] > $_POST['ppn'])
    jobForm("ERROR: Asking to refine on more processors than available");
  if (!$_POST['dmfpath']) jobForm("ERROR: No DMF path specified");
  if (!$_POST['dmfmod']) jobForm("ERROR: No starting model");
  if (!$_POST['dmfstack']) jobForm("ERROR: No stack file");
  for ($i=1; $i<=$_POST['numiters']; $i++) {
    if (!$_POST['ang'.$i]) jobForm("ERROR: no angular increment set for iteration $i");
    if (!$_POST['mask'.$i]) jobForm("ERROR: no mask set for iteration $i");
  }
  writeJobFile();
}

elseif ($_POST['submitstackmodel'] || $_POST['duplicate']) {
  if (!$_POST['model']) stackModelForm("ERROR: no initial model selected");
  if (!$_POST['stackval']) stackModelForm("ERROR: no stack selected");
  ## make sure that box sizes are the same
  ## get stack data
  $stackinfo = explode('|--|',$_POST['stackval']);
  $stackbox = $stackinfo[2];
  ## get model data
  $modelinfo = explode('|--|',$_POST['model']);
  $modbox = $modelinfo[2];
  if ($stackbox != $modbox) stackModelForm("ERROR: model and stack must have same box size");
  jobForm();
}

else stackModelForm();

function stackModelForm($extra=False) {
  // check if session provided
  $expId = $_GET['expId'];
  if ($expId) {
    $sessionId=$expId;
    $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  }
  else {
    $sessionId=$_POST['sessionId'];
    $formAction=$_SERVER['PHP_SELF'];
  }


  // if user wants to use templates from another project

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
  // find each stack entry in database
  // THIS IS REALLY, REALLY SLOW
  $stackIds = $particle->getStackIds($sessionId);
  $stackinfo=explode('|--|',$_POST['stackval']);
  $stackidval=$stackinfo[0];
  $apix=$stackinfo[1];
  $box=$stackinfo[2];
  $javafunc="
  <script src='js/viewer.js'></script>
  <SCRIPT LANGUAGE='JavaScript'>
  function displayDMF() {
    stack = document.viewerform.stackval.value;
    stackinfo = stack.split('|--|');
    pathinfo = stackinfo[3].split('/');
    dpath='';
    newwindow=window.open('','name','height=250, width=800')
    newwindow.document.write('<HTML><BODY>')

    for (i=3; i<pathinfo.length; i++) {
      dpath=dpath+pathinfo[i]+'/';

    }
    newwindow.document.write('dmf mkdir -p '+dpath+'<BR/><BR/>');
    newwindow.document.write('dmf put '+stackinfo[3]+'/'+stackinfo[4]+' '+dpath+stackinfo[4]+'<BR/><BR/>')
    if (stackinfo[5]) {
      newwindow.document.write('dmf put '+stackinfo[3]+'/'+stackinfo[5]+' '+dpath+stackinfo[5]+'<BR/><BR/>')
    }
    newwindow.document.write('&nbsp;<BR></BODY></HTML>');
    newwindow.document.close();
  }
  </SCRIPT>\n";
  //newwindow.document.write('dmf mkdir '+dpath+'<BR>');
  writeTop("Eman Job Generator","EMAN Job Generator",$javafunc);

  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo "<FORM NAME='viewerform' METHOD='POST' ACTION='$formaction'>
  <B>Select Project:</B><BR>
  <SELECT NAME='projectId' onchange='newexp()'>\n";

  foreach ($projects as $k=>$project) {
    $sel = ($project['id']==$projectId) ? "selected" : '';
    echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
  }
  echo"
  </select>
  <P>
  Stack:";
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
    echo">$stackid[stackid] ($nump particles, $apix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
  }
  echo "</SELECT>\n";
  echo"<INPUT TYPE='button' NAME='dmfput' VALUE='Put stack in DMF' onclick='displayDMF()'><P>\n";
  echo"<INPUT TYPE='hidden' NAME='dmfpath' VALUE=''>\n";
  # show initial models
  echo "Model:<BR>\n";
  if (count($models)>0) {
    foreach ($models as $model) {
      echo "<TABLE CLASS='tableborder' BORDER='1' CELLSPACING='1' CELLPADDING='2'>\n";
# get list of png files in directory
      $pngfiles=array();
      $modeldir= opendir($model['path']);
      while ($f = readdir($modeldir)) {
  if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;
      }
      sort($pngfiles);

# display starting models
      $sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
      echo "<TR><TD COLSPAN=2>\n";
      $modelvals="$model[DEF_id]|--|$model[name]|--|$model[boxsize]|--|$sym[symmetry]";
      echo "<INPUT TYPE='RADIO' NAME='model' VALUE='$modelvals'><B>Use Model ID: $model[DEF_id]</B><BR>\n";
      foreach ($pngfiles as $snapshot) {
  $snapfile = $model['path'].'/'.$snapshot;
  echo "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
      }
      echo "</TD>\n";
      echo "</TR>\n";
      echo"<TR><TD COLSPAN=2>$model[description]</TD></TR>\n";
      echo"<TR><TD COLSPAN=2>$model[path]/$model[name]</TD></TR>\n";
      echo"<TR><TD>pixel size:</TD><TD>$model[pixelsize]</TD></TR>\n";
      echo"<TR><TD>box size:</TD><TD>$model[boxsize]</TD></TR>\n";
      echo"<TR><TD>symmetry:</TD><TD>$sym[symmetry]</TD></TR>\n";
      echo"<TR><TD>resolution:</TD><TD>$model[resolution]</TD></TR>\n";
      echo "</TABLE>\n";
      echo "<P>\n";
    }
    echo"<P><INPUT TYPE='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack & model'></FORM>\n";
  }
  else {echo "No models.  <A HREF='uploadmodel.php?expId=$expId'>Upload one now</A>\n";}
  writeBottom();
  exit;
}

function jobForm($extra=false) {
  ## get stack data
  $stackinfo = explode('|--|',$_POST['stackval']);
  $dmfstack = $stackinfo[4];
  $dmfpathdata = explode('/', $stackinfo[3]);
  $dmfpath = '';
  for ($i=3 ; $i<count($dmfpathdata); $i++) {
    $dmfpath .= "$dmfpathdata[$i]/";
  }

  ## get model data
  $modelinfo = explode('|--|',$_POST['model']);
  $dmfmod = $modelinfo[1];
  $syminfo = explode(' ',$modelinfo[3]);
  $modsym=$syminfo[0];
  if ($modsym == 'Icosahedral') $modsym='icos';

  $jobname = ($_POST['jobname']) ? $_POST['jobname'] : '';
  $nodes = ($_POST['nodes']) ? $_POST['nodes'] : 4;
  $ppn = ($_POST['ppn']) ? $_POST['ppn'] : 4;
  $rprocs = ($_POST['rprocs']) ? $_POST['rprocs'] : 4;
  $walltime = ($_POST['walltime']) ? $_POST['walltime'] : 240;
  $cput = ($_POST['cput']) ? $_POST['cput'] : 240;
  $dmfstack = ($_POST['dmfstack']) ? $_POST['dmfstack'] : $dmfstack;
  $dmfpath = ($_POST['dmfpath']) ? $_POST['dmfpath'] : $dmfpath;
  $dmfmod = ($_POST['dmfmod']) ? $_POST['dmfmod'] : $dmfmod;
  $dmfstorech = ($_POST['dmfstore']=='on') ? 'CHECKED' : '';
  $numiters= ($_POST['numiters']) ? $_POST['numiters'] : 1;
  if ($_POST['duplicate']) {
    $numiters+=1;
    $newiter=explode(" ",$_POST['duplicate']);
    $j=$newiter[2];
  }

  else $j=$numiters;
  $javafunc .= defaultReconValues();
  $javafunc .= writeJavaPopupFunctions();
  writeTop("Eman Job Generator","EMAN Job Generator",$javafunc);
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo "
  <FORM NAME='emanjob' METHOD='POST' ACTION='$formaction'><BR/>
  <CENTER><FONT SIZE='+1'>
    <B>Job Name:</B> <INPUT TYPE='text' NAME='jobname' VALUE='$jobname' SIZE=50><BR/><BR/>
  </FONT></CENTER>\n";
  echo "<INPUT TYPE='hidden' NAME='model' VALUE='".$_POST['model']."'>
  <INPUT TYPE='hidden' NAME='stackval' VALUE='".$_POST['stackval']."'>";
  echo"<TABLE BORDER='0' WIDTH='99%'><TR><TD VALIGN='TOP'>"; //overall table

//Cluster Parameters
  echo"
    <TABLE CLASS='tableborder' CELLPADDING=4 CELLSPACING=4>
    <TR>
      <TD COLSPAN='4' ALIGN='CENTER'>
      <H4>PBS Cluster Parameters</H4>
      </TD>
    </TR>
    <TR>
      <TD><A HREF=\"javascript:refinfopopup('nodes')\">Nodes:</A></TD>
      <TD><INPUT TYPE='text' NAME='nodes' VALUE='$nodes' SIZE='4' MAXCHAR='4'></TD>
      <TD><A HREF=\"javascript:refinfopopup('procpernode')\">Proc/Node:</A></TD>
      <TD><INPUT TYPE='text' NAME='ppn' VALUE='$ppn' SIZE='3'></TD>
    </TR>
    <TR>
      <TD><A HREF=\"javascript:refinfopopup('walltime')\">Wall Time:</A></TD>
      <TD><INPUT TYPE='text' NAME='walltime' VALUE='$walltime' SIZE='4'></TD>
      <TD><A HREF=\"javascript:refinfopopup('cputime')\">CPU Time</A></TD>
      <TD><INPUT TYPE='text' NAME='cput' VALUE='$cput' SIZE='4'></TD>
    </TR>
    <TR>
      <TD COLSPAN='4'>
      Refinement procs per node:<INPUT TYPE='text' NAME='rprocs' VALUE='$rprocs' SIZE='3'>
      </TD>
    </TR>
    </TABLE>
    <BR/>";

  echo"</TD><TD VALIGN='TOP'>"; //overall table

//DMF Parameters TABLE
  echo"
    <TABLE CLASS='tableborder' CELLPADDING=4 CELLSPACING=4>
    <TR>
      <TD COLSPAN='4' ALIGN='CENTER'>
      <H4>DMF Parameters</H4>
      </TD>
    </TR>
    <TR>
      <TD>DMF Directory:</TD>
      <TD><INPUT TYPE='text' NAME='dmfpath' VALUE='$dmfpath' SIZE='40' ></TD>
    </TR>
    <TR>
      <TD>Starting Model (mrc):</TD>
      <TD><INPUT TYPE='text' NAME='dmfmod' VALUE='$dmfmod' SIZE='40' ></TD>
    </TR>
    <TR>
      <TD>Stack (img or hed):</TD>
      <TD><INPUT TYPE='text' NAME='dmfstack' VALUE='$dmfstack' SIZE='40' ></TD>
    </TR>
    <TR>
      <TD>Save results to DMF</TD>
      <TD><INPUT TYPE='checkbox' NAME='dmfstore' $dmfstorech></TD>
    </TR>
    </TABLE>\n";
  echo"</TD></TR></TABLE>"; //overall table
  echo"
   <BR/><CENTER>
   <H4>Refine Run Parameters</H4>
   </CENTER><HR/>
  <INPUT TYPE='BUTTON' onClick='sefDefaults(this.form)' VALUE='Set Defaults for Iteration 1'>\n";

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
    $mediann="median".$i;
    $phaseclsn="phasecls".$i;
    $refinen="refine".$i;
    $goodbadn="goodbad".$i;
    $eotestn="eotest".$i;
    $corann="coran".$i;
    $msgpn="msgp".$i;
    $msgp_corcutoffn="msgp_corcutoff".$i;
    $msgp_minptclsn="msgp_minptcls".$i;

    $ang=($i>$j) ? $_POST["ang".($i-1)] : $_POST[$angn];
    $mask=($i>$j) ? $_POST["mask".($i-1)] : $_POST[$maskn];
    $imask=($i>$j) ? $_POST["imask".($i-1)] : $_POST[$imaskn];
    $sym=($i>$j) ? $_POST["sym".($i-1)] : $_POST[$symn];
    $hard=($i>$j) ? $_POST["hard".($i-1)] : $_POST[$hardn];
    $classkeep=($i>$j) ? $_POST["classkeep".($i-1)] : $_POST[$classkeepn];
    $classiter=($i>$j) ? $_POST["classiter".($i-1)] : $_POST[$classitern];
    $filt3d=($i>$j) ? $_POST["filt3d".($i-1)] : $_POST[$filt3dn];
    $shrink=($i>$j) ? $_POST["shrink".($i-1)] : $_POST[$shrinkn];
    $msgp_corcutoff=($i>$j) ? $_POST["msgp_corcutoff".($i-1)] : $_POST[$msgp_corcutoffn];
    $msgp_minptcls=($i>$j) ? $_POST["msgp_minptcls".($i-1)] : $_POST[$msgp_minptclsn];
    ## use symmetry of model by default, but you can change it
    if ($i==1 && !$_POST['duplicate']) $sym=$modsym;

    if ($i>$j) {
           $median=($_POST["median".($i-1)]=='on') ? 'CHECKED' : '';
           $phasecls=($_POST["phasecls".($i-1)]=='on') ? 'CHECKED' : '';
           $refine=($_POST["refine".($i-1)]=='on') ? 'CHECKED' : '';
           $goodbad=($_POST["goodbad".($i-1)]=='on') ? 'CHECKED' : '';
           $eotest=($_POST["eotest".($i-1)]=='on') ? 'CHECKED' : '';
           $coran=($_POST["coran".($i-1)]=='on') ? 'CHECKED' : '';
           $msgp=($_POST[$mspg.($i-1)]=='on') ? 'CHECKED' : '';
    }
    else {
           $median=($_POST[$mediann]=='on') ? 'CHECKED' : '';
           $phasecls=($_POST[$phaseclsn]=='on') ? 'CHECKED' : '';
           $refine=($_POST[$refinen]=='on') ? 'CHECKED' : '';
           $goodbad=($_POST[$goodbadn]=='on') ? 'CHECKED' : '';
           $eotest=($_POST[$eotestn]=='on') ? 'CHECKED' : '';
           $coran=($_POST[$corann]=='on') ? 'CHECKED' : '';
           $msgp=($_POST[$mspgn]=='on') ? 'CHECKED' : '';
    }
    $bgcolor="#E8E8E8";
    echo"
      <P><B>Iteration $i</B><BR/>

      <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
      <TR>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('ang')\">ang:</A>
          <INPUT TYPE='text' NAME='$angn' SIZE='2' VALUE='$ang'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('mask')\">mask:</A>
          <INPUT TYPE='text' NAME='$maskn' SIZE='4' VALUE='$mask'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('imask')\">imask:</A>
          <INPUT TYPE='text' NAME='$imaskn' SIZE='4' VALUE='$imask'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('sym')\">sym:</A>
          <INPUT TYPE='text' NAME='$symn' SIZE='5' VALUE='$sym'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('hard')\">hard:</A>
          <INPUT TYPE='text' NAME='$hardn' SIZE='3' VALUE='$hard'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('classkeep')\">classkeep:</A>
          <INPUT TYPE='text' NAME='$classkeepn' SIZE='4' VALUE='$classkeep'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('classiter')\">classiter:</A>
          <INPUT TYPE='text' NAME='$classitern' SIZE='2' VALUE='$classiter'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('filt3d')\">filt3d:</A>
          <INPUT TYPE='text' NAME='$filt3dn' SIZE='4' VALUE='$filt3d'></TD>
      </TR>
      <TR>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('shrink')\">shrink:</A>
          <INPUT TYPE='text' NAME='$shrinkn' SIZE='2' VALUE='$shrink'></TD>
        <TD BGCOLOR='$bgcolor'>
          <INPUT TYPE='checkbox' NAME='$mediann' $median><A HREF=\"javascript:refinfopopup('median')\">median</A></TD>
        <TD BGCOLOR='$bgcolor'>
          <INPUT TYPE='checkbox' NAME='$phaseclsn' $phasecls><A HREF=\"javascript:refinfopopup('phasecls')\">phasecls</A></TD>
        <TD BGCOLOR='$bgcolor'>
          <INPUT TYPE='checkbox' NAME='$refinen' $refine><A HREF=\"javascript:refinfopopup('refine')\">refine</A></TD>
        <TD BGCOLOR='$bgcolor'>
          <INPUT TYPE='checkbox' NAME='$goodbadn' $goodbad><A HREF=\"javascript:refinfopopup('goodbad')\">goodbad</A></TD>
        <TD BGCOLOR='$bgcolor'>
          <INPUT TYPE='checkbox' NAME='$eotestn' $eotest><A HREF=\"javascript:refinfopopup('eotest')\">eotest</A></TD>
        <TD BGCOLOR='$bgcolor'>
          <INPUT TYPE='checkbox' NAME='$corann' $coran><A HREF=\"javascript:refinfopopup('coran')\">coran</A></TD>
        <TD BGCOLOR='$bgcolor'></TD>
      </TR>
      <TR>
	<TD colspan=6 BGCOLOR='$bgcolor' CELLPADDING=0 CELLSPACING=0>
	  <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4 WIDTH=100%>
            <TR>
        <TD BGCOLOR='$bgcolor'><INPUT TYPE='checkbox' NAME='$msgpn'><A HREF=\"javascript:refinfopopup('msgp')\">Subclassification by message passing:</A></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('msgp_corcutoff')\">CorCutoff:</A>
          <INPUT TYPE='text' NAME='$msgp_corcutoffn' SIZE='4' VALUE='$msgp_corcutoff'></TD>
        <TD BGCOLOR='$bgcolor'><A HREF=\"javascript:refinfopopup('msgp_minptcls')\">MinPtcls:</A>
          <INPUT TYPE='text' NAME='$msgp_minptclsn' SIZE='4' VALUE='$msgp_minptcls'></TD>
            </TR>
          </TABLE>
        <TD colspan=2 BGCOLOR='$bgcolor' ALIGN='CENTER'>
          <INPUT TYPE='SUBMIT' NAME='duplicate' VALUE='Duplicate Iteration $i'></TD>
      </TR>
      </TABLE>\n";
  }
  echo"
  <INPUT TYPE='hidden' NAME='numiters' VALUE='$numiters'><P>
  <INPUT TYPE='SUBMIT' NAME='write' VALUE='Create Job File'>
  </FORM>\n";
  writeBottom();
  exit;
}

function writeJobFile () {
  // get the stack info (pixel size, box size)
  $stackinfo=explode('|--|',$_POST['stackval']);
  $stackidval=$stackinfo[0];
  $apix=$stackinfo[1];
  $box=$stackinfo[2];

  // get the model id
  $modelinfo=explode('|--|',$_POST['model']);
  $modelid=$modelinfo[0];
  echo "<PRE>\n";
  $dmfpath=$_POST['dmfpath'];
  // make sure dmf store dir ends with '/'
  if (substr($dmfpath,-1,1)!='/') $dmfpath.='/';
  if ($_POST['jobname']) echo "# ".$_POST['jobname']."\n";
  echo "# stackId: $stackidval\n";
  echo "# modelId: $modelid\n";
  echo "#PBS -l nodes=".$_POST['nodes'].":ppn=".$_POST['ppn']."\n";
  echo "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
  echo "#PBS -l cput=".$_POST['cput'].":00:00\n";
  echo "#PBS -m e\n";
  echo "#PBS -r n\n";
  echo "\ncd \$PBSREMOTEDIR\n";
  // get file name, strip extension
  $ext=strrchr($_POST['dmfstack'],'.');
  $stackname=substr($_POST['dmfstack'],0,-strlen($ext));
  echo "\ndmf get $dmfpath".$_POST['dmfmod']." threed.0a.mrc\n";
  echo "dmf get $dmfpath$stackname.hed start.hed\n";
  echo "dmf get $dmfpath$stackname.img start.img\n";
  echo "\nforeach i (`sort -u \$PBS_NODEFILE`)\n";
  echo "  echo 'rsh 1 ".$_POST['rprocs']."' \$i \$PBSREMOTEDIR >> .mparm\n";
  echo "end\n";
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
    $median=$_POST["median".$i];
    $phasecls=$_POST["phasecls".$i];
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
    if ($median=='on') $line.=" median";
    if ($phasecls=='on') $line.=" phasecls";
    if ($refine=='on') $line.=" refine";
    if ($goodbad=='on') $line.=" goodbad";
    $line.=" > refine".$i.".txt\n";
    $line.="getProjEulers.py proj.img proj.$i.txt\n";
    if ($eotest=='on') {
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
    if ($coran=='on') {
      $line .="coran_for_cls2.py mask=$mask proc=$procs iter=$i";
      if ($sym) $line .= " sym=$sym";
      if ($hard) $line .= " hard=$hard";
      $line .= "\n";
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
    echo $line;
  }
  if ($_POST['dmfstore']=='on') {
    echo "\ntar -cvzf model.tar.gz threed.*a.mrc\n";
    echo "dmf put model.tar.gz $dmfpath\n";
    $line = "\ntar -cvzf results.tar.gz fsc* tcls* refine.* particle.* classes.* proj.* sym.* .emanlog *txt ";
    if ($msgp=='on') {
	$line .= "goodavgs.* ";
	$line .= "msgPassing_subClassification.log ";
	echo "dmf put msgPassing.tar $dmfpath\n";
    }
    $line .= "\n";
    echo $line;
    echo "dmf put results.tar.gz $dmfpath\n";
  }
  echo "\nexit\n\n";
  echo "</PRE>\n";
  exit;
};

function defaultReconValues () {
  $javafunc = "
  <SCRIPT LANGUAGE='JavaScript'>
    function sefDefaults(obj) {
      obj.ang1.value = '4.0';
      obj.mask1.value = '180.0';
      obj.imask1.value = '0.0';
      //obj.sym1.value = '3.4';
      obj.hard1.value = '25';
      obj.classkeep1.value = '0.8';
      obj.classiter1.value = '8';
      obj.filt3d1.value = '15.0';
      obj.shrink1.value = '1';
      obj.median1.checked = true;
      obj.phasecls1.checked = true;
      obj.refine1.checked = true;
      obj.goodbad1.checked = true;
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
    } else if (infoname=='mask') {
      newwindow.document.write('Radius of external mask');
    } else if (infoname=='imask') {
      newwindow.document.write('Radius of internal mask');
    } else if (infoname=='sym') {
      newwindow.document.write('Imposes symmetry on the model, omit this option for no/unknown symmetry<BR/>Examples: c1, c2, d7, etc.');
    } else if (infoname=='hard') {
      newwindow.document.write('Hard limit for <I>make3d</I> program. This specifies how well the class averages must match the model to be included, 25 is typical');
    } else if (infoname=='classkeep') {
      newwindow.document.write('Classkeep is the keep value for <I>classalignall</I> program. The threshold value for keeping images. Standard deviation multiplier');
    } else if (infoname=='classiter') {
      newwindow.document.write('Classiter is the interation value for <I>classalignall</I> program. Number of iterative loops');
    } else if (infoname=='filt3d') {
      newwindow.document.write('Radius of lowpass filter applied to the model after each iteration.');
    } else if (infoname=='shrink') {
      newwindow.document.write('<I>Experimental</I>, shrinks images at several points for faster runs');
    } else if (infoname=='median') {
      newwindow.document.write('Specify this when CTF correction is NOT being performed');
    } else if (infoname=='phasecls') {
      newwindow.document.write('Uses weighted mean phase error for classification (<I>experimental</I>)');
    } else if (infoname=='refine') {
      newwindow.document.write('This will do subpixel alignment of the particle translations for classification and averaging. May have a significant impact at higher resolutions.');
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

