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
	if (!$_POST['dmfpath'] > $_
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
    <TD>DMF Starting Model (mrc):</TD>
    <TD><INPUT TYPE='text' NAME='dmfmod' VALUE='$dmfmod' SIZE='50'></TD>
  </TR>
  <TR>
    <TD>DMF Stack (img or hed):</TD>
    <TD><INPUT TYPE='text' NAME='dmfstack' VALUE='$dmfstack' SIZE='50'></TD>
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
		$mediann="median".$i;
		$phaseclsn="phasecls".$i;
		$refinen="refine".$i;
		$goodbadn="goodbad".$i;
		$eotestn="eotest".$i;
	
		$ang=($i==$numiters) ? $_POST["ang".$j] : $_POST[$angn];
		$mask=($i==$numiters) ? $_POST["mask".$j] : $_POST[$maskn];
		$imask=($i==$numiters) ? $_POST["imask".$j] : $_POST[$imaskn];
		$sym=($i==$numiters) ? $_POST["sym".$j] : $_POST[$symn];
		$hard=($i==$numiters) ? $_POST["hard".$j] : $_POST[$hardn];
		$classkeep=($i==$numiters) ? $_POST["classkeep".$j] : $_POST[$classkeepn];
		$classiter=($i==$numiters) ? $_POST["classiter".$j] : $_POST[$classitern];
		$filt3d=($i==$numiters) ? $_POST["filt3d".$j] : $_POST[$filt3dn];
		if ($i==$numiters) {
		       $median=($_POST["median".$j]=='on') ? 'CHECKED' : '';
		       $phasecls=($_POST["phasecls".$j]=='on') ? 'CHECKED' : '';
		       $refine=($_POST["refine".$j]=='on') ? 'CHECKED' : '';
		       $goodbad=($_POST["goodbad".$j]=='on') ? 'CHECKED' : '';
		       $eotest=($_POST["eotest".$j]=='on') ? 'CHECKED' : '';
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
        $dmfpath=$_POST['dmfpath'];
        if ($_POST['jobname']) echo "# ".$_POST['jobname']."<P>\n";
        echo "#PBS -l nodes=".$_POST['nodes'].":ppn=".$_POST['ppn']."<BR>\n";
	echo "#PBS -l walltime=".$_POST['walltime'].":00:00<BR>\n";
	echo "#PBS -l cput=".$_POST['cput'].":00:00<BR>\n";
	echo "#PBS -m e<BR>\n";
	echo "#PBS -r n<BR>\n";
	echo "<P>cd \$PBSREMOTEDIR\n";
	// get file name, strip extension
	$ext=strrchr($_POST['dmfstack'],'.');
	$stackname=substr($_POST['dmfstack'],0,-strlen($ext));
	echo "<P>dmf get ".$_POST['dmfmod']." threed.0a.mrc<BR>\n";
	echo "dmf get $stackname.hed start.hed<BR>\n";
	echo "dmf get $stackname.img start.img<BR>\n";
	echo "<P>foreach i (`sort -u \$PBS_NODEFILE`)<BR>\n";
	echo "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;echo 'rsh 1 ".$_POST['rprocs']."' \$i \$PBSREMOTEDIR >> .mparm<BR>\n";
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
		$line="<P>refine $i proc=$procs ang=$ang pad=$pad";
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
		$line.=" > refine".$i.".txt<BR>";
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
			$line.=" > eotest".$i.".txt<BR>";
			$line.="mv fsc.eotest fsc.eotest".$i."<BR>";
		}
		$line.="rm cls*.lst<BR>";
		echo $line;
	}
	if ($_POST['dmfstore']=='on') {
	        // make sure dmf store dir ends with '/'
	        if (substr($dmfpath,-1,1)!='/') $dmfpath.='/';
		echo "<P>tar -cvzf model.tar.gz threed.*a.mrc<BR>\n";
		echo "dmf put model.tar.gz $dmfstore<BR>\n";
		echo "<P>tar -cvzf results.tar.gz fsc* tcls* refine.* particle.* classes.* proj.* sym.* .emanlog *txt<BR>\n";
		echo "dmf put results.tar.gz $dmfstore\n";
	} 
	exit;
}