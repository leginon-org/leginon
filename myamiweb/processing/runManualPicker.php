<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *  Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";
  
/**
 * Handle Particle pick Label
 **/
if (count($_POST) == 0) unset($_SESSION['picklabels']);
if ($_POST['addpicklabel']) {
	// --- check id label exists --- //
	$picklabel = trim($_POST['picklabel']);
	$picklabels = $_SESSION['picklabels'];
	$editrunname = $_POST['editrunname'];
	if (empty($_POST['editrunlabels']) && ($picklabel==$editrunname))
		createManualPickerForm('Unlabeled Old Particle Pick is automatically labeled by its runname');
	else {
		$reserved_labels = array('fromtrace','_trace');
		foreach ($reserved_labels as $rlabel)
		if ($picklabel==$rlabel)
			createManualPickerForm('"'.$rlabel.'" is a reserved label. Give another name');
		if (!in_array($picklabel, $picklabels) && count($picklabels)<8) {
			$_SESSION['picklabels'][]=$picklabel;
		}
	}
}
if ($_POST['delpicklabel']) {
	foreach ((array)$_POST as $k=>$v) {
		if (preg_match('%^[0-9]{1,}i%', $k)) {
			$index = (int)$k;
			unset($_SESSION['picklabels'][$index]);
		}
	}
}

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
  runManualPicker();
	// --- clear labels when data submitted --- //
	unset($_SESSION['picklabels']);
}
// CREATE FORM PAGE
else {
  createManualPickerForm();
}


