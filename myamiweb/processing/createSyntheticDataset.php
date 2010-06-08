<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
  
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	createSyntheticDataset();
}
// CREATE FORM PAGE
elseif ($_POST['submitModel']) {
	syntheticDatasetForm();
}
else chooseModel();

	

function chooseModel($extra=False) {
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
	
	$projectId=getProjectId();
		
	if (is_numeric($projectId)) {
		$particle = new particledata();
		// get initial models associated with project
		$models=$particle->getModelsFromProject($projectId);
	}

	$javafunc="<script src='../js/viewer.js'></script>\n";

	processing_header("Choose Model","Choose Model for Projecting Synthetic Dataset",$javafunc);

	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";
	
	// show initial models
	echo "<P><B>Model:</B><br><A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><br>\n";
	echo"<P><input type='SUBMIT' NAME='submitModel' VALUE='Project this Model'><br>\n";
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
			$sym['symmetry'] = strtolower($sym['symmetry']);
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
			echo "<input type='BUTTON' NAME='rescale' VALUE='Rescale/Resize this model' onclick=\"parent.location='uploadmodel.php?expId=$expId&rescale=TRUE&modelid=$model[DEF_id]'\"><br>\n";
			foreach ($pngfiles as $snapshot) {
				$snapfile = $model['path'].'/'.$snapshot;
				echo "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><img src='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'>\n";
			}
			echo "</td>\n";
			echo "</tr>\n";
			echo"<tr><TD COLSPAN=2>$model[description]</td></tr>\n";
			echo"<tr><TD COLSPAN=2>$model[path]/$model[name]</td></tr>\n";
			echo"<tr><td>pixel size:</td><td>$model[pixelsize]</td></tr>\n";
			echo"<tr><td>box size:</td><td>$model[boxsize]</td></tr>\n";
			echo"<tr><td>symmetry:</td><td>$sym[symmetry]</td></tr>\n";
			echo"<tr><td>resolution:</td><td>$model[resolution]</td></tr>\n";
			echo "</table>\n";
			echo "<P>\n";
		}
		echo"<P><input type='SUBMIT' NAME='submitModel' VALUE='Project this Model'></FORM>\n";
	}
	else echo "No initial models in database";
	processing_footer();
	exit;
}
	
	
	
	

