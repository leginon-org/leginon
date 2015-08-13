<?php
/**
 *	The Leginon software is Copyright 2003
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see http://ami.scripps.edu/software/leginon-license
 *
 *	Make stack function
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/appionloop.inc";

/* Boxsize rules:
* (1) no prime factor greater than 11
* (2) if greater than 4^x, must be multiple of 2^x, 
* (3) surely no one will make a stack bigger than 5000 pixels
*/

$goodboxes = array(
	4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64, 72, 80, 96, 
	112, 120, 128, 144, 160, 176, 192, 200, 224, 240, 256, 288, 
	320, 336, 352, 384, 400, 432, 448, 480, 512, 560, 576, 640, 
	672, 704, 720, 768, 800, 864, 896, 960, 1024, 1120, 1152, 
	1280, 1344, 1408, 1440, 1536, 1568, 1600, 1728, 1760, 1792, 
	1920, 2016, 2048, 2112, 2240, 2304, 2400, 2464, 2560, 2592, 
	2688, 2816, 2880, 3072, 3136, 3168, 3200, 3360, 3456, 3520, 
	3584, 3840, 3872, 4000, 4032, 4096, 4224, 4480, 4608, 4800, 
	4928, 5120,
);

if ($_POST['process']) {
	// IF VALUES SUBMITTED, EVALUATE DATA
	runMakestack();
} else {
	// Create the form page
	createMakestackForm();
}

