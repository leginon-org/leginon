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
	if (!$_POST['box']) jobForm("ERROR: No box size");
	for ($i=1; $i<=$_POST['numiters']; $i++) {
	        if (!$_POST['ang'.$i]) jobForm("ERROR: no angular increment set for iteration $i");
	}
        writeJobFile();
}

else jobForm();

function jobForm($extra=false) {
        $formAction=$_SERVER['PHP_SELF'];
	$jobname = ($_POST['jobname']) ? $_POST['jobname'] : '';
	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : 4;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : 4;
	$rprocs = ($_POST['rprocs']) ? $_POST['rprocs'] : 4;
	$box = ($_POST['box']) ? $_POST['box'] : '';
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
	
	writeTop("Eman Job Generator","EMAN Job Generator");
        // write out errors, if any came up:
        if ($extra) {
                echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
        }
	echo "<FORM NAME='emanjob' METHOD='POST' ACTION='$formaction'>
Job Name: <INPUT TYPE='text' NAME='jobname' VALUE='$jobname' SIZE=50>
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
  <TR>
    <TD>Box Size (pixels):</TD>
    <TD><INPUT TYPE='text' NAME='box' VALUE='$box' SIZE='5'></TD>
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
		}
		else {
		       $median=($_POST[$mediann]=='on') ? 'CHECKED' : '';
		       $phasecls=($_POST[$phaseclsn]=='on') ? 'CHECKED' : '';
		       $refine=($_POST[$refinen]=='on') ? 'CHECKED' : '';
		       $goodbad=($_POST[$goodbadn]=='on') ? 'CHECKED' : '';
		       $eotest=($_POST[$eotestn]=='on') ? 'CHECKED' : '';
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
    <TD BGCOLOR='$bgcolor' ALIGN='CENTER' COLSPAN='2'><INPUT TYPE='SUBMIT' NAME='duplicate' VALUE='Duplicate Row $i'></TD>
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
        echo "<PRE>\n";
        $dmfpath=$_POST['dmfpath'];
	// make sure dmf store dir ends with '/'
	if (substr($dmfpath,-1,1)!='/') $dmfpath.='/';
        if ($_POST['jobname']) echo "# ".$_POST['jobname']."\n";
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
		$pad=intval($_POST['box']*1.25);
		// make sure $pad value is even int
		$pad = ($pad%2==1) ? $pad+=1 : $pad;
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
			if ($phasecls=='on') $line.=" phasecls";
			if ($refine=='on') $line.=" refine";
			$line.=" > eotest".$i.".txt\n";
			$line.="mv fsc.eotest fsc.eotest".$i."\n";
			$line.="getRes.pl >> resolution.txt\n";
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
	echo "</PRE>\n";
	exit;
}