function createManualPickerForm($extra=false, $title='Manual Picker Launcher', $heading='Manual Particle Selection and Editing', $results=false) {

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

  // --- find hosts to run Manual Picker

  $javafunctions="
        <script src='../js/viewer.js'></script>
        <script LANGUAGE='JavaScript'>
                 function enabledtest(){
                         if (document.viewerform.testimage.checked){
                                 document.viewerform.testfilename.disabled=false;
                                 document.viewerform.testfilename.value='';
                                 document.viewerform.commit.disabled=true;
                                 document.viewerform.commit.checked=false;
                         }  
                         else {
                                 document.viewerform.testfilename.disabled=true;
                                 document.viewerform.testfilename.value='mrc file name';
                                 document.viewerform.commit.disabled=false;
                                 document.viewerform.commit.checked=true;
                         }
                 }
                 function disableHsteps(){
			if (document.viewerform.helicalcheck.checked){
				document.viewerform.helicalstep.disabled=true;
				document.viewerform.ovrlp.disabled=true;
			}
			else {
				document.viewerform.helicalstep.disabled=false;
				document.viewerform.ovrlp.disabled=false;
			}
                 }
        </SCRIPT>\n";
  $javafunctions .= writeJavaPopupFunctions('appion');
  processing_header($title="Manual Picker Launcher", $heading="Manual Particle Selection and Editing", 
  					$headerstuff=$javafunctions, $pleaseWait=false, $showmenu=true, $printDiv=false, 
					$guideURL="http://emg.nysbc.org/redmine/projects/appion/wiki/Manual_Picking");
  if ($extra) {
    echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
  }
  if ($results) echo "$results<hr />\n";
  echo"
  <form name='viewerform' method='POST' ACTION='$formAction'>
  <input type='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

  $sessiondata=getSessionList($projectId,$expId);

  // Set any existing parameters in form
  $particle=new particleData;
  $prtlrunIds = $particle->getParticleRunIds($sessionId, True);
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApSelectionRunData','name'); 
  $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'manrun'.($lastrunnumber+1);
  $presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
  $prtlrunval = ($_POST['editrunid']) ? $_POST['editrunid'] : '';
  $testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
  $testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
  $testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';
  $helicalcheck = ($_POST['helicalcheck']=='on') ? 'CHECKED' : '';

  echo"
  <table BORDER=0 CLASS=tableborder CELLPADDING=15>
  <TR>
    <TD VALIGN='TOP'>";

  createAppionLoopTable($sessiondata, $defrunname, "extract");
	?>
	<font style="font-weight: bold"><?=docpop("picklabel", "Particle Labels");?></font>
	<p>
	Label: <input type="text" name="picklabel" value="particle">
	<input type="submit" name="addpicklabel" value="Add">
	</p>
<?php
	$picklabels = (array)$_SESSION['picklabels'];
		
	if ($picklabels) {
		echo '<input type="hidden" name="delpicklabel" value="1">';
	}
	$labeldata=array();
	$pick_color_index=0;
	$editrunlabels = array();
	if (is_numeric($prtlrunval) && $prtlrunval > 0) {
		$editrunparams = $particle->getSelectionParams($prtlrunval);
		
		$editrunlabelinfos = $particle->getParticleLabels($prtlrunval); 
		if (is_array($editrunlabelinfos)) {
			// old run without labels will be automatically assigned
			// therefore better not to use it.
			$editrunname = $editrunparams[0]['name'];
			if (empty($editrunlabelinfos) && in_array($editrunname,(array) $picklabels)) {
				$picklabels = array_diff($picklabels,array($editrunname));
				$_SESSION['picklabels'] = array_diff($_SESSION['picklabels'],array($editrunname));
				echo "<font color=red> Label identical to unlabeled editing pick runname removed </font>";
			}
			foreach ($editrunlabelinfos as $info)
				$editrunlabels[] = $info['label'];
			$oldlabels = implode('|--|',$editrunlabels);
			echo '<input type="hidden" name="editrunpicklabels" value="'.$oldlabels.'">';
			$picklabels = array_unique(array_merge($picklabels,$editrunlabels));
		}
	}
	// Show available labels in different colors
	foreach((array)$picklabels as $k=>$picklabel) {
		$labelrow = array();
		$labelrow[] = $picklabel;
		$labelrow[] = '<img alt="cross" src="../getimgtarget.php?target=cross2&c='
			.$pick_color_index++.'">';
		if (!in_array($picklabel,$editrunlabels))
			$labelrow[] = '<input style="font-size:9px" type="submit" 
				name="'.$k.'i" value="Del">';
		else {
			// Don't allow deletion of labels from pick run to be edited
			$labelrow[] = '(from old picks)';
		}
		$labeldata[] = $labelrow;
	}
	echo array2table($labeldata);
	echo "<hr>";

  if (!$prtlrunIds) {
    echo"<font COLOR='RED'><B>No Particles for this Session</B></font>\n";
    echo"<input type='HIDDEN' NAME='editrunid' VALUE='None'>\n";
  }
  else {
    echo "<br />Edit Particle Picks:
    <SELECT NAME='editrunid' onchange=submit()>\n";
    echo "<OPTION VALUE='None'>None</OPTION>";
    foreach ($prtlrunIds as $prtlrun){
      $prtlrunId=$prtlrun['DEF_id'];
      $runname=$prtlrun['name'];
      $prtlstats=$particle->getStats($prtlrunId);
      $totprtls=commafy($prtlstats['totparticles']);
      echo "<OPTION VALUE='$prtlrunId'";
      // select previously set prtl on resubmit
      if ($prtlrunval==$prtlrunId) {
				$editrunname = $runname;
				echo " SELECTED";
			}
      echo">$runname ($totprtls prtls)</OPTION>\n";
    }
    echo "</SELECT>\n";
    echo"<input type='HIDDEN' NAME='editrunname' VALUE='".$editrunname."'>\n";
  }
	// pick and image parameters
  echo "<TD CLASS='tablebg'>\n";
  echo "<b>Particle Diameter:</b><br />\n";
  $diam = ($_POST['diam']) ? $_POST['diam'] : "";
  echo "<input type='text' NAME='diam' VALUE='$diam' SIZE='4'>\n";
  echo docpop('pdiam','Particle diameter for result images');
  echo "<font SIZE=-2><I>(in &Aring;ngstroms)</I></font>\n";
  echo "<br /><br />\n";
  echo "<B>Picking Icon</B><I>\n";
  echo "<br />(only for visual purposes, does not affect data)</I>:<br />\n";
  echo "<SELECT NAME='shape'>\n";
  $shapes = array('plus', 'circle', 'cross', 'point', 'square', 'diamond', );
  foreach($shapes as $shape) {
    $s = ($_POST['shape']==$shape) ? 'SELECTED' : '';
    echo "<OPTION $s>$shape</OPTION>\n";
  }
  echo "</SELECT>\n&nbsp;Picking icon shape<br />";
  $shapesize = (int) $_POST['shapesize'];
  echo"
    <input type='text' NAME='shapesize' VALUE='$shapesize' SIZE='3'>&nbsp;
    Picking icon diameter <font SIZE=-2><I>(in pixels; 0 = autosize)</I></font><br />
		<I>16 pixels is best</I>
    <br /><br />";    
  echo "<b>Helical Parameters:</b><br />\n";
	echo "<input type='checkbox' name='helicalcheck' onclick='disableHsteps()' $helicalcheck >\n";
	echo docpop('alonghelices','Pick along helices');
	echo "<br>\n";
  $helicalstep = ($_POST['helicalstep']) ? $_POST['helicalstep'] : "";
  echo "<input type='text' NAME='helicalstep' VALUE='$helicalstep' SIZE='4'>\n";
  echo docpop('helicalstep','Stepsize for Helical Insert');
  echo "<font SIZE=-2><I>(in &Aring;ngstroms)</I></font>\n";
  echo "<br />\n";
  $ovrlp = ($_POST['ovrlp']) ? $_POST['ovrlp'] : "0";
  echo "<input type='text' NAME='ovrlp' VALUE='$ovrlp' SIZE='4'>\n";
  echo docpop('ovrlp','Percent overlap');
  echo "<font SIZE=-2><I>(%)</I></font>\n";
  echo "<br /><br />\n";
  createParticleLoopTable(-1, -1);
  echo "
		</TD>
		</tr>
		<TR>
		<TD COLSPAN='2' ALIGN='CENTER'><hr>";
	echo getSubmitForm("Run ManualPicker", true, true);
  echo "</TD>
		</tr>
		</table>
		</CENTER>
		</FORM>
	";

	echo appionRef();

  processing_footer();
  exit;
}

