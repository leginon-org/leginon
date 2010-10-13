<?php
/**
 *	The Leginon software is Copyright 2003
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see http://ami.scripps.edu/software/leginon-license
 *
 *	Make stack function
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/appionloop.inc";

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
	$ctffindids = $particle->getCtfRunIds($sessionId,$showHidden=False,$ctffind=True);
	$partrunids = $particle->getParticleRunIds($sessionId);
	$massessrunIds = $particle->getMaskAssessRunIds($sessionId);
	$stackruninfos = $particle->getStackIds($sessionId, True);
	$nohidestackruninfos = $particle->getStackIds($sessionId, False);
	$stackruns = ($stackruninfos) ? count($stackruninfos):0;



	$javascript="<script src='../js/viewer.js'></script>
	<script type='text/javascript'>

	function enableace(){
		if (document.viewerform.acecheck.checked){
			document.viewerform.ace.disabled=false;
			document.viewerform.ace.value='0.8';
		} else {
			document.viewerform.ace.disabled=true;
			document.viewerform.ace.value='0.8';
		}
	}

	function enablexmipp(){
		if (document.viewerform.xmippnormcheck.checked){
			document.viewerform.xmippnormval.disabled=false;
			document.viewerform.xmippnormval.value='4.5';
		} else {
			document.viewerform.xmippnormval.disabled=true;
			document.viewerform.xmippnormval.value='4.5';
		}
	}

	function enablectftype() {
		if (document.viewerform.ctfcorrect.checked){
			document.viewerform.ctfcorrecttype.disabled=false;
		} else {
			document.viewerform.ctfcorrecttype.disabled=true;
		}
	}

	function enableselex(){
		if (document.viewerform.selexcheck.checked){
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
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","stacks/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// Set any existing parameters in form
	$single = ($_POST['single']) ? $_POST['single'] : 'start.hed';
	$rundescrval = ($_POST['description']) ? $_POST['description'] : True;
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'stack'.($stackruns+1)))
		$stackruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'stack'.($stackruns+1);
	$partrunval = ($_POST['partrunid']) ? $_POST['partrunid'] : $partrunids[0]['DEF_id'];
	$labelcheck = ($_POST['labelcheck']=='on') ? 'checked' : '';
	$labeldisable = ($_POST['labelcheck']=='on') ? '' : 'disabled';
	$fromstackval = ($_POST['fromstackid']) ? $_POST['fromstackid'] : '0';
	if ($_POST['fromstackid'] && !$_POST['partrunid']) $partrunval = 0;
	$massessval = $_POST['massessname'];
	// set phaseflip on by default
	$phasecheck = ($_POST['ctfcorrect']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	$boxfilescheck = ($_POST['boxfiles']=='on') ? 'CHECKED' : '';
	$inspectcheck = ($_POST['inspected']=='off') ? '' : 'CHECKED';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'CHECKED' : '';

	$binval = ($_POST['bin']) ? $_POST['bin'] : '1';
	$partlimit = $_POST['partlimit'];
	$lpval = ($_POST['lp']) ? $_POST['lp'] : '';
	$hpval = ($_POST['hp']) ? $_POST['hp'] : '';
	// ice check params
	$iceval = ($_POST['icecheck']=='on') ? $_POST['ice'] : '0.8';
	$icecheck = ($_POST['icecheck']=='on') ? 'CHECKED' : '';
	$icedisable = ($_POST['icecheck']=='on') ? '' : 'DISABLED';
	// ace check params
	$acecheck = ($_POST['acecheck']=='on') ? 'CHECKED' : '';
	$ctffindcheck = ($_POST['ctffindonly'])=='on' ? 'CHECKED' : '';
	$acedisable = ($_POST['acecheck']=='on') ? '' : 'DISABLED';
	$aceval = ($_POST['acecheck']=='on') ? $_POST['ace'] : '0.8';
	// correlation check params
	$selexminval = ($_POST['selexcheck']=='on') ? $_POST['correlationmin'] : '0.5';
	$selexmaxval = ($_POST['selexcheck']=='on') ? $_POST['correlationmax'] : '1.0';
	$selexcheck = ($_POST['selexcheck']=='on') ? 'CHECKED' : '';
	$selexdisable = ($_POST['selexcheck']=='on') ? '' : 'DISABLED';
	// density check (checked by default)
	$invcheck = ($_POST['density']=='invert' || !$_POST['process']) ? 'CHECKED' : '';
	// normalization check (checked by default)
	$normcheck = ($_POST['normalize']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	$xmippnormcheck = ($_POST['xmippnormcheck']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	$xmippdisable = ($xmippnormcheck=='CHECKED') ? '' : 'DISABLED';
	$xmippnormval = ($_POST['xmippnormval']) ? $_POST['xmippnormval'] : '4.5';
	$overridecheck = ($_POST['override']=='on') ? 'CHECKED' : '';
	
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

	echo "<input type='checkbox' name='density' $invcheck value='invert'>\n";
	echo docpop('stackinv','Invert image density');
	echo "<br/>\n";

	echo "<input type='checkbox' name='normalize' $normcheck>\n";
	echo docpop('stacknorm','Normalize Stack Particles');
	echo "<br/>\n";

	echo "<input type='checkbox' name='xmippnormcheck' onclick='enablexmipp(this)' $xmippnormcheck>\n";
	echo docpop('xmippstacknorm','XMIPP normalize to sigma:');
	echo "<input type='text' name='xmippnormval' $xmippdisable value='$xmippnormval' size='4'>";
	echo "<br/>\n";

	if ($ctfdata) {
		echo"<input type='checkbox' name='ctfcorrect' onclick='enablectftype(this)' $phasecheck>\n";
		echo docpop('ctfcorrect','Ctf Correct Particle Images');
		echo "<br/>\n";

		echo "Ctf Correct Method:\n";
		echo "&nbsp;&nbsp;<select name='ctfcorrecttype' ";
		if (!$phasecheck) echo " disabled";
		echo ">\n";
		echo "<option value='ace2image'>Ace 2 WeinerFilter Whole Image (default)</option>\n";
		echo "<option value='emanpart'>EMAN PhaseFlip by Stack</option>\n";
		echo "<option value='emanimage'>EMAN PhaseFlip Whole Image</option>\n";
		echo "<option value='emantilt'>EMAN PhaseFlip by Tilt Location</option>\n";
		echo "</select>\n";
		echo "<br/>\n";
	}

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

	//echo "</td></tr></table>";
	echo "</td><td class='tablebg'>";
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
			$totparts=commafy($partstats['totparticles']);
			echo "<option value='$partrunid'";
			// select previously set part on resubmit
			if ($partrunval==$partrunid) {
				echo " selected";
			}
			echo">$runname ($totparts parts)</option>\n";
		}
		echo "</select>\n";

		// add particle label page
		$particlelabels = $particle->getParticleLabels($partrunval);
		if (!empty($particlelabels)) {
			echo "<br/>\n";
			echo"<input type='checkbox' name='labelcheck' onclick='enablelabel()' $labelcheck >\n";
			echo docpop('stackparticlelabels','Particle labels:');
			echo "<select name='partlabel' $labeldisable >\n";
			foreach ($particlelabels as $row) {
				$label=$row['label'];
				$sel = (trim($_POST['partlabel'])==$label) ? 'selected' : '';
				echo '<option value="'.$label.'" '.$sel.' >'.$label."</option>\n";
			}
		} else {
			echo "<input type='hidden' name='labelcheck' value='off' >";
			echo "<input type='hidden' name='partlabel' value='' >";
		}
		echo "</select>\n";
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


	// Determine best box size...

	if (!$_POST['boxsize']) {
		$partrundata = $particle->getSelectionParams($partrunval);
		$imgid = $particle->getImgIdFromSelectionRun($partrunval);
		$partdiam = $partrundata[0]['diam'];
		$pixelsize = $particle->getPixelSizeFromImgId($imgid)*1e10;
		//echo "Diameter: $partdiam &Aring;<br/>\n";
		//echo "Image id: $imgid<br/>\n";
		//echo "Pixel size: $pixelsize &Aring;<br/>\n";
		$pixdiam = (int) ($partdiam/$pixelsize);
		//echo "Pixel diam: $pixdiam pixels<br/>\n";
		$boxdiam = (int) ($partdiam/$pixelsize*1.4);
		//echo "Box diam: $boxdiam pixels<br/>\n";
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

	echo "<b>Filter Values:</b><br/>";

	echo "<input type='text' name='lp' value='$lpval' size='4'>\n";
	echo docpop('lpstackval', 'Low Pass');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br/>\n";

	echo "<input type='text' name='hp' value='$hpval' size='4'>\n";
	echo docpop('hpstackval', 'High Pass');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br/>\n";

	echo "<input type='text' name='bin' value='$binval' size='4'>\n";
	echo docpop('stackbin','Binning');
	echo "<br/>\n";
	echo "<br/>\n";

	// commented out for now, since not implemented
//		<input type='checkbox' name='icecheck' onclick='enableice(this)' $icecheck>
//		Ice Thickness Cutoff<br />
//		Use Ice Thinner Than:<input type='text' name='ice' $icedisable value='$iceval' size='4'>
//		(between 0.0 - 1.0)\n";

	if ($ctfdata) {
		// give option of only using ctffind values
		if ($ctffindids) {
			echo "<input type='checkbox' name='ctffindonly' $ctffindcheck>\n";
			echo docpop('ctffindonly','Only use CTFFIND values');
			echo "<br/>\n";
		}
		echo"<input type='checkbox' name='acecheck' onclick='enableace(this)' $acecheck>\n";
		echo docpop('aceconf','CTF Confidence Cutoff');
		echo "<br />\n";
		echo "Use Values Above:<input type='text' name='ace' $acedisable value='$aceval' size='4'>
		(between 0.0 - 1.0)\n";
		echo "<br/>\n";
		echo "<br/>\n";
	}


	echo"<input type='checkbox' name='selexcheck' onclick='enableselex(this)' $selexcheck>\n";
	echo docpop('partcutoff','Particle Correlation Cutoff');
	echo "<br />\n";
	echo "Use Values Above:<input type='text' name='correlationmin' $selexdisable value='$selexminval' size='4'><br/>\n";
	echo "Use Values Below:<input type='text' name='correlationmax' $selexdisable value='$selexmaxval' size='4'><br/>\n";
	echo "<br/>\n";

	echo "<b>Defocal pairs:</b>\n";
	echo "<br/>\n";
	echo "<input type='checkbox' name='defocpair' $defocpair>\n";
	echo docpop('stackdfpair','Use defocal pairs');
	echo "<br/>\n";
	echo "<br/>\n";

	//if there is CTF data, show min & max defocus range
	if ($ctfdata) {
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
		$minval = ereg_replace("E","e",round($minval,8));
		$maxval = ereg_replace("E","e",round($maxval,8));
		$mindbval = ereg_replace("E","e",round($min,8));
		$maxdbval = ereg_replace("E","e",round($max,8));
		echo"<b>Defocus Limits</b><br />
				<input type='text' name='dfmin' value='$minval' size='25'>
				<input type='hidden' name='dbmin' value='$mindbval'>
			Minimum<br/>
				<input type='text' name='dfmax' value='$maxval' size='25'>
				<input type='hidden' name='dbmax' value='$maxdbval'>
			Maximum\n";
		echo "<br/>\n";
		echo "<br/>\n";
	}


	echo docpop('stacklim','Limit # of particles to: ');
	echo "<input type='text' name='partlimit' value='$partlimit' size='8'>\n";
	echo "<br/>\n";
	echo "<input type='checkbox' name='boxfiles' $boxfilescheck>\n";
	echo docpop('boxfiles','Only create EMAN boxfiles');
	echo "<br />\n";
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
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$single=$_POST['single'];
	//make sure a session was selected
	$description = $_POST['description'];
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

	$invert = ($_POST['density']=='invert') ? 'yes' : 'no';
	$normalize = ($_POST['normalize']=='on') ? 'yes' : 'no';
	$ctfcorrect = ($_POST['ctfcorrect']=='on') ? 'ctfcorrect' : '';
	$ctfcorrecttype = $_POST['ctfcorrecttype'];
	$stig = ($_POST['stig']=='on') ? 'stig' : '';
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$defocpair = ($_POST['defocpair']=="on") ? "1" : "0";
	$boxfiles = ($_POST['boxfiles']);
	$ctffindonly = ($_POST['ctffindonly'])=='on' ? True : False;

	// xmipp normalization
	// ace cutoff
	if ($_POST['xmippnormcheck']=='on') {
		$xmippnorm=$_POST['xmippnormval'];
		if ($xmippnorm <= 0 || !$xmippnorm) createMakestackForm("<b>ERROR:</b> Xmipp sigma must be greater than 0" );
	}

	// set image inspection selection
	$norejects=$inspected=0;
	if ($_POST['checkimage']=="Non-rejected") {
		$norejects=1;
	} elseif ($_POST['checkimage']=="Best") {
		$norejects=1;
		$inspected=1;
	}
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

	// ace cutoff
	if ($_POST['acecheck']=='on') {
		$ace=$_POST['ace'];
		if ($ace > 1 || $ace < 0 || !$ace) createMakestackForm("<b>ERROR:</b> Ace cutoff must be between 0 & 1");
	}

	// correlation cutoff
	if ($_POST['selexcheck']=='on') {
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

	$command = "makestack2.py"." ";
	$command.="--single=$single ";
	if ($partrunid)
		$command.="--selectionid=$partrunid ";
	elseif ($fromstackid)
		$command.="--fromstackid=$fromstackid ";
	if ($lp) $command.="--lowpass=$lp ";
	if ($hp) $command.="--highpass=$hp ";
	if ($invert == "yes") $command.="--invert ";
	if ($invert == "no") $command.="--no-invert ";
	if ($normalize == "yes") $command.="--normalized ";
	if ($xmippnorm) $command.="--xmipp-normalize=$xmippnorm ";
	if ($ctfcorrect) { 
		$command.="--phaseflip --flip-type=$ctfcorrecttype ";
	}
	if ($massessname) $command.="--maskassess=$massessname ";
	$command.="--boxsize=$boxsize ";
	if ($bin > 1) $command.="--bin=$bin ";
	if ($ace) $command.="--acecutoff=$ace ";
	if ($defocpair) $command.="--defocpair ";
	if ($correlationmin) $command.="--mincc=$correlationmin ";
	if ($correlationmax) $command.="--maxcc=$correlationmax ";
	if ($dfmin) $command.="--mindef=$dfmin ";
	if ($dfmax) $command.="--maxdef=$dfmax ";
	if ($_POST['fileformat']=='spider') $command.="--spider ";
	if ($partlimit != "none") $command.="--partlimit=$partlimit ";
	if ($boxfiles == 'on') $command.="--boxfiles ";
	$command.="--description=\"$description\" ";
	if (!empty($partlabel)) $command.="--label=\"$partlabel\" ";
	if ($ctffindonly) $command.="--ctfmethod=ctffind ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createMakestackForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	// submit job to cluster
	if ($_POST['process']=="Make Stack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createMakestackForm("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'makestack2',$testimage);
		// if errors:
		if ($sub) createMakestackForm("<b>ERROR:</b> $sub");
		exit;
	}

	processing_header("Makestack Run","Makestack Params");

	echo appionRef();

	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>Makestack Command:</b><br />
	$command
	</td></tr>";
	echo appionLoopSummaryTable();
	echo"
	<tr><td>stack name</td><td>$single</td></tr>
	<tr><td>selection Id</td><td>$partrunid</td></tr>
	<tr><td>particle label</td><td>$partlabel</td></tr>
	<tr><td>invert</td><td>$invert</td></tr>
	<tr><td>normalize</td><td>$normalize</td></tr>
	<tr><td>xmipp-normalize</td><td>$xmippnormalize</td></tr>
	<tr><td>ctf correct</td><td>$ctfcorrect</td></tr>
	<tr><td>ctf correct type</td><td>$ctfcorrecttype</td></tr>
	<tr><td>mask assessment</td><td>$massessname</td></tr>
	<tr><td>box size</td><td>$boxsize</td></tr>
	<tr><td>binning</td><td>$bin</td></tr>
	<tr><td>ace cutoff</td><td>$ace</td></tr>
	<tr><td>correlationmin cutoff</td><td>$correlationmin</td></tr>
	<tr><td>correlationmax cutoff</td><td>$correlationmax</td></tr>
	<tr><td>minimum defocus</td><td>$dfmin</td></tr>
	<tr><td>maximum defocus</td><td>$dfmax</td></tr>
	<tr><td>particle limit</td><td>$partlimit</td></tr>
	<tr><td>spider</td><td>$_POST[fileformat]</td></tr>";

	echo "</table>\n";
	processing_footer(True,True);
}
?>