function createMakestackForm($extra=false, $title='Makestack.py Launcher', $heading='Create an Image Stack') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=getProjectId();

	// connect to particle and ctf databases
	$particle = new particledata();
	$ctfdata=$particle->hasCtfData($sessionId);
	$ctftiltdata=$particle->hasCtfTiltData($sessionId);
	$ctffindids = $particle->getCtfRunIds($sessionId,$showHidden=False,$ctffind=True);
	$ctfruns = $particle->getCtfRunIds($sessionId,$showHidden=False,$ctffind=False);
	$partrunids = $particle->getParticleRunIds($sessionId);
	$massessrunIds = $particle->getMaskAssessRunIds($sessionId);
	$stackruninfos = $particle->getStackIds($sessionId, True);
	$nohidestackruninfos = $particle->getStackIds($sessionId, False);
	$stackruns = ($stackruninfos) ? count($stackruninfos):0;

	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$sessionpath=getBaseAppionPath($sessioninfo).'/stacks/';

	// Set any existing parameters in form
	$single = ($_POST['single']) ? $_POST['single'] : 'start.hed';
	$rundescrval = ($_POST['description']) ? $_POST['description'] : True;
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$sessionpathval = (substr($sessionpathval, -1) == '/')? $sessionpathval : $sessionpathval.'/';
	while (file_exists($sessionpathval.'stack'.($stackruns+1)))
		$stackruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'stack'.($stackruns+1);
	$partrunval = ($_POST['partrunid']) ? $_POST['partrunid'] : -1;
	$labelcheck = ($_POST['labelcheck']=='on') ? 'checked' : '';
	$labeldisable = ($_POST['labelcheck']=='on') ? '' : 'disabled';
	$fromstackval = ($_POST['fromstackid']) ? $_POST['fromstackid'] : '0';
	if ($_POST['fromstackid'] && !$_POST['partrunid']) $partrunval = 0;
	$massessval = $_POST['massessname'];
	// set phaseflip on by default
	$phasecheck = ($_POST['ctfcorrect']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	$boxfilescheck = ($_POST['boxfiles']=='on') ? 'CHECKED' : '';
	$helicalcheck = ($_POST['helicalcheck']=='on') ? 'CHECKED' : '';
	$boxmaskcheck = ($_POST['boxmaskcheck']=='on') ? 'CHECKED' : '';
	$boxdisp = ($_POST['boxmaskcheck']=='on') ? 'block' : 'none';
	$boxmask = ($_POST['boxmask']) ? $_POST['boxmask'] : '240';
	$iboxmask = ($_POST['iboxmask']) ? $_POST['iboxmask'] : '0';
	$boxlen = ($_POST['boxlen']) ? $_POST['boxlen'] : '300';
	$falloff = ($_POST['falloff']) ? $_POST['falloff'] : '90';
	$finealigncheck = ($_POST['finealigncheck']=='on') ? 'CHECKED' : '';
	$inspectcheck = ($_POST['inspected']=='off') ? '' : 'CHECKED';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'CHECKED' : '';

	$binval = ($_POST['bin']) ? $_POST['bin'] : '2';
	$partlimit = $_POST['partlimit'];
	$lpval = ($_POST['lp']) ? $_POST['lp'] : '';
	$hpval = ($_POST['hp']) ? $_POST['hp'] : '';
	// ice check params
	$iceval = ($_POST['icecheck']=='on') ? $_POST['ice'] : '0.8';
	$icecheck = ($_POST['icecheck']=='on') ? 'CHECKED' : '';
	$icedisable = ($_POST['icecheck']=='on') ? '' : 'DISABLED';
	// ctf check params
	$ctfcheck = ($_POST['aceconf']=='on') ? 'CHECKED' : '';
	$ctffindcheck = ($_POST['ctffindonly'])=='on' ? 'CHECKED' : '';
	$ctfdisable = ($_POST['aceconf']=='on') ? '' : 'DISABLED';
	$ctfval = ($_POST['aceconf']=='on') ? $_POST['ctf'] : '0.8';
	$ctfrescheck = ($_POST['ctfres']=='on') ? 'CHECKED' : '';
	$ctfresdisable = ($_POST['ctfres']=='on') ? '' : 'DISABLED';
	$ctfres80max = ($_POST['ctfres']=='on') ? $_POST['ctfres80max'] : '';
	$ctfres50max = ($_POST['ctfres']=='on') ? $_POST['ctfres50max'] : '';
	$ctfres80min = ($_POST['ctfres']=='on') ? $_POST['ctfres80min'] : '';
	$ctfres50min = ($_POST['ctfres']=='on') ? $_POST['ctfres50min'] : '';
	// correlation check params
	$selexminval = ($_POST['partcutoff']=='on') ? $_POST['correlationmin'] : '0.5';
	$selexmaxval = ($_POST['partcutoff']=='on') ? $_POST['correlationmax'] : '1.0';
	$selexcheck = ($_POST['partcutoff']=='on') ? 'CHECKED' : '';
	$selexdisable = ($_POST['partcutoff']=='on') ? '' : 'DISABLED';
	// density check (checked by default)
	$invcheck = ($_POST['stackinv']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	$overridecheck = ($_POST['override']=='on') ? 'CHECKED' : '';
	// defocus pair check
	$defocpaircheck = ($_POST['stackdfpair']=='on') ? 'checked' : '';
	$ddnframe = $_POST['ddnframe'];
	$ddstartframe = $_POST['ddstartframe'];
	$forceInsert = ($_POST['forceInsert']=='on' || (!isset($_POST['forceInsert']) && !$_POST) ) ? 'CHECKED' : '';
	$pixlimitv = ($_POST['pixlimit']) ? $_POST['pixlimit'] : '4';
	$normoptions = array(
		'edgenorm'=>'edgenorm: normalize by mean 0 stdev 1 in based on edge pixels',
		'none'=>'none: do not normalize particle images',
		'boxnorm'=>'boxnorm: normalize by mean 0 stdev 1 in whole box',
		'rampnorm'=>'rampnorm: normalize by subtracting a least squares 2D plane',
		//'parabolic'=>'normalize by subtracting a least squares 2D parabola',
	);
	$ctfoptions = array(
		'ace2image'=>'Ace 2 Wiener Filter Whole Image',
		'ace2imagephase'=>'Ace 2 PhaseFlip Whole Image',
		'spiderimage'=>'SPIDER PhaseFlip Whole Image (no astig)',
		'emanimage'=>'EMAN1 PhaseFlip Whole Image (no astig)',
		'emanpart'=>'EMAN1 PhaseFlip Particle (no astig)',
	);
	if ($ctftiltdata) {
		$ctfoptions['emantilt'] = 'EMAN PhaseFlip by Tilt Location';
		$limitedctfoptions['emantilt'] = 'EMAN PhaseFlip by Tilt Location';
	}
	$ctfsortoptions = array(
		'res80'=>'Resolution 0.8 criteria',
		'res50'=>'Resolution 0.5 criteria',
		'resplus'=>'Sum of Res 0.5 + Res 0.8',
		'maxconf'=>'Maximum confidence value',
		'conf3010'=>'Confidence btw 1/30A and 1/10A',
		'conf5peak'=>'5 peaks confidence',
		'crosscorr'=>'CtfFind cross correlation',
	);
	$javascript="<script src='../js/viewer.js'></script>
	<script type='text/javascript'>

	function enablectf(){
		if (document.viewerform.aceconf.checked){
			document.viewerform.ctf.disabled=false;
			document.viewerform.ctf.value='0.8';
		} else {
			document.viewerform.ctf.disabled=true;
			document.viewerform.ctf.value='0.8';
		}
	}

	function enablectfres() {
		if (document.viewerform.ctfres.checked){
			document.viewerform.ctfres80max.disabled=false;
			document.viewerform.ctfres50max.disabled=false;
			document.viewerform.ctfres80min.disabled=false;
			document.viewerform.ctfres50min.disabled=false;
			document.viewerform.ctfres80max.value='';
			document.viewerform.ctfres50max.value='';
			document.viewerform.ctfres80min.value='';
			document.viewerform.ctfres50min.value='';
		} else {
			document.viewerform.ctfres80max.disabled=true;
			document.viewerform.ctfres50max.disabled=true;
			document.viewerform.ctfres80min.disabled=true;
			document.viewerform.ctfres50min.disabled=true;
		}
	}


	function toggleboxmask() {
		if (document.getElementById('boxmaskopts').style.display == 'none' || document.getElementById('boxmaskopts').style.display == '') {
			document.getElementById('boxmaskopts').style.display = 'block';
		}
		else {
			document.getElementById('boxmaskopts').style.display = 'none';
		}
	}

	function enablectftype() {
		if (document.viewerform.ctfcorrect.checked){
			document.viewerform.ctfcorrecttype.disabled=false;
			document.viewerform.ctfsorttype.disabled=false;
		} else {
			document.viewerform.ctfcorrecttype.disabled=true;
			document.viewerform.ctfsorttype.disabled=true;
		}
	}

	function enableselex(){
		if (document.viewerform.partcutoff.checked){
			document.viewerform.correlationmin.disabled=false;
			document.viewerform.correlationmin.value='0.5';
			document.viewerform.correlationmax.disabled=false;
			document.viewerform.correlationmax.value='1.0';
		} else {
			document.viewerform.correlationmin.disabled=true;
			document.viewerform.correlationmin.value='0.5';
			document.viewerform.correlationmax.disabled=true;
			document.viewerform.correlationmax.value='1.0';
		}
	}

	function partrunToNone() {
		if (document.viewerform.fromstackid.value != 0) {
			document.viewerform.partrunid.value = 0
		}
		document.viewerform.submit()
	}

	function fromstackToNone() {
		if (document.viewerform.partrunid.value != 0) {
			document.viewerform.fromstackid.value = 0
		}
		document.viewerform.submit()
	}

	function enablelabel() {
		if (document.viewerform.labelcheck.checked) {
			document.viewerform.partlabel.disabled=false;
		} else {
			document.viewerform.partlabel.disabled=true;
		}
	}

	</script>\n";
	$javascript .= writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javascript);

	if (!$partrunids && !$nohidestackruninfos) {
		echo "<font color='#cc3333' size='+2'><b>No particles available for this session; pick some particles first</b></font>\n";
		exit;
	}

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"<FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
	
	echo "<table border=0 class=tableborder>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo "<table cellpadding='5' border='0'>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";

#	echo docpop('stackname','<b>Stack File Name:</b>');
	echo "<input type='hidden' name='single' value='start.hed'>\n";
#	echo "<br />\n";
#	echo "<br />\n";

#	echo docpop('stackdescr','<b>Stack Description:</b>');
#	echo "<br/>\n";
#	echo "<textarea name='description' rows='2' cols='50'>$rundescrval</textarea>\n";
#	echo "<br/>\n";
#	echo "<br/>\n";
	
	createAppionLoopTable($sessiondata, $runnameval, "stacks", 0, $rundescrval);

	echo "<b>Density modifications:</b><br/>";

	echo "<input type='checkbox' name='stackinv' $invcheck>\n";
	echo docpop('stackinv','Invert image density');
	echo "<br/>\n";

	//
	// STARTING ADVANCED SECTION 1
	//
	// Only hide advanced parameters if there is not an advanced user logged in.
	// Modify user profile to set to an advanced user. 
	// NOTE: this assumes the Appion user name and the username that is used to log in to the processing page are the same.
	// We may want to change that someday.
	if ( !$_SESSION['advanced_user'] ) {	
		echo "<a id='Advanced_Stack_Options_1_toggle' href='javascript:toggle(\"Advanced_Stack_Options_1\");' style='color:blue'>";
		echo "Show Advanced Stack Options</a><br/>\n";
		echo "<div id='Advanced_Stack_Options_1' style='display: none'>\n";
	}

	// select normalization method
	echo docpop('normalizemethod','Normalization Method');
	echo "<br/>\n";
	echo "&nbsp;&nbsp;<select name='normalizemethod' ";
	echo ">\n";
	foreach ($normoptions as $key => $text) {
		$selected = ($_POST['normalizemethod']==$key) ? 'SELECTED':'';
		echo "<option value='$key' $selected>$text</option>";
	}
	echo "</select>\n";
	echo "<br/><br/>";

	/* SPIDER IS BROKEN
	echo "<i>File format:</i>";
	echo "<br/>\n";

	echo "&nbsp;<input type='radio' name='fileformat' value='imagic' ";
	if ($_POST['fileformat'] == 'imagic' || !$_POST['checkimage']) echo "checked";
	echo ">\n";
	echo "Imagic: start.hed/.img <font size='-2'><i>(default)</i></font><br/>\n";

	echo "&nbsp;<input type='radio' name='fileformat' value='spider' ";
	if ($_POST['fileformat'] == 'spider') echo "checked";
	echo ">\n";
	echo "Spider: start.spi<br/>\n";
	*/
	echo "<input type='hidden' name='fileformat' value='imagic'> ";

	//
	// ENDING ADVANCED SECTION 1
	//
	echo "</div>\n";

	//echo "</td></tr></table>";
	echo "</td><td class='tablebg' valign='top'>";
	//echo "<table cellpadding='5' border='0'><tr><td valign='TOP'>";
	
	$partruns=count($partrunids);

	if (!$partrunids) {
		echo "<font class='apcomment'><b>No Particles for this Session</b></font>\n";
	} else {
		echo docpop('stackparticles','Particles:');
		echo "<select name='partrunid' onchange='fromstackToNone()'>\n";
		echo "<option value='0'>None</option>\n";
		foreach ($partrunids as $partrun){
			$partrunid=$partrun['DEF_id'];
			$runname=$partrun['name'];
			$partstats=$particle->getStats($partrunid);
			$numPart = $partstats['totparticles'];
			if ($numPart == 0)
				continue;
			$totparts=commafy($numPart);
			echo "<option value='$partrunid'";
			// select previously set part on resubmit
			if ($partrunval==$partrunid) {
				echo " selected";
			} elseif ($partrunval==-1) {
				echo " selected";
				$partrunval=$partrunid;
			}			
			echo">$runname ($totparts parts)</option>\n";
		}
		echo "</select>\n";

		// get particle selection parameters
		$partrundata = $particle->getSelectionParams($partrunval);
		// add particle label page
		$particlelabels = $particle->getParticleLabels($partrunval);
		// use fromtrace label to activate particle insertion from traced center
		$traceconverted = false;
		if ($partrundata[0]['trace'] == 1)
			$particlelabels[]=array('label'=>'fromtrace');
		// if "Stored Helices" label, remove from list
		$particlelabelsEdit=array();
		foreach ($particlelabels as $row) {
			$label = $row['label'];
			if ($label == 'Stored Helices') {$storedhelices = True; continue;}
			$particlelabelsEdit[]=$row;
		}
		$particlelabels=$particlelabelsEdit;
		if (!empty($particlelabels)) {
			echo "<br/>\n";
			echo"<input type='checkbox' name='labelcheck' onclick='enablelabel()' $labelcheck >\n";
			echo docpop('stackparticlelabels','Particle labels:');
			echo "<select name='partlabel' $labeldisable >\n";
			foreach ($particlelabels as $row) {
				$label=$row['label'];
				if ($label == '_trace') $traceconverted = true;
				if ($label == 'fromtrace' && $traceconverted == true) continue;
				$sel = (trim($_POST['partlabel'])==$label) ? 'selected' : '';
				echo '<option value="'.$label.'" '.$sel.' >'.$label."</option>\n";
			}
			echo "</select>\n";
		} else {
			echo "<input type='hidden' name='labelcheck' value='off' >";
			echo "<input type='hidden' name='partlabel' value='' >";
		}
		echo "<br/><br/>\n";

		// add stack selection page
	}
	if ($nohidestackruninfos) {
		echo docpop('stackparticles2','Stacks:');
		echo "<select name='fromstackid' onchange='partrunToNone()'>\n";
		echo "<option value='0'>None</option>\n";
		foreach ($nohidestackruninfos as $stackruninfo){
			$stackid = $stackruninfo['stackid'];
			$numpart = commafy($particle->getNumStackParticles($stackid));
			$stackdata = $particle->getStackParams($stackid);
			$stackname = $stackdata['shownstackname'];
			echo "<option value='$stackid'";
			// select previously set part on resubmit
			if ($fromstackval==$stackid) {
				echo " selected";
			}
			echo">$stackname ($numpart parts)</option>\n";
		}
		echo "</select>\n";
		// add stack selection page
	} else {
		echo "<input type='hidden' name='fromstackid' value='0'>";
	}
	echo "<br/>\n";
	echo "<br/>\n";

	// Determine best box size...

	if (!$_POST['boxsize']) {
		$imgid = $particle->getImgIdFromSelectionRun($partrunval);
		$partdiam = $partrundata[0]['diam'];
		$helicalstep = $partrundata[0]['helicalstep'];
		$pixelsize = $particle->getPixelSizeFromImgId($imgid)*1e10;
		//echo "Diameter: $partdiam &Aring;<br/>\n";
		//echo "Image id: $imgid<br/>\n";
		//echo "Pixel size: $pixelsize &Aring;<br/>\n";
		if ($helicalstep) {
			$boxdiam = (int) ($helicalstep/$pixelsize);
		}
		else {
			$pixdiam = (int) ($partdiam/$pixelsize);
			//echo "Pixel diam: $pixdiam pixels<br/>\n";
			$boxdiam = (int) ($partdiam/$pixelsize*1.4);
			//echo "Box diam: $boxdiam pixels<br/>\n";
		}
		global $goodboxes;
		foreach ($goodboxes as $box) {
			if ($box >= $boxdiam) {
				$defaultboxsize = $box;
				break;
			}
		}
		//echo "Box size: $defaultboxsize pixels<br/>\n";
		$boxszval = $defaultboxsize;
	} else {
		$boxszval = $_POST['boxsize'];
	}
	echo "<input type='text' name='boxsize' size='5' value='$boxszval'>\n";
	echo docpop('boxsize','Box Size');
	echo "(Unbinned, in pixels)<br />\n";
	echo "<input type='checkbox' name='override' $overridecheck>\n";
	echo "<font size='-2'>(override boxsize)</font><br/>\n";
	echo "<br/>\n";

	echo "<input type='text' name='bin' value='$binval' size='4'>\n";
	echo docpop('stackbin','Binning');
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<input type='checkbox' name='forceInsert' $forceInsert>\n";
	echo docpop('force','Fast Insert');
	
	echo "<br/>\n";
	echo "<br/>\n";


	if ($ctfdata) {
		echo "<table style='border: 1px solid black; padding:5px; background-color:#f9f9ff; ' ><tr ><td>\n\n";

		// use ctf correction
		echo"<input type='checkbox' name='ctfcorrect' onclick='enablectftype(this)' $phasecheck>\n";
		echo docpop('ctfcorrect','Ctf Correct Particle Images');

		echo "<br/><br/>";
		echo "</td></tr><tr><td>\n\n";

		// confidence cutoff
		echo"<input type='checkbox' name='aceconf' onclick='enablectf(this)' $ctfcheck>\n";
		echo docpop('aceconf','CTF Confidence Cutoff');
		echo "<br />\n";
		echo "Use Values Above:<input type='text' name='ctf' $ctfdisable value='$ctfval' size='4'>
		(between 0.0 - 1.0)\n";

		echo "<br/><br/>";

		//
		// STARTING ADVANCED CTF SECTION
		//
		// Only hide advanced parameters if there is not an advanced user logged in.
		// Modify user profile to set to an advanced user. 
		// NOTE: this assumes the Appion user name and the username that is used to log in to the processing page are the same.
		// We may want to change that someday.
		if ( !$_SESSION['advanced_user'] ) {
			echo "<a id='Advanced_Ctf_Options_toggle' href='javascript:toggle(\"Advanced_Ctf_Options\");' style='color:blue'>";
			echo "Show Advanced CTF Options</a><br/>\n";
			echo "<div id='Advanced_Ctf_Options' style='display: none'>\n";
		}

		// select correction method
		echo docpop('ctfcorrectmeth','CTF Correction Method');
		echo "<br/>\n";
		echo "&nbsp;&nbsp;<select name='ctfcorrecttype' ";
		if (!$phasecheck) echo " disabled";
		echo ">\n";
		foreach ($ctfoptions as $key => $text) {
			$selected = ($_POST['ctfcorrecttype']==$key) ? 'SELECTED':'';
			echo "<option value='$key' $selected>$text</option>";
		}
		echo "</select>\n";

		echo "<br/><br/>";
		//echo "</td></tr><tr><td>\n\n";

		// select cutoff types method
		echo docpop('ctfsort','CTF Sorting Method');
		echo "<br/>\n";
		echo "&nbsp;&nbsp;<select name='ctfsorttype' ";
		if (!$phasecheck) echo " disabled";
		echo ">\n";
		foreach ($ctfsortoptions as $key => $text) {
			$selected = ($_POST['ctfsorttype']==$key) ? 'SELECTED':'';
			echo "<option value='$key' $selected>$text</option>";
		}
		echo "</select>\n";

		echo "<br/>";

		$empty_array=array(array('DEF_id'=> 0,'name' => 'all'));
		$ctfruns=array_merge ($empty_array,$ctfruns);
		echo "-OR- choose a ctf run:\n";
		echo "&nbsp;&nbsp;<select name='ctfrunID'>\n";
		foreach ($ctfruns as $ctfrun) {
			$ID=$ctfrun['DEF_id'];
			$ctfname=$ctfrun['name'];
			$selected = ($_POST['ctfrunID']==$ID) ? 'SELECTED':'';
			echo "<option value='$ID' $selected>$ctfname ($ID)</option>";
		}
		echo "</select>\n";

		echo "<br/>";

			// give option of only using ctffind values
		if ($ctffindids) {
			echo "-OR- <input type='checkbox' name='ctffindonly' $ctffindcheck>\n";
			echo docpop('ctffindonly','Only use CTFFIND values');
			echo "<br/>\n";
		}

		echo "<br/>";
		//echo "</td></tr><tr><td>\n\n";

		// resolution cutoff
		echo"<input type='checkbox' name='ctfres' onclick='enablectfres(this)' $ctfrescheck>\n";
		echo docpop('ctfres','CTF Resolution Cutoff');
		echo "<br />\n";
		echo "&nbsp;&nbsp;Resolution range at 0.8 criteria: <br/>";
			echo "between <input type='text' name='ctfres80min' value='$ctfres80min' size='4' $ctfresdisable>";
			echo "and <input type='text' name='ctfres80max' value='$ctfres80max' size='4' $ctfresdisable>";
			echo "&nbsp; <i>(in &Aring;ngstroms)</i>\n";
		echo "<br/>\n";
		echo "&nbsp;&nbsp;Resolution range at 0.5 criteria: <br/>";
			echo "between <input type='text' name='ctfres50min' value='$ctfres50min' size='4' $ctfresdisable>";
			echo "and <input type='text' name='ctfres50max' value='$ctfres50max' size='4' $ctfresdisable>";
			echo "&nbsp; <i>(in &Aring;ngstroms)</i>\n";

		echo "<br/><br/>";
		//echo "</td></tr><tr><td>\n\n";

		// defocus cutoff
		$fields = array('defocus1', 'defocus2');
		$bestctf = $particle->getBestStats($fields, $sessionId);
		// make sure defocus is always negative
		$min=-1*abs($bestctf['defocus1'][0]['min']);
		$max=-1*abs($bestctf['defocus1'][0]['max']);
		//echo $min."<br/>\n";
		//echo $max."<br/>\n";
		// check if user has changed values on submit
		$minval = ($_POST['dfmin']!=$min && $_POST['dfmin']!='' && $_POST['dfmin']!='-') ? $_POST['dfmin'] : $min;
		$maxval = ($_POST['dfmax']!=$max && $_POST['dfmax']!='' && $_POST['dfmax']!='-') ? $_POST['dfmax'] : $max;
		$minval = preg_replace("%E%","e",round($minval,8));
		$maxval = preg_replace("%E%","e",round($maxval,8));
		$mindbval = preg_replace("%E%","e",round($min,8));
		$maxdbval = preg_replace("%E%","e",round($max,8));
		echo"<b>Defocus Limits</b><br />
				Min <input type='text' name='dfmin' value='$minval' size='8'>
				<input type='hidden' name='dbmin' value='$mindbval'>
			 & Max
				<input type='text' name='dfmax' value='$maxval' size='8'>
				<input type='hidden' name='dbmax' value='$maxdbval'>
			\n";
		echo "<br/>\n";
		echo "<br/>\n";

		echo "</div>\n";	
		
		echo "</td></tr></table>\n";
		echo "<br/>\n";
		echo "<br/>\n";
		
	
	}

	//
	// STARTING ADVANCED SECTION 2
	//
	// Only hide advanced parameters if there is not an advanced user logged in.
	// Modify user profile to set to an advanced user. 
	// NOTE: this assumes the Appion user name and the username that is used to log in to the processing page are the same.
	// We may want to change that someday.
	if ( !$_SESSION['advanced_user'] ) {
		echo "<a id='Advanced_Stack_Options_2_toggle' href='javascript:toggle(\"Advanced_Stack_Options_2\");' style='color:blue'>";
		echo "Show Advanced Stack Options</a><br/>\n";
		echo "<div id='Advanced_Stack_Options_2' style='display: none'>\n";
	}
	echo "<br/>\n";

	$massessruns=count($massessrunIds);
	$massessname = '';
	$massessnames= $particle->getMaskAssessNames($sessionId);

	if (!$massessnames) {
		echo"<font size='-1'><i>No Mask Assessed for this Session</i></font>\n";
	} else {
		echo "Mask Assessment:
		<select name='massessname'>\n";
		foreach ($massessnames as $name) {
			$massessname = $name;
			$massessruns = $particle->getMaskAssessRunByName($sessionId,$massessname);
			$totkeeps = 0;
			foreach ($massessruns as $massessrun){
				$massessrunId=$massessrun['DEF_id'];
				$massessstats=$particle->getMaskAssessStats($massessrunId);
				$permaskkeeps=$massessstats['totkeeps'];
				$totkeeps = $totkeeps + $permaskkeeps;
			}
			echo "<OPTION value='$massessname'";
			// select previously set assessment on resubmit
			if ($massessval==$massessname) echo " selected";
			$totkeepscm=commafy($totkeeps);
			echo">$massessname ($totkeepscm regions)</OPTION>\n";
		}
		echo "</select>\n";
	}
	echo "<br/>\n";
	echo "<br/>\n";

	// for boxing helical segments
	if ($storedhelices) {
		$hstep = ($_POST['boxhstep']) ? $_POST['boxhstep']:'';
		echo "<input type='text' name='boxhstep' size='5' value='$hstep'>\n";
		echo docpop('helicalstep', 'Helical Step');
		echo " <font SIZE=-2><I>(in &Aring;ngstroms)</I></font>\n";
		echo "<br>\n";
	}

	// raw frame processing gui assuming presetname is ed
	// This feature only works with Python 2.6
	echo "<b>Raw frame processing if available: </b><br/>\n";
	echo "start frame:<input type='text' name='ddstartframe' value='$ddstartframe' size='3'>\n";
	echo docpop('makeDDStack.ddstartframe', 'start frame');
	echo "total frame:<input type='text' name='ddnframe' value='$ddnframe' size='3'>\n";
	echo docpop('makeDDStack.ddnframe', 'total frames');
	echo "<br/><br/>\n";

	echo "<b>Filter Values:</b><br/>";

	echo "<input type='text' name='lp' value='$lpval' size='4'>\n";
	echo docpop('lpstackval', 'Low Pass');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br/>\n";

	echo "<input type='text' name='hp' value='$hpval' size='4'>\n";
	echo docpop('hpstackval', 'High Pass');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br/>\n";

	echo "<input type='text' name='pixlimit' VALUE='$pixlimitv' size='4'>\n";
	echo docpop('pixlimit',' Pixel Limit');
	echo "<font size=-2><I>(in Standard Deviations; 0 = off)</I></font><br />\n";


	// commented out for now, since not implemented
//		<input type='checkbox' name='icecheck' onclick='enableice(this)' $icecheck>
//		Ice Thickness Cutoff<br />
//		Use Ice Thinner Than:<input type='text' name='ice' $icedisable value='$iceval' size='4'>
//		(between 0.0 - 1.0)\n";

	echo"<input type='checkbox' name='partcutoff' onclick='enableselex(this)' $selexcheck>\n";
	echo docpop('partcutoff','Particle Correlation Cutoff');
	echo "<br />\n";
	echo "Remove particles with CCC below:<input type='text' name='correlationmin' $selexdisable value='$selexminval' size='4'><br/>\n";
	echo "Remove particles with CCC above:<input type='text' name='correlationmax' $selexdisable value='$selexmaxval' size='4'><br/>\n";
	echo "<br/>\n";

	echo "<b>Defocal pairs:</b>\n";
	echo "<br/>\n";
	echo "<input type='checkbox' name='stackdfpair' $defocpaircheck>\n";
	echo docpop('stackdfpair','Use defocal pairs');
	echo "<br/>\n";
	echo "<br/>\n";


	echo docpop('stacklim','Limit # of particles to: ');
	echo "<input type='text' name='partlimit' value='$partlimit' size='8'>\n";
	echo "<br/>\n";
	echo "<input type='checkbox' name='boxfiles' $boxfilescheck>\n";
	echo docpop('boxfiles','Only create EMAN boxfiles');
	echo "<br />\n";

	echo "<br />\n";
	if ($storedhelices) {
		echo "<input type = 'checkbox' name='boxmaskcheck' onclick='toggleboxmask(this)' $boxmaskcheck>\n";
		echo docpop('boxmaskcheck', 'Boxmask the raw particles');
		echo "<br />\n";
		echo "<div id='boxmaskopts' style='display:$boxdisp;'>\n";
		// parameters
		echo "<input type='text' name='boxmask' value='$boxmask' size='4'>\n";
	       	echo docpop('boxmask','Outer Mask Radius: ');
		echo "(in Angstroms)<br/>\n";

		echo "<input type='text' name='iboxmask' value='$iboxmask' size='4'>\n";
		echo docpop('iboxmask','Inner Mask Radius');
		echo "(in Angstroms)<br/>\n";

		echo "<input type='text' name='boxlen' value='$boxlen' size='4'>\n";
		echo docpop('boxlen','Length Mask: ');
		echo "(in Angstroms)<br/>\n";

		echo "<input type='text' name='falloff' value='$falloff' size='4'>\n";
		echo docpop('falloff','Edge Falloff: ');
		echo "(in Angstroms)\n";

		echo "</div>\n";
	}

	echo "<b>Helical Alignment:</b>\n";
	echo "<br />\n";
	echo "<input type='checkbox' name='helicalcheck' $helicalcheck>\n";
	echo docpop('helicalcheck','Apply rough helical rotation angles');
	echo "<br />\n";
	echo "<input type='checkbox' name='finealigncheck' $finealigncheck>\n";
	echo docpop('finealigncheck','Apply fine helical rotation angles');
	echo "<br />\n";

	//
	// ENDING ADVANCED SECTION 2
	//
	echo "</div>\n";

	echo "</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td colspan='2' align='CENTER'>\n";
	echo "<hr/>\n";
	echo getSubmitForm("Make Stack");
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";

	echo appionRef();

	processing_footer();
	exit;
}