function runManualPicker() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

  $command.="manualpicker.py ";
  $apcommand = parseAppionLoopParams($_POST);
  if ($apcommand[0] == "<") {
    createManualPickerForm($apcommand);
    exit;
  }
  $command .= $apcommand;

  $partcommand = parseParticleLoopParams("manual", $_POST);
  if ($partcommand[0] == "<") {
    createManualPickerForm($partcommand);
    exit;
  }
  $command .= $partcommand;
  $editrunid=$_POST['editrunid'];
  if ($editrunid != 'None') {
    $command .= " --pickrunid=$editrunid";
  }

  $shape=$_POST['shape'];
  if($shape) {
    $command .= " --shape=$shape";
  }

  $shapesize = (int) $_POST['shapesize'];
  if($shapesize && is_int($shapesize)) {
    $command .= " --shapesize=$shapesize";
  } 

  $helicalcheck=($_POST['helicalcheck']=='on') ? True: False;
  $helicalstep=$_POST['helicalstep'];
  $ovrlp=$_POST['ovrlp'];
  if ($helicalcheck) $command .= " --helix";
  elseif($helicalstep) {
    $command .= " --helicalstep=$helicalstep";
    $command .= " --ovrlp=$ovrlp";
  }

	$oldlabels = explode('|--|',$_POST['editrunpicklabels']);
	$picklabels = array_unique(array_merge((array)$_SESSION['picklabels'],$oldlabels));
	foreach ((array)$picklabels as $picklabel) {
		if (strlen($picklabel))
			$command .= " --label=$picklabel";
	}
	
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= appionRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'manualpicker', 1);

	// if error display them
	if ($errors)
		createManualPickerForm($errors);
	exit;
}

?>
