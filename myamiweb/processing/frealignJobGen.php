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
require "inc/summarytables.inc";

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
	if (!$_POST['mask']) jobForm("ERROR: Enter an outer mask radius");
	if ($_POST['initorientmethod']=='projmatch' && !$_POST['dang']) jobForm("ERROR: Enter an angular increment");
	prepareFrealign();
}

elseif ($_POST['submitstackmodel'] || $_POST['importrecon']) {
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
	#if ($stackbox != $modbox) stackModelForm("ERROR: model and stack must have same box size");
	jobForm();
}


else stackModelForm();

function stackModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectFromExpId($expId);

	$javafunc="<script src='../js/viewer.js'></script>\n";
	processing_header("FREALIGN Job Generator","FREALIGN Job Generator",$javafunc);

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
	$stackid = $stackinfo[0];
	$apix = $stackinfo[1];
	$box = $stackinfo[2];

	// write out errors, if any came up:
	if ($extra) echo "<font color='red' size='+2'>$extra</font>\n<hr>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	echo"<b>Stack:</b><br>";
	$particle->getStackSelector($stackIds, $stackid, '');

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
	$stackid=$stackinfo[0];
	$nump=$particle->getNumStackParticles($stackid);
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
	$stackpath=$stackinfo[4];
	$stackname1=$stackinfo[5];
  
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
	$modelid = $modelinfo[0];
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];
	$dmfmod = $modelinfo[2];

	$syminfo = explode(' ',$modelinfo[4]);
	$modsym = $syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : 1;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : 8;

	// preset information from stackid
	$presetinfo = $particle->getPresetFromStackId($stackid);
	$kv = $presetinfo['hightension']/1e3;
	$cs = 2.0;

	$javafunc .= writeJavaPopupFunctions('frealign');
	processing_header("Frealign Job Generator","Frealign Job Generator",$javafunc);
	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='#CC3333' size='+2'>$extra</FONT>\n<HR>\n";

	echo "<form name='frealignjob' method='post' action='$formaction'><br/>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";

	$sym = ($_POST['sym']) ? $_POST['sym'] : $modsym;

	// if importing reconstruction eulers
	if ($_POST['importrecon'] && $_POST['importrecon']!='None'){
		$_POST['initorientmethod']='importrecon';
		$_POST['write']='True';
		$importcheck='checked';
	}
	$angcheck = ($_POST['initorientmethod']=='projmatch' || !$_POST['write']) ? 'checked' : '';
	$inparfilecheck = ($_POST['initorientmethod']=='inparfile') ? 'checked' : '';

	/* ******************************************
	SCRIPT PARAMETERS
	****************************************** */
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunid;
	$outdir  = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '10';

	echo "<table class='tableborder' border='1' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td colspan='2' align='center'>\n";
		echo "<h4>Script parameters</h4>\n";
	echo "</td></tr><tr><td>\n";

		echo docpop('runname','Run Name')." <br/>\n";
		echo " <input type='type' name='runname' value='$runname' size='20'>\n";
		echo "<br/>\n";
		echo docpop('outdir','Output directory')." <br/>\n";
		echo " <input type='type' name='outdir' value='$outdir' size='50'>\n";
		echo "<br/><br/>\n";

		echo " <input type='type' name='nodes' value='$nodes' size='4'>\n";
		echo docpop('nodes','Number of nodes')." <font size='-2'><i></i></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='ppn' value='$ppn' size='4'>\n";
		echo docpop('ppn','Number of processors per node')." <font size='-2'><i></i></font>\n";
		echo "<br/><br/>\n";

		echo " <input type='type' name='numiter' value='$numiter' size='4'>\n";
		echo docpop('numiter','Number of refinement iterations')." <font size='-2'><i></i></font>\n";
		echo "<br/>\n";

	echo "</td></tr>\n";
	echo "</table>\n";

	/* ******************************************
	INITIAL ORIENTATIONS BOX
	****************************************** */

	### Frealign initial search only
	$dang   = $_POST['dang'] ? $_POST['dang'] : '5';
	$initlp = $_POST['initlp'] ? $_POST['initlp'] : '25';

	echo "<br/>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td>\n";
	echo "<h4>Initial Orientations</h4>\n";

	echo "</td></tr><tr><td>\n";

	echo "<input type='radio' name='initorientmethod' value='importrecon' $importcheck>\n";
	// Neil:: Switching code ; why do want recons from other sessions, we don't have a mathcing stack
	//$recons = $particle->getReconIdsFromSession($expId);
	$recons = $particle->getReconIterIdRelatedToStackid($stackid);
	if (is_array($recons)) {
		echo "<b>Import from EMAN reconstruction:</b>";
		echo "<br/>&nbsp;&nbsp;&nbsp; Reconstr.:\n";
		echo "<select name='importrecon' onchange='this.form.submit()'>\n";
		echo "   <option value='None'>Select Reconstruction</option>\n";
	  	foreach ($recons as $r) {
			$ropt = "<option value='".$r['DEF_id']."' ";
			$ropt.= ($_POST['importrecon']==$r['DEF_id']) ? 'selected':'';
			$ropt.= ">";
			$ropt.= $r['name']." (id: ".$r['DEF_id'].") -- ".substr($r['description'],0,60);
			$ropt.= "</option>\n";
			echo $ropt;
		}
	} else {
		echo "<i>no EMAN recons to import Euler angles</i>\n";
	}
	echo "</select>\n";
	echo "<br/>\n";

	// if a reconstruction has been selected, show iterations & resolutions
	if ($_POST['importrecon'] && $_POST['importrecon']!='None') {
		echo "&nbsp;&nbsp;&nbsp; Iteration:\n";
		$iterinfo = $particle->getRefinementData($_POST['importrecon']);
		echo "<select name='importiter'>\n";
		if (is_array($iterinfo)) {
			foreach ($iterinfo as $iter){
			  	$iterstuff = $particle->getIterationInfo($_POST['importrecon'],$iter['iteration']);
				$rmeas = $particle->getRMeasureInfo($iter['REF|ApRMeasureData|rMeasure']);
				$fsc = $particle->getResolutionInfo($iter['REF|ApResolutionData|resolution']);
				$iopt.="<option value='".$iter['DEF_id']."' ";
				$iopt.= ($_POST['importiter']==$iter['DEF_id']) ? 'selected':'';
				$iopt.= ">Iter ".$iter['iteration'];
				$iopt.= ": Ang=".$iterstuff['ang'];
				$iopt.= ", FSC=".sprintf('%.1f',$fsc['half']);
				$iopt.= ", Rmeas=".sprintf('%.1f',$rmeas['rMeasure']);
				$iopt.= "</option>\n";
			}
		}
		echo $iopt;
		echo "</select>\n";
		echo "<br/>\n";
	}
	echo "</td></tr><tr><td>\n";

	echo "<input type='radio' name='initorientmethod' value='projmatch' $angcheck>\n";
	echo "<b>Determine with Frealign</b>";
	echo "<br/>\n";
	echo docpop('dang',"&nbsp;&nbsp;&nbsp; Angular increment: ");
	echo " <input type='type' name='dang' value='$dang' size='4'>\n";
	echo "&nbsp;&nbsp;&nbsp; Initial LP filter: ";
	echo " <input type='type' name='initlp' value='$initlp' size='4'>\n";

	//echo "</td></tr><tr><td>\n";

	//echo "<input type='radio' name='initorientmethod' value='inparfile' $inparfilecheck>\n";
	//echo docpop('inpar',"Use input Frealign parameter file:");
	//echo " <input type='type' name='inparfile' value='$inparfile' size='50'>\n";

	echo "</td></tr>\n";
	echo "</table>\n";
	echo closeRoundBorder();

	echo "<br/>\n";
	echo "<br/>\n";


	/* ******************************************
	FREALIGN PARAMETERS
	****************************************** */

	//$magrefine=($_POST[$magrefinen]=='on') ? 'CHECKED' : '';
	//$defocusrefine=($_POST[$defocusrefinen]=='on') ? 'CHECKED' : '';
	//$astigrefine=($_POST[$astigrefinen]=='on') ? 'CHECKED' : '';

	###set default values that iterate
	$mask  = $_POST["mask"] ? $_POST["mask"] : round($apix*$box/3.0);
	$imask = $_POST["imask"] ? $_POST["imask"] : 0;
	$wgh   = $_POST["wgh"] ? $_POST["wgh"] : 0.07;
	$xstd  = $_POST["xstd"] ? $_POST["xstd"] : 0;
	$pbc   = $_POST["pbc"] ? $_POST["pbc"] : 100;
	$boff  = $_POST["boff"] ? $_POST["boff"] : 70;
	$itmax = $_POST["itmax"] ? $_POST["itmax"] : 10;
	$ipmax = $_POST["ipmax"] ? $_POST["ipmax"] : 0;

	$target = $_POST["target"] ? $_POST["target"] : 15;
	$thresh = $_POST["thresh"] ? $_POST["thresh"] : 90;

	$rrec = $_POST["rrec"] ? $_POST["rrec"] : (ceil($apix*20))/10;
	$hp = $_POST["hp"] ? $_POST["hp"] : 50;
	$lp = $_POST["lp"] ? $_POST["lp"] : (ceil($apix*40))/10;
	$rbfact = $_POST["rbfact"] ? $_POST["rbfact"] : 0;

	echo "<table class='tableborder' border='1' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td colspan='2' align='center'>\n";
		echo "<h4>Frealign parameters</h4>\n";
	echo "</td></tr>";

	echo "<tr><td>\n";
		echo "<h4>Card #2</h4>\n";
	echo "</td><td>\n";
		echo "<h4>Card #5</h4>\n";
	echo "</td></tr>";

	echo "<tr><td rowspan='5'>\n";
		echo " <input type='type' name='mask' value='$mask' size='4'>\n";
		echo docpop('mask','Particle outer mask radius (RO)')." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='imask' value='$imask' size='4'>\n";
		echo docpop('imask','Particle inner mask radius (RI)')." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";

		echo "<br/><br/>\n";

		echo " <input type='type' name='wgh' value='$wgh' size='4'>\n";
		echo docpop('wgh','Amplitude contrast (WGH)')." \n";
		echo "<br/>\n";
		echo " <input type='type' name='xstd' value='$xstd' size='4'>\n";
		echo docpop('xstd','Standard deviation filtering (XSTD)')." <font size='-2'><i>(0 = no filtering)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='pbc' value='$pbc' size='4'>\n";
		echo docpop('pbc','Phase B-factor weighting constant (PBC)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='boff' value='$boff' size='4'>\n";
		echo docpop('boff','B-factor offset (BOFF)')." <font size='-2'></font>\n";

		echo "<br/><br/>\n";

		echo " <input type='type' name='itmax' value='$itmax' size='4'>\n";
		echo docpop('itmax','Number of randomized search trials (ITMAX)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='ipmax' value='$ipmax' size='4'>\n";
		echo docpop('ipmax','Number of potential matches to refine (IPMAX)')." <font size='-2'></font>\n";

	echo "</td><td>\n";

		echo " <input type='type' name='sym' value='$sym' size='4'>\n";
		echo docpop('sym','Symmetry (ASYM)')." <font size='-2'></font>\n";

	echo "</td></tr><tr><td>\n";
		echo "<h4>Card #6</h4>\n";
	echo "</td></tr><tr><td>\n";

		echo " <input type='type' name='target' value='$target' size='4'>\n";
		echo docpop('target','Target phase residual (TARGET)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='thresh' value='$thresh' size='4'>\n";
		echo docpop('thresh','Worst phase residual for inclusion (THRESH)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='cs' value='$cs' size='4'>\n";
		echo docpop('cs','Spherical abberation (CS)')." <font size='-2'></font>\n";

	echo "</td></tr><tr><td>\n";
		echo "<h4>Card #7</h4>\n";
	echo "</td></tr><tr><td>\n";

		echo " <input type='type' name='rrec' value='$rrec' size='4'>\n";
		echo docpop('rrec','Resolution limit of reconstruction (RREC)')." <font size='-2'><i>(in &Aring;ngstroms; default Nyquist)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='hp' value='$hp' size='4'>\n";
		echo docpop('hp','Lower resolution limit or high-pass filter (RMAX1)')." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='lp' value='$lp' size='4'>\n";
		echo docpop('lp','Higher resolution limit or low-pass filter (RMAX2)')." <font size='-2'><i>(in &Aring;ngstroms; default 2*Nyquist)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='type' name='rbfact' value='$rbfact' size='4'>\n";
		echo docpop('rbfact','B-factor correction (RBFACT)')." <font size='-2'><i>(0 = off)</i></font>\n";
	echo "</td></tr>\n";
	echo "</table>\n";

	echo "
		  <input type='hidden' NAME='cs' value='$cs'>
		  <input type='hidden' NAME='kv' value='$kv'>
		  <input type='hidden' NAME='last' value='$nump'>
		  <input type='hidden' NAME='apix' value='$apix'>
		  <input type='hidden' name='projectId' value='$projectId'><P>
		  <input type='submit' name='write' value='Prepare Data for Frealign'>
	  </form>\n";
	echo "<br/><br/><hr/>\n";
	//echo "StackID: $stackid -- ModelID: $modelid<br/>\n";
	echo "<table class='tablebubble'><tr><td>\n";
	echo stacksummarytable($stackid, true);
	echo "</td></tr><tr><td>\n";
	echo modelsummarytable($modelid, true);
	echo "</td></tr></table>\n";

	processing_footer();
	exit;
}

function prepareFrealign ($extra=False) {
	$expId = $_GET['expId'];
	$projectId = getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$jobname = $_POST['runname'];

	$nodes = $_POST['nodes'];
	$ppn = $_POST['ppn'];
	$procs = $nodes*$ppn;
	$clustername = $_POST['clustername'];
	$outdir = $_POST['outdir'];
	if (substr($outdir,-1,1)!='/') $outdir.='/';

	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackid=$stackinfo[0];
	$stackpath=$stackinfo[4];
	$stackname1=$stackinfo[5];
 
	// get the model id
	$modelinfo=explode('|--|',$_POST['model']);
	$modelid=$modelinfo[0];
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];

	processing_header("Frealign Job Generator","Frealign Job Generator", $javafunc);

	$last=$_POST['last'];
	$cs=$_POST['cs'];
	$kv=$_POST['kv'];
	$mask=$_POST["mask"];
	$imask=$_POST["imask"];
	$wgh=$_POST["wgh"];
	$xstd=$_POST["xstd"];
	$pbc=$_POST["pbc"];
	$boff=$_POST["boff"];
	$dang = ($_POST['initorientmethod']=='projmatch') ? $_POST["ang"] : '';
	$itmax=$_POST["itmax"];
	$ipmax=$_POST["ipmax"];
	$sym=$_POST["sym"];
	$target=$_POST["target"];
	$thresh=$_POST["thresh"];
	$rrec=$_POST['rrec'];
	$hp=$_POST["hp"];
	$lp=$_POST["lp"];
	$rbfact=$_POST["rbfact"];
	$numiter=$_POST['numiter'];
	$inpar=$_POST['inparfile'];
	$importiter=$_POST['importiter'];
	
	$line.= "#PBS -l nodes=$nodes:ppn=$ppn\n";
	$line.= "#PBS -l walltime=240:00:00\n";
	$line.= "#PBS -l cput=240:00:00\n";
	$line.= "\nrunfrealign.py -n $jobname \\\n  ";
	$line.= "--mask=$mask ";
	$line.= "--imask=$imask ";
	$line.= "--wgh=$wgh \\\n  ";
	$line.= "--xstd=$xstd ";
	$line.= "--pbc=$pbc ";
	$line.= "--boff=$boff ";
	$line.= "--itmax=$itmax ";
	$line.= "--ipmax=$ipmax \\\n  ";
	//$line.= "--last=$last ";
	$line.= "--sym=$sym ";
	$line.= "--target=$target ";
	$line.= "--thresh=$thresh \\\n  ";
	$line.= "--cs=$cs --kv=$kv \\\n  ";
	$line.= "--rrec=$rrec --hp=$hp --lp=$lp --rbfact=$rbfact \\\n  ";
	//if ($inpar) $line.= "--inpar=$inpar ";
	if ($dang) $line.= "--dang=$dang ";
	if ($numiter) $line.= "--numiter=$numiter ";

	//appion specific options
	if ($importiter) $line.= "--reconiterid=$importiter ";
	$line.= "--stackid=$stackid \\\n  ";
	$line.= "--modelid=$modelid ";
	$line.= "--project=$projectId ";
	$line.= "--proc=$procs ";
	
	//$line.=" > runfrealign".$i.".txt\n";
	$clusterjob.= $line;
 
	echo "<FORM NAME='frealignjob' METHOD='POST' ACTION='$formAction'><br>\n";
	echo "<input type='hidden' name='clustername' value='$clustername'>\n";
	echo "<input type='HIDDEN' NAME='clusterpath' VALUE='$clusterpath'>\n";
	echo "<input type='HIDDEN' NAME='dmfpath' VALUE='$dmfpath'>\n";
	echo "<input type='HIDDEN' NAME='jobname' VALUE='$jobname'>\n";
	echo "<input type='HIDDEN' NAME='outdir' VALUE='$outdir'>\n";

	// convert \n to /\n's for script
	if (!$extra) {
		echo "<HR>\n";
		echo "<PRE>\n";
		echo $clusterjob;
		echo "</PRE>\n";
		//$tmpfile = "/tmp/$jobfile";
		// write file to tmp directory
		//$f = fopen($tmpfile,'w');
		//fwrite($f,$clusterjob);
		//fclose($f);
	}	


	processing_footer();
	exit;
};