function runMakestack() {
	
	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$single=$_POST['single'];
	$description = $_POST['description'];
	
	$invert = ($_POST['stackinv']=='on') ? True : False;
	$normalizemethod = $_POST['normalizemethod'];
	$ctfcorrect = ($_POST['ctfcorrect']=='on') ? 'ctfcorrect' : '';
	$ctfcorrecttype = $_POST['ctfcorrecttype'];
	$ctfsorttype = $_POST['ctfsorttype'];
	$ctfrunID = $_POST['ctfrunID'];
	$stig = ($_POST['stig']=='on') ? 'stig' : '';
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$stackdfpair = ($_POST['stackdfpair']=="on") ? True : False;
	$boxfiles = ($_POST['boxfiles']);
	$boxhstep = ($_POST['boxhstep']);
	$helicalcheck = ($_POST['helicalcheck']);
	$finealigncheck = ($_POST['finealigncheck']);
	$ctffindonly = ($_POST['ctffindonly'])=='on' ? True : False;
	$ddstartframe = $_POST['ddstartframe'];
	$ddnframe = $_POST['ddnframe'];
	$forceInsert = ($_POST['forceInsert'])=='on' ? True : False;
	
	if ($_POST['boxmaskcheck']=='on') {
		$boxmask = $_POST['boxmask'].','.$_POST['boxlen'].','.$_POST['iboxmask'].','.$_POST['falloff'];
	}

	// set image inspection selection
	$norejects=$inspected=0;
	if ($_POST['checkimage']=="Non-rejected") {
		$norejects=1;
	} elseif ($_POST['checkimage']=="Best") {
		$norejects=1;
		$inspected=1;
	}
	
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	// Got a little sloppy here, left some get variable code below to keep some parts easier to read. 
	
	//make sure a session was selected
	if (!$description)
		createMakestackForm("<b>ERROR:</b> Enter a brief description of the stack");

	//make sure a session was selected
	if (!$outdir)
		createMakestackForm("<b>ERROR:</b> Select an experiment session");

	// get particle runId or from stack id
	$partrunid=$_POST['partrunid'];
	$partlabel=(!empty($_POST['partlabel']) && $_POST['labelcheck']=='on') ? $_POST['partlabel'] : '';
	$fromstackid=$_POST['fromstackid'];
	if (!$partrunid && !$fromstackid)
		createMakestackForm("<b>ERROR:</b> No particle run was selected");
	if ($partrunid && $fromstackid)
		createMakestackForm("<b>ERROR:</b> Choose either a stack or particle run, but not both");


	// binning amount
	$bin=$_POST['bin'];
	if ($bin) {
		if (!is_numeric($bin)) createMakestackForm("<b>ERROR:</b> Binning amount must be an integer");
	}
	
	// box size
	$boxsize = $_POST['boxsize'];
	if (!$boxsize)
		createMakestackForm("<b>ERROR:</b> Specify a box size");
	if (!is_numeric($boxsize))
		createMakestackForm("<b>ERROR:</b> Box size must be an integer");
	if ($boxsize % $bin != 0)
		createMakestackForm("<b>ERROR:</b> Box size must be divisible by bin size");

	if ($_POST['override'] != 'on') {
		$binnedbox = (int) floor($boxsize/$bin);
		global $goodboxes;
		foreach ($goodboxes as $box) {
			if ($box == $binnedbox)
				break;
			elseif ($box > $binnedbox) {
				$bigbox = $box*$bin;
				createMakestackForm("<b>ERROR:</b> Bad prime number in boxsize, try using $smallbox or $bigbox instead or check 'override box size' to force");
				exit;
			}
			$smallbox = $box*$bin;
		}	
	}

	// lp filter
	$lp = $_POST['lp'];
	if ($lp && !is_numeric($lp)) createMakestackForm("<b>ERROR:</b> low pass filter must be a number");

	// hp filter
	$hp = $_POST['hp'];
	if ($hp && !is_numeric($hp)) createMakestackForm("<b>ERROR:</b> high pass filter must be a number");

	// pixlimit filter
	$pixlimit = $_POST['pixlimit'];
	if ($pixlimit && !is_numeric($pixlimit)) createMakestackForm("<b>ERROR:</b> pixel limit filter must be a number");

	// ctf cutoff
	if ($_POST['aceconf']=='on') {
		$ctf=$_POST['ctf'];
		if ($ctf > 1 || $ctf < 0 || !$ctf) createMakestackForm("<b>ERROR:</b> CTF cutoff must be between 0 & 1");
	}

	// ctf resolution
	if ($_POST['ctfres']=='on') {
		$ctfres80min=$_POST['ctfres80min'];
		if ($ctfres80min && !is_numeric($ctfres80min) )
			createMakestackForm("<b>ERROR:</b> CTF resolution cutoffs must be a number or blank");
		$ctfres50min=$_POST['ctfres50min'];
		if ($ctfres50min && !is_numeric($ctfres50min) )
			createMakestackForm("<b>ERROR:</b> CTF resolution cutoffs must be a number or blank");
		$ctfres80max=$_POST['ctfres80max'];
		if ($ctfres80max && !is_numeric($ctfres80max) )
			createMakestackForm("<b>ERROR:</b> CTF resolution cutoffs must be a number or blank");
		$ctfres50max=$_POST['ctfres50max'];
		if ($ctfres50max && !is_numeric($ctfres50max) )
			createMakestackForm("<b>ERROR:</b> CTF resolution cutoffs must be a number or blank");
		if ($ctfres50max && $ctfres50min && $ctfres50max < $ctfres50min )
			createMakestackForm("<b>ERROR:</b> CTF resolution cutoffs min must be less than the max");
		if ($ctfres80max && $ctfres80min && $ctfres80max < $ctfres80min )
			createMakestackForm("<b>ERROR:</b> CTF resolution cutoffs min must be less than the max");
	}

	// correlation cutoff
	if ($_POST['partcutoff']=='on') {
		$correlationmin=$_POST['correlationmin'];
		$correlationmax=$_POST['correlationmax'];
		//if ($correlationmin > 1 || $correlationmin < 0) createMakestackForm("<b>ERROR:</b> correlation Min cutoff must be between 0 & 1");
		//if ($correlationmax > 1 || $correlationmax < 0) createMakestackForm("<b>ERROR:</b> correlation Max cutoff must be between 0 & 1");
	}

	// check defocus cutoffs
	//echo "MIN :: $_POST[dfmin] :: $_POST[dbmin]<br/>\n";
	//echo "MAX :: $_POST[dfmax] :: $_POST[dbmax]<br/>\n";
	$dfmin = ($_POST['dfmin']>=$_POST['dbmin']) ? '' : $_POST['dfmin'];
	$dfmax = ($_POST['dfmax']<=$_POST['dbmax']) ? '' : $_POST['dfmax'];
	// mask assessment
	$massessname=$_POST['massessname'];

	// check the tilt situation
	$particle = new particledata();
	$maxang = $particle->getMaxTiltAngle($expId);
	if ($maxang > 5) {
		$tiltangle = $_POST['tiltangle'];
		if ($_POST['ctfcorrect']=='on' && $_POST['ctfcorrecttype']!='emantilt' && !($tiltangle=='notilt' || $tiltangle=='lowtilt')) {
			createMakestackForm("CTF correct does not work on tilted images: $tiltangle ");
			exit;
		}
	}

	// limit the number of particles
	$partlimit=$_POST['partlimit'];
	if ($partlimit) {
		if (!is_numeric($partlimit)) createMakestackForm("<b>ERROR:</b> Particle limit must be an integer");
	} else $partlimit="none";

	//helical alignment
	if ($helicalcheck && $finealigncheck)
		createMakestackForm("<b>ERROR:</b> Select either rough alignment or fine alignment, not both");

	/* *******************
	PART 3: Create program command
	******************** */
	
	$command = "makestack2.py"." ";
	$command.="--single=$single ";
	if ($partrunid)
		$command.="--selectionid=$partrunid ";
	elseif ($fromstackid)
		$command.="--fromstackid=$fromstackid ";
	if ($lp) $command.="--lowpass=$lp ";
	if ($hp) $command.="--highpass=$hp ";
	if ($pixlimit) $command.="--pixlimit=$pixlimit ";
	$command.= ($invert) ? "--invert " : "--no-invert ";
	if ($normalizemethod) $command.="--normalize-method=$normalizemethod ";
	if ($ctfcorrect) { 
		$command.="--phaseflip --flip-type=$ctfcorrecttype --sort-type=$ctfsorttype ";
	}
	if ($massessname) $command.="--maskassess=$massessname ";
	$command.="--boxsize=$boxsize ";
	if ($bin > 1) $command.="--bin=$bin ";
	if ($ctf) $command.="--ctfcutoff=$ctf ";
	if ($_POST['ctfres']=='on') {
		if ($_POST['ctfres80min'])
			$command.="--ctfres80min=$ctfres80min ";
		if ($_POST['ctfres50min'])
			$command.="--ctfres50min=$ctfres50min ";
		if ($_POST['ctfres80max'])
			$command.="--ctfres80max=$ctfres80max ";
		if ($_POST['ctfres50max'])
			$command.="--ctfres50max=$ctfres50max ";
	}

	if ($stackdfpair) $command.="--defocpair ";
	if ($correlationmin) $command.="--mincc=$correlationmin ";
	if ($correlationmax) $command.="--maxcc=$correlationmax ";
	if ($dfmin) $command.="--mindef=$dfmin ";
	if ($dfmax) $command.="--maxdef=$dfmax ";
	if ($_POST['fileformat']=='spider') $command.="--spider ";
	if ($partlimit != "none") $command.="--partlimit=$partlimit ";
	if ($boxfiles == 'on') $command.="--boxfiles ";
	// Don't need description here after converting appionloop
	//$command.="--description=\"$description\" ";
	if (!empty($partlabel)) $command.="--label=\"$partlabel\" ";
	if ($ctffindonly) $command.="--ctfmethod=ctffind ";
	if ($boxhstep) $command.="--helicalstep=$boxhstep ";
	if ($helicalcheck == 'on') $command.="--rotate ";
	elseif ($finealigncheck == 'on') $command.="--rotate --finealign ";
	if ($ddstartframe) $command.=" --ddstartframe=$ddstartframe ";
	if ($ddnframe) $command.=" --ddnframe=$ddnframe ";
	if ($ctfrunID) $command.="--ctfrunid=$ctfrunID ";
	if ($boxmask) $command.="--boxmask='$boxmask' ";
	if ($forceInsert) $command.="--forceInsert ";
	
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createMakestackForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef();
	
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$nproc = 1;
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack2', $nproc);

	// if error display them
	if ($errors)
		createMakestackForm("<b>ERROR:</b> $errors");
}
	
?>
