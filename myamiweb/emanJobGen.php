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
        if ($_POST['rprocs'] > $_POST['ppn']) jobForm("ERROR: Asking to refine on more processors than available");
	if (!$_POST['dmfpath']) jobForm("ERROR: No DMF path specified");
        if (!$_POST['dmfmod']) jobForm("ERROR: No starting model");
	if (!$_POST['dmfstack']) jobForm("ERROR: No stack file");
	for ($i=1; $i<=$_POST['numiters']; $i++) {
	        if (!$_POST['ang'.$i]) jobForm("ERROR: no angular increment set for iteration $i");
		if (!$_POST['mask'.$i]) jobForm("ERROR: no mask set for iteration $i");
	}
        writeJobFile();
}

else jobForm();

function jobForm($extra=false) {
  $particle = new particledata();

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
  $projectId=getProjectFromExpId($expId);

  // get initial models associated with project
  $modeldata=$particle->getModelsFromProject($projectId);

  // find each stack entry in database
  $stackIds = $particle->getStackIds($sessionId);
  $stackinfo=explode('|--|',$_POST['stackval']);
  $stackidval=$stackinfo[0];
  $apix=$stackinfo[1];
  $box=$stackinfo[2];
  $jobname = ($_POST['jobname']) ? $_POST['jobname'] : '';
  $nodes = ($_POST['nodes']) ? $_POST['nodes'] : 4;
  $ppn = ($_POST['ppn']) ? $_POST['ppn'] : 4;
  $rprocs = ($_POST['rprocs']) ? $_POST['rprocs'] : 4;
  $walltime = ($_POST['walltime']) ? $_POST['walltime'] : 240;
  $cput = ($_POST['cput']) ? $_POST['cput'] : 240;
  $dmfstack = ($_POST['dmfstack']) ? $_POST['dmfstack'] : '';
  $dmfpath = ($_POST['dmfpath']) ? $_POST['dmfpath'] : '';
  $dmfmod = ($_POST['dmfmod']) ? $_POST['dmfmod'] : '';
  $dmfstorech = ($_POST['dmfstore']=='on') ? 'CHECKED' : '';
  $numiters= ($_POST['numiters']) ? $_POST['numiters'] : 1;
  
  if ($_POST['duplicate']) {
    $numiters+=1;
    $newiter=explode(" ",$_POST['duplicate']);
    $j=$newiter[2];
  }
	
  else $j=$numiters;

  $javafunc="<SCRIPT LANGUAGE='JavaScript'>
function displayModelSelector(emanObj){
  newwindow=window.open('','name','resizable=1,scrollbars=1,height=400,width=600');
  newwindow.document.write(\"<HTML><HEAD>\");
  newwindow.document.write(\"<link rel='stylesheet' type='text/css' href='css/viewer.css'>\");
  newwindow.document.write(\"</HEAD>\");
  newwindow.document.write(\"<BODY>\");
  newwindow.document.write(\"<TABLE CLASS='tableborder' BORDER='1' CELLSPACING='1' CELLPADDING='2'>\")\n";
  foreach ($modeldata as $model) {
    # get list of png files in directory
    $pngfiles=array();
    $modeldir= opendir($model['path']);
    while ($f = readdir($modeldir)) {
      if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;
    }
    sort($pngfiles);

    # display starting model
    $javafunc .= "newwindow.document.write(\"<TR><TD COLSPAN=2>\");\n";
    foreach ($pngfiles as $snapshot) {
      $snapfile = $model['path'].'/'.$snapshot;
      $javafunc .= "newwindow.document.write(\"<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\");\n";
    }
    $javafunc .= "newwindow.document.write(\"</TD>\");\n";
    $javafunc .= "newwindow.document.write(\"</TR>\")\n";
    $sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
    $javafunc.="newwindow.document.write(\"<TR><TD COLSPAN=2>$model[description]</TD></TR>\");\n";
    $javafunc.="newwindow.document.write(\"<TR><TD COLSPAN=2>$model[path]/$model[name]</TD></TR>\");\n";
    $javafunc.="newwindow.document.write(\"<TR><TD>pixel size:</TD><TD>$model[pixelsize]</TD></TR>\");\n";
    $javafunc.="newwindow.document.write(\"<TR><TD>box size:</TD><TD>$model[boxsize]</TD></TR>\");\n";
    $javafunc.="newwindow.document.write(\"<TR><TD>symmetry:</TD><TD>$sym[symmetry]</TD></TR>\");\n";
    $javafunc.="newwindow.document.write(\"<TR><TD COLSPAN=2 ALIGN=CENTER>\");\n";
    $javafunc.="newwindow.document.write(\"<INPUT TYPE='button' NAME='modelselect' VALUE='Select Initial Model' onclick='emanObj.document.emanjob.dmfmod.value=3'>\")\n";
    $javafunc.="newwindow.document.write(\"</TD></TR>\");\n";

  }
  $javafunc.="newwindow.document.write(\"</TABLE>\")
  newwindow.document.write(\"</BODY></HTML>\")
  newwindow.document.close();
}
function displayDMF() {
  stack = document.emanjob.stackval.value;
  stackinfo = stack.split('|--|');
  pathinfo = stackinfo[3].split('/');
  dpath='';
  newwindow=window.open('','name','height=250, width=800')
  newwindow.document.write('<HTML><BODY>')
  for (i=3; i<pathinfo.length; i++) {
    dpath=dpath+pathinfo[i]+'/';
    newwindow.document.write('dmf mkdir '+dpath+'<BR>');
  }
  newwindow.document.write('dmf put '+stackinfo[3]+'/'+stackinfo[4]+' '+dpath+stackinfo[4]+'<BR>')
  if (stackinfo[5]) {
    newwindow.document.write('dmf put '+stackinfo[3]+'/'+stackinfo[5]+' '+dpath+stackinfo[5]+'<BR>')
  }
  newwindow.document.write('</BODY></HTML>');
  newwindow.document.close();
  document.emanjob.dmfpath.value=dpath;
  document.emanjob.dmfstack.value=stackinfo[4];
}
</SCRIPT>\n";
  writeTop("Eman Job Generator","EMAN Job Generator",$javafunc);
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo "<FORM NAME='emanjob' METHOD='POST' ACTION='$formaction'>
Job Name: <INPUT TYPE='text' NAME='jobname' VALUE='$jobname' SIZE=50><BR>
Stack:
<SELECT NAME='stackval'>\n";
	foreach ($stackIds as $stackid){
	  // get stack parameters from database
	  $s=$particle->getStackParams($stackid['stackid']);
	  // get number of particles in each stack
	  $nump=commafy($particle->getNumStackParticles($stackid['stackid']));
	  // get pixel size of stack
	  $apix=($particle->getPixelSizeFromStackId($stackid['stackid']))*1e10;
	  $apix=($s['bin']) ? $apix*$s['bin'] : $apix;
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
	  echo">$stackid[stackid] ($nump particles, $apix A/pix, $box x $box)</OPTION>\n";
	}
	echo "</SELECT>
<P>
<INPUT TYPE='button' NAME='modelselect' VALUE='Select Initial Model' onclick='displayModelSelector(this)'>
<INPUT TYPE='button' NAME='dmfput' VALUE='Put stack in DMF' onclick='displayDMF()'>
<P>
<TABLE CLASS='tableborder'>
  <TR>
    <TD>Nodes:</TD>
    <TD><INPUT TYPE='text' NAME='nodes' VALUE='$nodes' SIZE='4'></TD>
    <TD>Procs per Node:</TD>
    <TD><INPUT TYPE='text' NAME='ppn' VALUE='$ppn' SIZE='3'></TD>
  </TR>
  <TR>
    <TD>Wall Time:</TD>
    <TD><INPUT TYPE='text' NAME='walltime' VALUE='$walltime' SIZE='4'></TD>
    <TD>CPU Time:</TD>
    <TD><INPUT TYPE='text' NAME='cput' VALUE='$cput' SIZE='4'></TD>
  </TR>
  <TR>
    <TD COLSPAN='4'>
    Refinement procs per node:<INPUT TYPE='text' NAME='rprocs' VALUE='$rprocs' SIZE='3'>
    </TD>
  </TR>
</TABLE>
<BR>
<TABLE CLASS='tableborder'>
  <TR>
    <TD>DMF Directory:</TD>
    <TD><INPUT TYPE='text' NAME='dmfpath' VALUE='$dmfpath' SIZE='50'></TD>
  </TR>
  <TR>
    <TD>Starting Model (mrc):</TD>
    <TD><INPUT TYPE='text' NAME='dmfmod' VALUE='$dmfmod' SIZE='50'></TD>
  </TR>
  <TR>
    <TD>Stack (img or hed):</TD>
    <TD><INPUT TYPE='text' NAME='dmfstack' VALUE='$dmfstack' SIZE='50'></TD>
  </TR>
  <TR>
    <TD>Save results to DMF</TD>
    <TD><INPUT TYPE='checkbox' NAME='dmfstore' $dmfstorech></TD>
  </TR>
  </TR>
</TABLE>\n";
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
	
		$ang=($i>$j) ? $_POST["ang".($i-1)] : $_POST[$angn];
		$mask=($i>$j) ? $_POST["mask".($i-1)] : $_POST[$maskn];
		$imask=($i>$j) ? $_POST["imask".($i-1)] : $_POST[$imaskn];
		$sym=($i>$j) ? $_POST["sym".($i-1)] : $_POST[$symn];
		$hard=($i>$j) ? $_POST["hard".($i-1)] : $_POST[$hardn];
		$classkeep=($i>$j) ? $_POST["classkeep".($i-1)] : $_POST[$classkeepn];
		$classiter=($i>$j) ? $_POST["classiter".($i-1)] : $_POST[$classitern];
		$filt3d=($i>$j) ? $_POST["filt3d".($i-1)] : $_POST[$filt3dn];
		$shrink=($i>$j) ? $_POST["shrink".($i-1)] : $_POST[$shrinkn];

		if ($i>$j) {
		       $median=($_POST["median".($i-1)]=='on') ? 'CHECKED' : '';
		       $phasecls=($_POST["phasecls".($i-1)]=='on') ? 'CHECKED' : '';
		       $refine=($_POST["refine".($i-1)]=='on') ? 'CHECKED' : '';
		       $goodbad=($_POST["goodbad".($i-1)]=='on') ? 'CHECKED' : '';
		       $eotest=($_POST["eotest".($i-1)]=='on') ? 'CHECKED' : '';
		       $coran=($_POST["coran".($i-1)]=='on') ? 'CHECKED' : '';
		}
		else {
		       $median=($_POST[$mediann]=='on') ? 'CHECKED' : '';
		       $phasecls=($_POST[$phaseclsn]=='on') ? 'CHECKED' : '';
		       $refine=($_POST[$refinen]=='on') ? 'CHECKED' : '';
		       $goodbad=($_POST[$goodbadn]=='on') ? 'CHECKED' : '';
		       $eotest=($_POST[$eotestn]=='on') ? 'CHECKED' : '';
		       $coran=($_POST[$corann]=='on') ? 'CHECKED' : '';
		}
		$bgcolor="#E8E8E8";
		echo"
<P><B>Iteration $i</B><BR>
<TABLE CLASS='tableborder' BORDER='1'>
  <TR>
    <TD BGCOLOR='$bgcolor'>ang:<INPUT TYPE='text' NAME='$angn' SIZE='2' VALUE='$ang'></TD>
    <TD BGCOLOR='$bgcolor'>mask:<INPUT TYPE='text' NAME='$maskn' SIZE='4' VALUE='$mask'></TD>
    <TD BGCOLOR='$bgcolor'>imask:<INPUT TYPE='text' NAME='$imaskn' SIZE='4' VALUE='$imask'></TD>
    <TD BGCOLOR='$bgcolor'>sym:<INPUT TYPE='text' NAME='$symn' SIZE='5' VALUE='$sym'></TD>
    <TD BGCOLOR='$bgcolor'>hard:<INPUT TYPE='text' NAME='$hardn' SIZE='3' VALUE='$hard'></TD>
    <TD BGCOLOR='$bgcolor'>classkeep:<INPUT TYPE='text' NAME='$classkeepn' SIZE='4' VALUE='$classkeep'></TD>
    <TD BGCOLOR='$bgcolor'>classiter:<INPUT TYPE='text' NAME='$classitern' SIZE='2' VALUE='$classiter'></TD>
    <TD BGCOLOR='$bgcolor'>filt3d:<INPUT TYPE='text' NAME='$filt3dn' SIZE='4' VALUE='$filt3d'></TD>
  </TR>
  <TR>
    <TD BGCOLOR='$bgcolor'>shrink:<INPUT TYPE='text' NAME='$shrinkn' SIZE='2' VALUE='$shrink'></TD>
    <TD BGCOLOR='$bgcolor'><INPUT TYPE='checkbox' NAME='$mediann' $median>median</TD>
    <TD BGCOLOR='$bgcolor'><INPUT TYPE='checkbox' NAME='$phaseclsn' $phasecls>phasecls</TD>
    <TD BGCOLOR='$bgcolor'><INPUT TYPE='checkbox' NAME='$refinen' $refine>refine</TD>
    <TD BGCOLOR='$bgcolor'><INPUT TYPE='checkbox' NAME='$goodbadn' $goodbad>goodbad</TD>
    <TD BGCOLOR='$bgcolor'><INPUT TYPE='checkbox' NAME='$eotestn' $eotest>eotest</TD>
    <TD BGCOLOR='$bgcolor'><INPUT TYPE='checkbox' NAME='$corann' $coran>coran</TD>
    <TD BGCOLOR='$bgcolor' ALIGN='CENTER'><INPUT TYPE='SUBMIT' NAME='duplicate' VALUE='Duplicate Row $i'></TD>
  </TR>
</TABLE>\n";
	}
	echo"<INPUT TYPE='hidden' NAME='numiters' VALUE='$numiters'>
<P><INPUT TYPE='SUBMIT' NAME='write' VALUE='Create Job File'>
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
  echo "<PRE>\n";
  $dmfpath=$_POST['dmfpath'];
  // make sure dmf store dir ends with '/'
  if (substr($dmfpath,-1,1)!='/') $dmfpath.='/';
  if ($_POST['jobname']) echo "# ".$_POST['jobname']."\n";
  echo "# stackId: $stackidval\n";
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
  echo "        echo 'rsh 1 ".$_POST['rprocs']."' \$i \$PBSREMOTEDIR >> .mparm\n";
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
    $line.="rm cls*.lst\n";
    echo $line;
  }
  if ($_POST['dmfstore']=='on') {
    echo "\ntar -cvzf model.tar.gz threed.*a.mrc\n";
    echo "dmf put model.tar.gz $dmfpath\n";
    echo "\ntar -cvzf results.tar.gz fsc* tcls* refine.* particle.* classes.* proj.* sym.* .emanlog *txt\n";
    echo "dmf put results.tar.gz $dmfpath\n";
  } 
  echo "\nexit\n\n";
  echo "</PRE>\n";
  exit;
}