function syntheticDatasetForm($extra=false, $title='Synthetic Dataset Creation', $heading='Synthetic Dataset Creation From 3d Model', $modelId=False) {
	// check if coming directly from a session
   	$expId = $_GET['expId'];

	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=getProjectId();
	
	
	// javascript functions that go into form
	$javafunctions="<script type='text/javascript' src='../js/viewer.js'></script>
	<script type='text/javascript'>
	
	function enablerandomdef(){
		if (document.viewerform.randomdef.checked){
			document.viewerform.defstd.disabled=false;
			document.viewerform.defstd.value='0.4';
		} else {
			document.viewerform.defstd.disabled=true;
			document.viewerform.defstd.value='0.4';
		}
	}
	
	function enablecorrect(){
		if (document.viewerform.ace2correct.checked){
			document.viewerform.correction.disabled=false;
		} else {
			document.viewerform.correction.disabled=true;
		}
		checkcorrection()
	}

	function checkcorrection() {
		en_stdev=(document.viewerform.ace2correct.checked) ? true : false
		if (o=document.viewerform.correction) {
			if (o_r=document.viewerform.randcor_std) {
			selcorrect=o.options[o.selectedIndex].value
				if (selcorrect=='perturb' && en_stdev) {
					o_r.disabled=false
					o_r.value='0.05'
				} else {
					o_r.disabled=true
				}
			}
		}
	}

	function checkprojection() {
		if (o=document.viewerform.projection) {
			if ((o_r1=document.viewerform.projinc) && (o_r2=document.viewerform.projstdev)) {
			projtype=o.options[o.selectedIndex].value
				if (projtype=='even') {
					o_r1.disabled=false
					o_r1.value='5'
					o_r2.disabled=true
				} else {
					o_r1.disabled=true
					o_r2.disabled=false
					o_r2.value='7'
				}
			}
		}
	}
	
	</script>\n";

	$javafunctions .= writeJavaPopupFunctions('appion');	

	processing_header("Synthetic Dataset Creation","Synthetic Dataset Creation from Input Model",$javafunctions,True, 'enablecorrect()');

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<input type='HIDDEN' NAME='lastSessionId' value='$sessionId'>\n"; // what is this?

	$sessiondata=getSessionList($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("data..","data00", $sessionpath);
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","syntheticData/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	
	// Set any existing parameters in form
	$particle=new particleData;
	$datasetruns = 0;
	$sessionpathval = ($_POST['rundir']) ? $_POST['rundir'] : $sessionpath;
	while (file_exists($sessionpathval.'dataset'.($datasetruns+1))) {
		$datasetruns += 1;
	}
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'dataset'.($datasetruns+1);
	$description = $_POST['description'];
	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	
	// set other default params
	$projcount = ($_POST['projcount']) ? $_POST['projcount'] : 4096;
	$projinc = ($_POST['projinc']) ? $_POST['projinc'] : 5;
	$projstdev = ($_POST['projstdev']) ? $_POST['projstdev'] : 7;
	$shiftrad = ($_POST['shiftrad']) ? $_POST['shiftrad'] : 5;
	$rotang = ($_POST['rotang']) ? $_POST['rotang'] : 360;
	$flip = ($_POST['flip']=='on' || !$_POST['process']) ? 'checked' : '';
	$snr1 = ($_POST['snr1']) ? $_POST['snr1'] : 1.8;
	$snrtot = ($_POST['snrtot']) ? $_POST['snrtot'] : 0.05;
	$df1 = ($_POST['df1']) ? $_POST['df1'] : -1.5;
	$df2 = ($_POST['df2']) ? $_POST['df2'] : -1.5;
	$astigmatism = ($_POST['astigmatism']) ? $_POST['astigmatism'] : 0;
	$lpfilt = ($_POST['lpfilt']) ? $_POST['lpfilt'] : 5;
	$hpfilt = ($_POST['hpfilt']) ? $_POST['hpfilt'] : 600;

	// default params for javascript
	$randomdef = ($_POST['randomdef']=='on') ? 'CHECKED' : '';
	$defstd = ($_POST['randomdef']=='on') ? $_POST['defstd'] : '';
	$ace2correct = ($_POST['ace2correct']=='on') ? 'CHECKED' : '';
	$randcor_std = ($_POST['randomdef']=='on') ? $_POST['randcor_std'] : '';
	$randomdefdisable = ($_POST['randomdef']=='on') ? '' : 'DISABLED';
	$correctiondisable = ($_POST['correction']) ? $_POST['correction'] : "DISABLED";
	$randcordisable = ($_POST['randcor_std']) ? $_POST['randcor_std'] : "DISABLED";
	$projstdevdisabled = ($_POST['projection']=='even' && !$extra) ? $_POST['projstdev'] : "DISABLED";

	// get model data
	
	if ($modelId) $modeldata = $particle->getInitModelInfo($modelId);
	else {
		$model = $_POST['model'];
		$modellist = explode('|--|', $model);
		$modeldata = $particle->getInitModelInfo($modellist['0']);
	}

	$pngfiles=array();
	$modeldir= opendir($modeldata['path']);
	while ($f = readdir($modeldir)) {
		if (eregi($modeldata['name'].'.*\.png$',$f)) $pngfiles[] = $f;
	}
	sort($pngfiles);
	$snapshot1 = $pngfiles[0];
	$snapfile1 = $modeldata['path'].'/'.$snapshot1;
	$snapshot2 = $pngfiles[1];
	$snapfile2 = $modeldata['path'].'/'.$snapshot2;
	$snapshot3 = $pngfiles[2];
	$snapfile3 = $modeldata['path'].'/'.$snapshot3;

	// setup basic run parameters
	echo "<TABLE border='0' cellpadding='5'>\n";
	echo "<TR><TD valign='top'>\n";
//	echo openRoundBorder();
	echo docpop('runid','<b>Synthetic Dataset Runname:</b>');
	echo "<br>\n";
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br>\n";
	echo "<br>\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br>\n";
	echo "<input type='text' name='rundir' value='$sessionpathval' size='38'>\n";
	echo "<br>\n";
	echo "<br>\n";
	echo docpop('descr','<b>Description:</b>');
	echo "<br>\n";
	echo "<textarea name='description' rows='3' cols='36'>$description</textarea>\n";
	echo "<br>\n";
	echo "<br>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "</TD></TR>\n";
	echo "</TABLE>";
	echo "<br>\n";
//	echo closeRoundBorder();

	// echo models
	echo "<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
		<tr>
		<td VALIGN='TOP' WIDTH='280'>";
	srand(time());
	if ((rand()%2) < 3) {
		echo "<center><img src='loadimg.php?s=80&filename=$snapfile1' WIDTH='90'>
			<img src='loadimg.php?s=80&filename=$snapfile2' WIDTH='90'>
			<img src='loadimg.php?s=80&filename=$snapfile3' WIDTH='90'></center>";
	}
	echo "</td></tr>";
	echo "</table>\n";
	echo "<br>\n";

	echo	"<br><br>
		<TABLE WIDTH='310' BORDER='.1'>
		<TR><TD COLSPAN='2'>
			<B>Model Params:</B><br>
		</TD></tr>
		<TR><td>Model ID</TD><td>$modeldata[DEF_id]</TD></tr>
		<TR><td>Resolution</TD><td>$modeldata[resolution]</TD></tr>
		<TR><td>Pixelsize</TD><td>$modeldata[pixelsize]</TD></tr>
		<TR><td>Boxsize</TD><td>$modeldata[boxsize]</TD></tr>
		</TABLE><br><br>\n";




	

	
	echo "<td class='tablebg'>\n";
	echo "<b>Projection Parameters:</b><br />\n";
	echo "<input type='text' NAME='projcount' value='$projcount' size='4'>\n";
	echo docpop('projcount','Number of Projections');
	echo "<font size=-2><i>(particles in stack)</i></font>\n";
	echo "<br />\n";

	echo docpop('projtype','Projection Type: ');
	echo "<select name='projection' onchange='checkprojection()'>";
	echo "<option value='even'>Evenly distributed</option>";
	echo "<option value='preferred'>Axial preferrence</option>";
	echo "</select><br>";

	echo "<input type='text' name='projinc' value='$projinc' size='4'>\n";
	echo docpop('projinc',' Angular increment of projections');
	echo " <font size=-2><i>(degrees)</i></font>\n";
	echo "<br />\n";
	
	echo "<input type='text' name='projstdev' $projstdevdisabled value='$projstdev' size='4'>\n";
	echo docpop('projstdev',' Standard deviation about projection axis');
	echo " <font size=-2><i>(degrees)</i></font>\n";
	echo "<br />\n";
	
	echo "<input type='text' name='shiftrad' value='$shiftrad' size='4'>\n";
	echo docpop('shiftrad',' Radius of random shift');
	echo " <font size=-2><i>(pixels)</i></font>\n";
	echo "<br />\n";
	
	echo "<input type='text' name='rotang' value='$rotang' size='4'>\n";
	echo docpop('rotang',' Degree of random rotation');
	echo " <font size=-2><i>(degree)</i></font>\n";
	echo "<br />\n";
	
	echo "<input type='checkbox' name='flip' $flip";
	echo docpop('flip', 'Randomly flip particles');
	echo "<br><br>\n";
	
	
	echo "<b>Signal to Noise Ratio:</b><br />\n";
	echo "<input type='text' name='snr1' value='$snr1' size='4'>\n";
	echo docpop('snr1',' SNR1 (beam damage, shot noise, etc.) ');
	echo " <font size=-2><i>(ratio)</i></font>\n";
	echo "<br />\n";
	
	echo "<input type='text' name='snrtot' value='$snrtot' size='4'>\n";
	echo docpop('snrtot',' SNR Total (digitization) ');
	echo " <font size=-2><i>(ratio)</i></font>\n";
	echo "<br><br>\n";
	
	
	echo "<b>CTF Application:</b><br />\n";
	echo "<input type='text' name='df1' value='$df1' size='4'>\n";
	echo docpop('df1',' Defocus (x)');
	echo " <font size=-2><i>(microns)</i></font>\n";
	echo "<br>\n";
	
	echo "<input type='text' name='df2' value='$df2' size='4'>\n";
	echo docpop('df2',' Defocus (y)');
	echo " <font size=-2><i>(microns)</i></font>\n";
	echo "<br>\n";
	
	echo "<input type='text' name='astigmatism' value='$astigmatism' size='4'>\n";
	echo docpop('astigmatism',' Astigmatism angle');
	echo " <font size=-2><i>(radians)</i></font>\n";
	echo "<br>\n";
	
	echo "<input type='checkbox' name='randomdef' onclick='enablerandomdef(this)' $randomdef>\n";
	echo docpop('randomdef',' Randomize defocus values');
	echo "<br>\n";
	echo docpop('randdefstd','Standard deviation of application: ');
	echo " $nbsp <input type='text' name='defstd' $randomdefdisable value='$defstd' size='4'>";
	echo " <font size=-2><i>(microns)</i></font>\n";
	echo "<br><br>\n";
	
	echo "<b>CTF Correction:</b><br />\n";
	echo "<input type='checkbox' name='ace2correct' onclick='enablecorrect(this)' $ace2correct>\n";
	echo docpop('ace2correct',' Correct CTF');
	echo "<br>\n";
	
	echo docpop('correctiontype','Correction Type: ');
	echo "<select name='correction' onchange='checkcorrection()' $correctiondisable>";
	echo "<option value='applied'>Applied CTF</option>";
#	echo "<option value='ace2estimate'>Use ACE2 Estimate</option>"; 
	echo "<option value='perturb'>Perturb Applied CTF</option>";
	echo "</select><br>";
 
	echo docpop('ace2correct_std','Standard deviation of correction: ');
	echo " $nbsp <input type='text' name='randcor_std' $randcordisable value='$randcor_std' size='4'>\n";
	echo " <font size=-2><i>(microns)</i></font>\n";
	echo "<br><br>\n";
	
	echo "<b>Final Stack Filtering:</b><br />\n";
	echo "<input type='text' name='lpfilt' value='$lpfilt' size='4'>\n";
	echo docpop('lpfilt',' Low-pass filter');
	echo " <font size=-2><i>(&Aring;ngstroms)</i></font>\n";
	echo "<br>\n";

	echo "<input type='text' name='hpfilt' value='$hpfilt' size='4'>\n";
	echo docpop('hpfilt',' High-pass filter');
	echo " <font size=-2><i>(&Aring;ngstroms)</i></font>\n";
	echo "<br>\n";

        echo "<input type='checkbox' name='norm' \n";
        echo docpop('stacknorm',' Normalize particles');
        echo "<br>\n";	
	
	
	
	
//	echo docpop('ace2estimate','Use ACE2 to Estimate & Correct: ');
//	echo "<input type='radio' name='correction' $randcordisable value='1' ><br>\n";
//	echo docpop('ace2correct_rand','Wiggle correction values: ');
//	echo "<input type='radio' name='correction' $randcordisable value='2' ><br>\n";



	echo "<input type='HIDDEN' NAME='modelId' value='$modeldata[DEF_id]'>\n";
	echo "<input type='HIDDEN' NAME='pixelsize' value='$modeldata[pixelsize]'>\n";
	echo "<input type='HIDDEN' NAME='boxsize' value='$modeldata[boxsize]'>\n";
	
	echo "</td>
	</tr>
	<tr>
		<td COLSPAN='2' ALIGN='center'><br>";
	echo getSubmitForm("Create Synthetic Dataset");
	echo "
		</td>
	</tr>
	</form>
	</table>\n";
	processing_footer();
	exit;
}

function createSyntheticDataset() {
	// get any passed parameters
	$projectId = getProjectId();
	$expId = $_GET['expId'];
	$rundir = $_POST['rundir'];
	$runname = $_POST['runname'];

	$commit = ($_POST['commit']=="on") ? 'commit' : '';

	$modelId = $_POST['modelId'];
	$pixelsize = $_POST['pixelsize'];
	$boxsize = $_POST['boxsize'];
	$projcount = $_POST['projcount'];
	$projstdev = $_POST['projstdev'];
	$projinc = $_POST['projinc'];
	$shiftrad = $_POST['shiftrad'];
	$rotang = $_POST['rotang'];
	$flip = $_POST['flip'];
	$snr1 = $_POST['snr1'];
	$snrtot = $_POST['snrtot'];
	$df1 = $_POST['df1'];
	$df2 = $_POST['df2'];
	$astigmatism = $_POST['astigmatism'];
	$lpfilt = $_POST['lpfilt'];
	$hpfilt = $_POST['hpfilt'];
	$norm = $_POST['norm'];

	// default params for javascript
	$randomdef = ($_POST['randomdef']=='on') ? 'randomdef' : '';
	$defstd = $_POST['defstd'];
	$ace2correct = ($_POST['ace2correct']=='on') ? 'ace2correct' : '';
	$randcor_std = $_POST['randcor_std'];
	$projection = $_POST['projection'];
	$correction = $_POST['correction'];

	//make sure default variables are selected
	$description=$_POST['description'];
	if (!$description) syntheticDatasetForm("<B>ERROR:</B> Enter a Description", $title, $heading, $modelId);
	if (!$runname) syntheticDatasetForm("<B>ERROR:</B> Enter run name", $title, $heading, $modelId);
	if (!$rundir) syntheticDatasetForm("<B>ERROR:</B> Enter output directory", $title, $heading, $modelId);
	if (!$modelId) chooseModel("<B>ERROR:</B> Please Choose a Model");
	if (!$projcount) syntheticDatasetForm("<B>ERROR:</B> Specify the number of projections (particles)", $title, $heading, $modelId);
	if (!$pixelsize) syntheticDatasetForm("<B>ERROR:</B> model does not have an associated pixelsize", $title, $heading, $modelId);
	if (!$boxsize) syntheticDatasetForm("<B>ERROR:</B> model does not have an associated boxsize", $title, $heading, $modelId);

	// make sure defocus values are positive
	if ($df1 > 0 || $df2 > 0) syntheticDatasetForm("<B>ERROR:</B> Make sure that the applied defocus values are negative", $title, $heading, $modelId);
	
	
	// other stuff
	if ($rotang > 360 || $rotang < 0) syntheticDatasetForm("<B>ERROR:</B> Enter rotation angle between 0 and 360", $title, $heading, $modelId);
	if ($defstd > ($df1 / -1.5) || $defstd > ($df2 / -1.5)) {
		syntheticDatasetForm("<B>ERROR:</B> STD of applied defocus too high. Big risk of applying positive defocus values", $title, $heading, $modelId);
	}
	if ($randcor_std > ($df1 / -2) || $randcor_std > ($df2 / -2)) {
		syntheticDatasetForm("<B>ERROR:</B> STD of defocus perturbation too high. Don't use correction at all", $title, $heading, $modelId);
	}
	if ($projection == "even" && !$projinc) {
		syntheticDatasetForm("<B>ERROR:</B> Please enter a projection angular increment", $title, $heading, $modelId);
	}
	if ($projection == "preferred" && !$projstdev) {
		syntheticDatasetForm("<B>ERROR:</B> Please enter a projection standard deviation", $title, $heading, $modelId);
	}
	if ($correction == "perturb" && !$randcor_std) {
		syntheticDatasetForm("<B>ERROR:</B> Please enter a standard deviation which will be used to perturb CTF correction values", $title, $heading, $modelId);
	}
		

	// create actual command that will run python script
	$command ="createSyntheticDataset.py ";
	$command.="--projectid=$projectId ";
	$command.="--rundir=$rundir ";
	$command.="--runname=$runname ";
	$command.="--description=\"$description\" ";
	$command.="--modelid=$modelId ";
	if ($pixelsize) $command.="--apix=$pixelsize ";
	if ($boxsize) $command.="--boxsize=$boxsize ";
	$command.="--projcount=$projcount ";
	if ($projection == "preferred") $command.="--preforient --projstdev=$projstdev ";
	elseif ($projection == "even") $command.="--projinc=$projinc ";
	if ($shiftrad) $command.="--shiftrad=$shiftrad ";
	if ($rotang) $command.="--rotang=$rotang ";
	if ($flip) $command.="--flip ";
	else $command.="--no-flip ";
	if ($snr1) $command.="--snr1=$snr1 ";
	if ($snrtot) $command.="--snrtot=$snrtot ";
	if ($df1) $command.="--df1=$df1 ";
	if ($df2) $command.="--df2=$df2 ";
	if ($astigmatism) $command.="--astigmatism=$astigmatism ";
	if ($randomdef) {
		$command.="--randomdef ";
		if ($defstd) $command.="--randomdef-std=$defstd ";
	}
	if ($correction=="applied") {
		$command.="--ace2correct ";
	}
#	elseif ($correction=="ace2estimate") {
#		$command.="--ace2correct ";
#		$command.="--ace2estimate ";
#	}
	elseif ($correction=="perturb") {
		$command.="--ace2correct-rand ";
		if ($randcor_std) $command.="--ace2correct-std=$randcor_std ";
	}
	if ($lpfilt) $command.="--lpfilt=$lpfilt ";
	if ($hpfilt) $command.="--hpfilt=$hpfilt ";
	if ($norm) $command.="--norm ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";



	// submit job to cluster
	if ($_POST['process']=="Create Synthetic Dataset") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password))
			syntheticDatasetForm("<B>ERROR:</B> Enter a user name and password", $title, $heading, $modelId);

		$sub = submitAppionJob($command,$rundir,$runname,$expId,"syntheticData");
		// if errors:
		if ($sub)
			syntheticDatasetForm("<b>ERROR:</b> $sub", $title, $heading, $modelId);
		exit;
	} else {
		processing_header("Synthetic Dataset Run","Selected Params");

		echo"
			<TABLE WIDTH='600' BORDER='1'>
			<TR><TD COLSPAN='2'>
			<B>Alignment Command:</B><br>
			$command
			</TD></tr>
			<TR><td>rundir</TD><td>$rundir</TD></tr>
			<TR><td>runname</TD><td>$runname</TD></tr>
			<TR><td>model Id</TD><td>$modelId</TD></tr>
			<TR><td>Pixelsize</TD><td>$pixelsize</TD></tr>
			<TR><td>Boxsize</TD><td>$boxsize</TD></tr>
			<TR><td># of Particles</TD><td>$projcount</TD></tr>";
		if ($projection == "even") echo "<TR><td>Angular increment of projections</TD><td>$projinc</TD></tr>";
		elseif ($projection == "preferred") echo "<TR><td>STD about projection axis</TD><td>$projstdev</TD></tr>";
		echo"
			<TR><td>Radius of random shift</TD><td>$shiftrad</TD></tr>
			<TR><td>Angle of random rotation</TD><td>$rotang</TD></tr>";
		if ($flip) echo "<TR><td>Randomly Flip</TD><td>YES</TD></tr>";
		else echo "<TR><td>Randomly Flip</TD><td><b>NO</b></TD></tr>";
		echo "
			<TR><td>1st Signal to Noise Ratio</TD><td>$snr1</TD></tr>
			<TR><td>Final Signal to Noise Ratio</TD><td>$snrtot</TD></tr>
			<TR><td>Defocus (x)</TD><td>$df1</TD></tr>
			<TR><td>Defocus (y)</TD><td>$df2</TD></tr>
			<TR><td>Angle of Astigmatism</TD><td>$astigmatism</TD></tr>";
		if ($randomdef) echo "<TR><td>Randomly Apply Defoci</TD><td>YES</TD></tr>
				<TR><td>With a Standard Deviation</TD><td>$defstd</TD></tr>";
		else echo "<TR><td>Randomly Apply Defoci</TD><td><b>NO</b></TD></tr>";
		if ($ace2correct) {
			echo "<TR><td>Correct Applied Defoci</TD><td>YES</TD></tr>
			      <TR><td>With this Method</TD><td>$correction</TD></tr>";
			if ($correction=='perturb') {
				echo "<TR><td>With this Standard Deviation</TD><td>$randcor_std</TD></tr>";
			}
		}
		else echo "<TR><td>Correct Applied Defoci</TD><td><b>NO</b></TD></tr>";
		echo "
			<TR><td>Low-Pass filter (&Aring;ngstroms)</TD><td>$lpfilt</TD></tr>
			<TR><td>High-Pass filter (&Aring;ngstroms)</TD><td>$hpfilt</TD></tr>

		</table>\n";
		processing_footer();
	}
}


?>
