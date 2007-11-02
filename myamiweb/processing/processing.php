<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *  Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/ctf.inc";
require "inc/leginon.inc";
require "inc/project.inc";

if ($_POST['login']) {
  $errors = checkLogin();
  if ($errors) processTable($extra=$errors);
}

processTable();

function processTable($extra=False) {
$leginondata = new leginondata();

// check if coming directly from a session
$expId=$_GET['expId'];
if ($expId){
  $sessionId=$expId;
  $projectId=getProjectFromExpId($expId);
  $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
  $sessionId=$_POST['sessionId'];
  $formAction=$_SERVER['PHP_SELF'];  
}
$projectId=$_POST['projectId'];

writeTop("Appion Data Processing","Appion Data Processing", "<script src='../js/viewer.js'></script>",False);

// write out errors, if any came up:
if ($extra) {
  echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
}

// create login form
$display_login = ($_SESSION['username'] && $_SESSION['password']) ? false:true;

if ($display_login) {
  $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  displayLogin($formAction);
}

echo"
<P>
<TABLE>
<TR><TD ALIGN='LEFT'>
<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

// Collect session info from database
$sessiondata=getSessionList($projectId,$sessionId);
$sessioninfo=$sessiondata['info'];
$sessions=$sessiondata['sessions'];
$currentproject=$sessiondata['currentproject'];

// Set colors for unprocessed & finished steps:
$nonecolor='#FFFFCC';
$progcolor='#CCFFFF';
$donecolor='#CCFFCC';
$mode = "neild";
if($mode == "neil") {
	$donepic='img/icon-check.png';
	$nonepic='img/icon-cross.png';
	$progpic='img/icon-bluestar.png';
} else {
	$donepic='img/green_circle.gif';
	$nonepic='img/red_circle.gif';
	$progpic='img/blue_circle.gif';
}

// If expId specified, don't show pulldowns, only session info
if (!$expId){
  echo"
  <B>Select Session:</B><BR>
  <SELECT NAME='projectId' onchange='newexp()'>\n";
  $projects=getProjectList();
  foreach ($projects as $k=>$project) {
    $sel = ($project['id']==$projectId) ? "selected" : '';
    echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
  }
  
  echo"
  </select>
  <BR>
 
  <SELECT NAME='sessionId' onchange='newexp()'>
  <option value=''>all sessions</OPTION>\n";
  foreach ($sessions as $k=>$session) {
    $sel = ($session['id']==$sessionId) ? 'selected' : '';
    $shortname=substr($session['name'],0,90);
    echo "<option value='".$session['id']."'".$sel.">".$shortname."</option>";
  }
  echo"</select>\n";
}
// Show project & session pulldowns
else {
  $proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
  $sessionDescr=$sessioninfo['Purpose'];
  echo "<TABLE>";
  echo "<TR><TD><B>Project:</B></TD><TD>$proj_link</TD></TR>\n";
  echo "<TR><TD><B>Session:</B></TD><TD>$sessionDescr</TD></TR>\n";

  // get experiment information
  $expinfo = $leginondata->getSessionInfo($expId);
  if (!empty($expinfo)) {
    $i=0;
    $imgpath=$expinfo['Image path'];
    echo "<TR><TD><B>Image Path:</B></TD><TD>$imgpath</TD></TR>\n";
  }
  echo "</TABLE>\n";
}
echo "<P>\n";

if ($sessionId) {
// ---  Get CTF Data
  $ctf = new ctfdata();
  if ($ctfrunIds = $ctf->getCtfRunIds($sessionId))
		$ctfruns=count($ctfrunIds);

  // --- Get Particle Selection Data
  $particle = new particledata();
  if ($prtlrunIds = $particle->getParticleRunIds($sessionId))
		$prtlruns=count($prtlrunIds);

  // retrieve template info from database for this project
  if ($expId){
    $projectId=getProjectFromExpId($expId);
  }
  if (is_numeric($projectId)) {
    if ($templatesData=$particle->getTemplatesFromProject($projectId))
			$templates = count($templatesData);
    if ($modelData=$particle->getModelsFromProject($projectId))
			$models = count($modelData);
  }

  // --- Get Mask Maker Data
  if ($maskrunIds = $particle->getMaskMakerRunIds($sessionId))
		$maskruns=count($maskrunIds);

  // --- Get Micrograph Assessment Data
  $totimgs = $particle->getNumImgsFromSessionId($sessionId);
  $assessedimgs = $particle->getNumAssessedImages($sessionId);
  
  // --- Get Stack Data
  if ($stackIds = $particle->getStackIds($sessionId))
		$stackruns=count($stackIds);

  // --- Get Class Data
  if ($stackruns>0) {
    $norefIds = $particle->getNoRefIds($sessionId);
    $norefruns=count($norefIds);
  } else {
    $norefruns=0;
  };

  // --- Get Ref-based Alignment Data
  if ($stackruns>0) {
    $refaliIds = $particle->getRefAliIds($sessionId);
		$refaliruns=count($refaliIds);
  } else {
    $refaliruns=0;
  };

  // --- Get Reconstruction Data
  if ($stackruns>0) {
    foreach ((array)$stackIds as $stackid) {
      $reconIds = $particle->getReconIds($stackid['stackid']);
      if ($reconIds) {
        $reconruns+=count($reconIds);
      }
    }
    $subjobs = $particle->getSubmittedJobs($sessionId);
    $numsubjobs = count($subjobs);
  }

  echo"
  </FORM>
  <TABLE BORDER='1' CLASS='tableborder' CELLPADDING='5'>
  <TR>\n";
  //header
  echo"
	 <TD ALIGN='LEFT' COLSPAN='2'><H4>Action</H4></TD>
	 <TD ALIGN='LEFT'><H4>Results</H4></TD>
	 <TD ALIGN='LEFT'><H4>New run</H4></TD>
  </TR><TR>\n";
  if ($prtlruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Particle Selection</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($prtlruns==0) {echo "none";}
    else {echo "<A HREF='prtlreport.php?expId=$sessionId'>$prtlruns completed</A>\n";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>";
    if ($templates==0) {
    	echo"<A HREF='uploadtemplate.php?expId=$sessionId'>";
      echo "Upload template for picking";
    } else {
    	echo"<A HREF='runPySelexon.php?expId=$sessionId'>";
    	if ($prtlruns==0) {echo "Template Picking";}
    	else {echo "Template Picking";}
    }
    echo"</A><BR>
    <A HREF='runDogPicker.php?expId=$sessionId'>";
    if ($prtlruns==0) {echo "DoG Picking";}
    else {echo "DoG Picking";}
    echo"</A><BR>
    <A HREF='runManualPicker.php?expId=$sessionId'>";
    if ($prtlruns==0) {echo "Manual Picking";}
    else {echo "Manually Edit Picking";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($ctfruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>CTF Estimation</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($ctfruns==0) {echo "none";}
    else {echo "<A HREF='ctfreport.php?Id=$sessionId'>$ctfruns completed</A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='runPyAce.php?expId=$sessionId'>";
    if ($ctfruns==0) {echo "ACE Estimation";}
    else {echo "ACE Estimation";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($assessedimgs==0 || $totimgs == 0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  elseif ($assessedimgs < $totimgs) {$bgcolor=$progcolor; $gifimg=$progpic;}
  else {$bgcolor=$donecolor; $gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Micrograph Assessment</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>";
    if ($assessedimgs==0 || $totimgs==0) { echo "none"; }
    elseif ($assessedimgs < $totimgs) { echo "$assessedimgs of $totimgs completed"; }
    elseif ($totimgs!=0) { echo "All $assessedimgs completed"; }
    else { echo "none"; }
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='imgassessor.php?expId=$sessionId'>";
    if ($assessedimgs==0) {echo "Manual Image Assessment";}
    else {
      if ($assessedimgs < $totimgs || $totimgs==0) echo "Continue Manual Assessment";
      else echo "Re-Assess Images";
    }
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($maskruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Region Mask Creation</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($maskruns==0) {echo "none";}
    else {echo "<A HREF='maskreport.php?expId=$sessionId'>$maskruns completed</A>\n";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='runMaskMaker.php?expId=$sessionId'>";
    if ($maskruns==0) {echo "Crud Finding";}
    else {echo "Crud Finding";}
    echo"</A><BR>
    <A HREF='manualMaskMaker.php?expId=$sessionId'>";
    if ($maskruns==0) {echo "Manual Masking";}
    else {echo "Manual Masking";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($stackruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Stacks</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($stackruns==0) {echo "none";}
    else {echo "<A HREF='stacksummary.php?expId=$sessionId'>$stackruns completed<A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>";
    if ($prtlruns == 0) {
      echo "<FONT SIZE=-1><I>Pick some particles first</I></FONT>";
    } elseif ($stackruns == 0) {
      echo"<A HREF='makestack.php?expId=$sessionId'>Stack creation</A>";
    } else {
      echo"<A HREF='makestack.php?expId=$sessionId'>Stack creation</A>";
    }
    echo"</TD></TR>
  <TR>\n";
  if ($norefruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Reference-free Classification</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($norefruns==0) {echo "none";}
    else {echo "<A HREF='norefsummary.php?expId=$sessionId'>$norefruns completed<A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>";
    if ($stackruns == 0) {echo "<FONT SIZE=-1><I>Create a stack first</I></FONT>";}
    else {echo"<A HREF='classifier.php?expId=$sessionId'>Ref-free Classification</A>";}
    echo"</TD>
  </TR>
  <TR>\n";
  if ($refaliruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Reference-based Alignment</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($refaliruns==0) {echo "none";}
    else {echo "<A HREF='refalisummary.php?expId=$sessionId'>$refaliruns completed<A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>";
    if ($stackruns == 0) {echo "<FONT SIZE=-1><I>Create a stack first</I></FONT>";}
    elseif ($refruns == 0) {echo"<A HREF='refbasedali.php?expId=$sessionId'>Ref-based Alignment</A>";}
    echo"</TD>
  </TR>
  <TR>\n";
  // if no submitted jobs, display none
  // for every uploaded job, subtract a submitted job
  // if all submitted jobs are uploaded, it should be 0
  $waitingjobs = $numsubjobs-$reconruns;
  if ($numsubjobs==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  elseif ($waitingjobs > 0) {$bgcolor=$progcolor;$gifimg=$progpic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Reconstructions</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
  if ($numsubjobs==0) {echo "none";}
  else {
    if ($waitingjobs>0) echo "<A HREF='checkjobs.php?expId=$sessionId'>$waitingjobs queued</A>\n";
    if ($waitingjobs>0 && $reconruns>0) echo "<BR/>\n";
    if ($reconruns>0) echo "<A HREF='reconsummary.php?expId=$sessionId'>$reconruns uploaded</A>";
  }
  echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>";
  if ($stackruns == 0) {
    echo "<FONT SIZE=-1><I>Create a stack first</I></FONT>";
  } 
  else {
    echo"<A HREF='emanJobGen.php?expId=$sessionId'>EMAN Reconstruction</A>";
  }
  if ($stackruns>0) {
    echo"<BR><A HREF='uploadrecon.php?expId=$sessionId'>Upload Reconstruction</A>";
  }
  echo"</TD>
  </TR>
  <TR>
    <TD COLSPAN='4'>
    <BR/>
    <B>Pipeline tools:</B>
    </TD>
  </TR>
  ";
  echo"
  <TR>\n";
  if ($templates==0) {$bgcolor=$nonecolor; $gifimg=$nonepic;}
  else {$bgcolor=$donecolor; $gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Templates</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
  if ($templates==0) {echo "none";}
  else {echo "<A HREF='viewtemplates.php?expId=$sessionId'>$templates available</A>";}
  //else {echo "$templates available";}
  echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>";
  if ($templates==0) { echo"<A HREF='uploadtemplate.php?expId=$sessionId'>Upload template</A>"; }
  else { echo"<A HREF='uploadtemplate.php?expId=$sessionId'>Upload template</A>"; }
  echo"</TD>
  </TR>
  <TR>\n";
  if ($models==0) {$bgcolor=$nonecolor; $gifimg=$nonepic;}
  else {$bgcolor=$donecolor; $gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Initial Models</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
  if ($models==0) {echo "none";}
  else {echo "<A HREF='viewmodels.php?expId=$sessionId'>$models available</A>";}
  echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>";
  if ($models==0) { echo"<A HREF='uploadmodel.php?expId=$sessionId'>Upload model</A>"; }
  else { echo"<A HREF='uploadmodel.php?expId=$sessionId'>Upload model</A>"; }
  echo"</TD>
  </TR>
  </TABLE>
  </TD>\n";
}
echo"
</TR>
</TABLE>
</CENTER>\n";
writeBottom($showproclink=False);
exit;
}

?>
