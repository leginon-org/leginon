<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Prepare a Frealign Job for submission to a cluster
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

if ($_POST['process'])
	prepareFrealign(); // generate command
elseif ($_POST['stackval'] && $_POST['model'])
	jobForm(); // set parameters
else
	stackModelForm(); // select stack and model

/* ******************************************
*********************************************
SELECT STACK AND INITIAL MODEL
*********************************************
****************************************** */

function stackModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectFromExpId($expId);

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
	$stackIds = $particle->getStackIds($expId, false, false, false);
	$stackinfo = explode('|--|', $_POST['stackval']);
	$stackid = $stackinfo[0];
	$apix = $stackinfo[1];
	$box = $stackinfo[2];
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	echo"<b>Not ctf-corrected Stacks:</b><br>";
	$particle->getStackSelector($stackIds, $stackid, '');

	// show initial models
	echo "<P><B>Initial models:</B><br>"
		."<A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><br>\n";
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

/* ******************************************
*********************************************
MAIN FORM TO SET PARAMETERS
*********************************************
****************************************** */

function jobForm($extra=false) {
	$expId = $_GET['expId'];
	$projectId = $_POST['projectId'];

	if (!$_POST['model'])
		stackModelForm("ERROR: no initial model selected");
	if (!$_POST['stackval'])
		stackModelForm("ERROR: no stack selected");

	## get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = $sessiondata['Image path'];
	$sessionpath = ereg_replace("leginon","appion",$sessionpath);
	$sessionpath = ereg_replace("rawdata","recon/",$sessionpath);

	$particle = new particledata();
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$reconruns = count($particle->getReconIdsFromSession($expId));
	while (glob($outdir.'*recon'.($reconruns+1))) {
		$reconruns += 1;
	}
	$defrunid = 'frealign_recon'.($reconruns+1);

	## find if there are ctffind runs
	$ctffindruns = $particle->getCtfRunIds($expId, $showHidden=False, $ctffind=True);

	## get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$stackid=$stackinfo[0];
	$nump=$particle->getNumStackParticles($stackid);
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
	$stackpath=$stackinfo[4];
	$stackname1=$stackinfo[5];
  
	$stack=$stackname1 ;
	
	## get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$modelid = $modelinfo[0];
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];

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
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='frealignjob' method='post' action='$formaction'><br/>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";

	$sym = ($_POST['sym']) ? $_POST['sym'] : $modsym;

	// if importing reconstruction eulers
	if ($_POST['importrecon'] && $_POST['importrecon']!='None'){
		$_POST['initmethod']='importrecon';
		$_POST['write']='True';
		$importcheck='checked';
	}
	$angcheck = ($_POST['initmethod']=='projmatch' || !$_POST['write']) ? 'checked' : '';
	$inparfilecheck = ($_POST['initmethod']=='inparfile') ? 'checked' : '';

	/* ******************************************
	SCRIPT PARAMETERS
	****************************************** */
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunid;
	$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '10';

	echo "<table class='tableborder' border='1' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td colspan='2' align='center'>\n";
		echo "<h4>Script parameters</h4>\n";
	echo "</td></tr><tr><td>\n";

	echo "</td></tr><tr><td>\n";

		echo docpop('runname','Run Name')." <br/>\n";
		echo " <input type='text' name='runname' value='$runname' size='20'>\n";
		echo "<br/>\n";
		echo docpop('outdir','Output directory')." <br/>\n";
		echo " <input type='text' name='outdir' value='$outdir' size='50'>\n";
		echo "<br/><br/>\n";

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

	echo "<input type='radio' name='initmethod' value='importrecon' $importcheck>\n";
	// Neil:: Switching code ; why do want recons from other sessions, we don't have a mathcing stack
	//$recons = $particle->getReconIdsFromSession($expId);
	$recons = $particle->getReconIterIdRelatedToStackid($stackid);
	if (is_array($recons)) {
		echo "<b>Import from EMAN reconstruction:</b>";
		echo "<br/>&nbsp;&nbsp;&nbsp; Reconstr.:\n";
		echo "<select name='importrecon' onchange='frealignjob.submit()'>\n";
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

	echo "<input type='radio' name='initmethod' value='projmatch' $angcheck>\n";
	echo "<b>Determine with Frealign</b>";
	echo "<br/>\n";
	echo docpop('dang',"&nbsp;&nbsp;&nbsp; Angular increment: ");
	echo " <input type='text' name='dang' value='$dang' size='4'>\n";
	echo "&nbsp;&nbsp;&nbsp; Initial LP filter: ";
	echo " <input type='text' name='initlp' value='$initlp' size='4'>\n";

	//echo "</td></tr><tr><td>\n";

	//echo "<input type='radio' name='initmethod' value='inparfile' $inparfilecheck>\n";
	//echo docpop('inpar',"Use input Frealign parameter file:");
	//echo " <input type='text' name='inparfile' value='$inparfile' size='50'>\n";

	echo "</td></tr><tr><td>\n";

	echo " <input type='text' name='numiter' value='$numiter' size='4'>\n";
	echo docpop('numiter','Number of refinement iterations')." <font size='-2'><i></i></font>\n";
	echo "<br/>\n";

	echo "</td></tr>\n";
	echo "</table>\n";
	echo closeRoundBorder();

	echo "<br/>\n";
	echo "<br/>\n";

	/* ******************************************
	CLUSTER PARAMETERS
	****************************************** */
	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : 32;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : 8;

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
	$ctffindcheck = ($_POST['ctffindonly']=='on') ? 'checked':'';

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
		echo " <input type='text' name='mask' value='$mask' size='4'>\n";
		echo docpop('mask','Particle outer mask radius (RO)')
			." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='imask' value='$imask' size='4'>\n";
		echo docpop('imask','Particle inner mask radius (RI)')
			." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";

		echo "<br/><br/>\n";

		echo " <input type='text' name='wgh' value='$wgh' size='4'>\n";
		echo docpop('wgh','Amplitude contrast (WGH)')." \n";
		echo "<br/>\n";
		echo " <input type='text' name='xstd' value='$xstd' size='4'>\n";
		echo docpop('xstd','Standard deviation filtering (XSTD)')
			." <font size='-2'><i>(0 = no filtering)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='pbc' value='$pbc' size='4'>\n";
		echo docpop('pbc','Phase B-factor weighting constant (PBC)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='boff' value='$boff' size='4'>\n";
		echo docpop('boff','B-factor offset (BOFF)')." <font size='-2'></font>\n";

		echo "<br/><br/>\n";

		echo " <input type='text' name='itmax' value='$itmax' size='4'>\n";
		echo docpop('itmax','Number of randomized search trials (ITMAX)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='ipmax' value='$ipmax' size='4'>\n";
		echo docpop('ipmax','Number of potential matches to refine (IPMAX)')." <font size='-2'></font>\n";

	echo "</td><td>\n";

		echo " <input type='text' name='sym' value='$sym' size='4'>\n";
		echo docpop('sym','Symmetry (ASYM)')." <font size='-2'></font>\n";

	echo "</td></tr><tr><td>\n";
		echo "<h4>Card #6</h4>\n";
	echo "</td></tr><tr><td>\n";

		echo " <input type='text' name='target' value='$target' size='4'>\n";
		echo docpop('target','Target phase residual (TARGET)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='thresh' value='$thresh' size='4'>\n";
		echo docpop('thresh','Worst phase residual for inclusion (THRESH)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='cs' value='$cs' size='4'>\n";
		echo docpop('cs','Spherical abberation (CS)')." <font size='-2'></font>\n";

	echo "</td></tr><tr><td>\n";
		echo "<h4>Card #7</h4>\n";
	echo "</td></tr><tr><td>\n";

		echo " <input type='text' name='rrec' value='$rrec' size='4'>\n";
		echo docpop('rrec','Resolution limit of reconstruction (RREC)')
			." <font size='-2'><i>(in &Aring;ngstroms; default Nyquist)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='hp' value='$hp' size='4'>\n";
		echo docpop('hp','Lower resolution limit or high-pass filter (RMAX1)')
			." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='lp' value='$lp' size='4'>\n";
		echo docpop('lp','Higher resolution limit or low-pass filter (RMAX2)')
			." <font size='-2'><i>(in &Aring;ngstroms; default 2*Nyquist)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='rbfact' value='$rbfact' size='4'>\n";
		echo docpop('rbfact','B-factor correction (RBFACT)')." <font size='-2'><i>(0 = off)</i></font>\n";

		echo "</td></tr><tr><td colspan='3' align='center'>\n";

		// give option of only using ctffind runs
		if ($ctffindruns) {
			echo "<input type='checkbox' name='ctffindonly' $ctffindcheck>";
			echo docpop('ctffindonly','Only use CTFFIND values');
			echo "&nbsp;&nbsp;&nbsp;&nbsp;\n";
		}
		echo " <input type='text' name='last' value='$last' size='4'>\n";
		echo docpop('last','Last particle to use')." \n";

	// SUBMIT BUTTON
	echo "</td></tr><tr><td colspan='3' align='center'>\n";
		echo "<br/>\n";
		echo getSubmitForm("Prepare Frealign");
	echo "</td></tr>\n";
	echo "</table>\n";

	echo "<input type='hidden' NAME='cs' value='$cs'>";
	echo "<input type='hidden' NAME='kv' value='$kv'>";
	echo "<input type='hidden' NAME='apix' value='$apix'>";

	echo "</form>\n";
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

/* ******************************************
*********************************************
GENERATE COMMAND
*********************************************
****************************************** */

function prepareFrealign ($extra=False) {
	$expId = $_GET['expId'];
	$projectId = getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$runname = $_POST['runname'];

	$nodes = $_POST['nodes'];
	$ppn = $_POST['ppn'];
	$outdir = $_POST['outdir'];
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	/*
	if ($_POST['ppn'] > C_PPN_MAX )
		jobForm("ERROR: Max processors per node is ".C_PPN_MAX);
	if ($_POST['nodes'] > C_NODES_MAX )
		jobForm("ERROR: Max nodes on ".C_NAME." is ".C_NODES_MAX);
	*/

	if ($_POST['initmethod']=='projmatch' && !$_POST['dang'])
		jobForm("<b>ERROR:</b> Enter an angular increment");
	if (!$_POST['mask'])
		jobForm("<b>ERROR:</b> Enter an outer mask radius");

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

	$last=$_POST['last'];
	$cs=$_POST['cs'];
	$kv=$_POST['kv'];
	$mask=$_POST["mask"];
	$imask=$_POST["imask"];
	$wgh=$_POST["wgh"];
	$xstd=$_POST["xstd"];
	$pbc=$_POST["pbc"];
	$boff=$_POST["boff"];
	$dang = ($_POST['initmethod']=='projmatch') ? $_POST["ang"] : '';
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
	$ctffindonly=($_POST['ctffindonly']=='on') ? True:'';

	$cmd = "prepFrealign.py ";
	$cmd.= "--runname=$runname ";
	$cmd.= "--rundir=$rundir ";
	$cmd.= "--project=$projectId ";
	$cmd.= "--stackid=$stackid ";
	$cmd.= "--modelid=$modelid ";
	if ($importiter) $cmd.= "--reconiterid=$importiter ";
	if ($dang) $cmd.= "--dang=$dang ";

	$cmd.= "--mask=$mask ";
	$cmd.= "--imask=$imask ";
	$cmd.= "--wgh=$wgh ";
	$cmd.= "--xstd=$xstd ";
	$cmd.= "--pbc=$pbc ";
	$cmd.= "--boff=$boff ";
	$cmd.= "--itmax=$itmax ";
	$cmd.= "--ipmax=$ipmax ";
	$cmd.= "--sym=$sym ";
	$cmd.= "--target=$target ";
	$cmd.= "--thresh=$thresh ";
	$cmd.= "--cs=$cs --kv=$kv ";
	$cmd.= "--rrec=$rrec --hp=$hp --lp=$lp --rbfact=$rbfact ";
	$cmd.= "--numiter=$numiter ";
	#enforce cluster mode, for now
	$cmd.= "--cluster ";
	$cmd.= "--ppn=$ppn ";
	$cmd.= "--nodes=$nodes ";
	if ($ctffindonly) $cmd.= "--ctffindonly ";
	if ($last) $cmd.= "--last=$last ";

	// submit job to cluster
	if ($_POST['process'] == "Prepare Frealign") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) jobForm("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($cmd,$outdir,$runname,$expId,'prepfrealign',False,False);
		// if errors:
		if ($sub) jobForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Frealign Job Generator","Frealign Job Generator", $javafunc);

		echo"
		<TABLE WIDTH='600'>
		<TR><TD COLSPAN='2'>
		<B>Frealign Command:</B><br/>
		$cmd<HR>
		</TD></tr>";

		echo "</table>\n";
		processing_footer(True, True);
	}
	exit;
};

