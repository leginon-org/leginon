<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Form for starting a reference-based alignment of a stack
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
  runAlignment();
}

 // Create the form page
elseif ($_POST['templates']) {
  createAlignmentForm();
}

// Make the template selection form
else {
  createTemplateForm();
}

function createTemplateForm() {
	// check if coming directly from a session
	$expId = $_GET[expId];
	$formAction=$_SERVER['PHP_SELF'];	

	// retrieve template info from database for this project
	if ($expId){
	$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}

	// if user wants to use templates from another project
	if($_POST['projectId']) $projectId =$_POST[projectId];

	$projects=getProjectList();

	if (is_numeric($projectId)) {
		$particle=new particleData;
		$templateData=$particle->getTemplatesFromProject($projectId);
	}

	// extract template info
	if ($templateData) {
		$i=1;
		$templatetable="<TABLE CLASS='tableborder' BORDER='1' CELLPADDING='5' WIDTH='600'>\n";
		$numtemplates=count($templateData);

		foreach($templateData as $templateinfo) { 
			if (is_array($templateinfo)) {
				$filename = $templateinfo[path] ."/".$templateinfo[templatename];
				$checkboxname='template'.$i;
				// create the image template table
				$templatetable.="<TR><TD>\n";
				$templatetable.="<IMG SRC='loadimg.php?filename=$filename&rescale=True' WIDTH='200'></TD>\n";
				$templatetable.="<TD>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='templateId".$i."' VALUE='$templateinfo[DEF_id]'>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='diam' VALUE='$templateinfo[diam]'>\n";
				$templatetable.="<INPUT TYPE='checkbox' NAME='$checkboxname'>\n";
				$templatetable.="<B>Use This Template</B><BR/>\n";
				$templatetable.="<B>Template ID:</B>  $templateinfo[DEF_id]<BR/>\n";
				$templatetable.="<B>Diameter:</B>  $templateinfo[diam]<BR/>\n";
				$templatetable.="<B>Pixel Size:</B>  $templateinfo[apix]<BR/>\n";
				$templatetable.="<B>File:</B><BR/>";
				$templatetable.="<TABLE CLASS='tableborder' BORDER='1'><TR><TD CLASS='tablebg'>\n";
				$templatetable.=$filename;
				$templatetable.="</TD></TR></TABLE>\n";
				$templatetable.="<B>Description:</B><BR/>";
				$templatetable.="<TABLE CLASS='tableborder' BORDER='1'><TR><TD CLASS='tablebg'>\n";
				$templatetable.=$templateinfo[description];
				$templatetable.="</TD></TR></TABLE>\n";
				$templatetable.="</TD></TR>\n";

				$i++;
			}
		}
		$templatetable.="</TABLE>\n";
	}

	processing_header("Template Correlator Launcher","Automated Particle Selection with Template Correlator","");
	echo"
  <FORM NAME='viewerform' method='POST' ACTION='$formAction'>
  <B>Select Project:</B><BR>
  <SELECT NAME='projectId' onchange='newexp()'>\n";

	foreach ($projects as $k=>$project) {
		$sel = ($project['id']==$projectId) ? "selected" : '';
		echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
	}
	echo"
  </select>\n";
	if ($templatetable) {
		echo"
    <CENTER>
    <INPUT TYPE='submit' NAME='templates' value='Use These Templates'>
    </CENTER>\n
    $templatetable
    <CENTER>
    <INPUT TYPE='hidden' NAME='numtemplates' value='$numtemplates'>
    <INPUT TYPE='submit' NAME='templates' value='Use These Templates'>
    </CENTER>\n";
	}
	else echo "<B>Project does not contain any templates.</B>\n";
	echo"</FORM>\n";
}

function createAlignmentForm($extra=false, $title='refBasedAlignment.py Launcher', $heading='Perform a reference-based Alignment') {
  // check if coming directly from a session
	//echo print_r($_POST);

	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	// connect to particle info
	$particle = new particledata();
	$templateid = $_POST['templateid'];
	$templateinfo = $particle->getTemplatesFromId($templateid);
	$stackIds = $particle->getStackIds($sessionId);
	$refbasedIds = $particle->getRefAliIds($sessionId);
	$alignruns = count($particle->getAlignStackIds($sessionId, $projectId));

	processing_header($title,$heading,"");
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
  
  // Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'refbased'.($alignruns+1)))
		$alignruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'refbased'.($alignruns+1);
	$rundescrval = $_POST['description'];
	$stackidval =$_POST['stackid'];
	$lp = $_POST['lp'];
	$csym = $_POST['csym'];
	$commitcheck = ($_POST['commit']=='on') ? 'CHECKED' : '';
	$staticref = ($_POST['staticref']=='on') ? 'CHECKED' : '';
	// alignment params
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : 3000;
	$iters = ($_POST['iters']) ? $_POST['iters'] : 5;
	$lp = ($_POST['lp']) ? $_POST['lp'] : 10;
	$diam = $_POST['diam'] ? $_POST['diam'] : 160;
	$xysearch = ($_POST['xysearch']) ? $_POST['xysearch'] : '3';
	$xystep = ($_POST['xystep']) ? $_POST['xystep'] : '1';
	$csym = 1;
	$maskdiam = ($_POST['maskdiam']) ? $_POST['maskdiam'] : $diam;
	$imaskdiam = ($_POST['imaskdiam']) ? $_POST['imaskdiam'] : '2';


	$templateCheck='';
	$templateTable.="<TABLE><TR>\n";
	for ($i=1; $i<=$_POST['numtemplates']; $i++) {
		$templateimg = "template".$i;
		if ($_POST[$templateimg]){
			$templateTable.="<TD VALIGN='TOP'><TABLE CLASS='tableborder'>\n";
			$templateIdName="templateId".$i;
			$templateId=$_POST[$templateIdName];
			$templateList.=$i.":".$templateId.",";
			$templateinfo=$particle->getTemplatesFromId($templateId);
			$filename=$templateinfo[path]."/".$templateinfo['templatename'];
			$templateTable.="<TR><TD VALIGN='TOP'><IMG SRC='loadimg.php?filename=$filename&rescale=True' WIDTH='200'></TD></TR>\n";
			$templateTable.="<TR><TD VALIGN='TOP'>".$templateinfo['templatename']."</TD></TR>\n";
			$templateForm.="<INPUT TYPE='hidden' NAME='$templateIdName' VALUE='$templateId'>\n";
			$templateForm.="<INPUT TYPE='hidden' NAME='$templateimg' VALUE='$templateId'>\n";
			$templateTable.="</TABLE></TD>\n";
		}
	}
	$templateTable.="</TR></TABLE>\n";
	if ($templateList) { $templateList=substr($templateList,0,-1);}
	else {
		echo "<BR/><B>no templates chosen, go back and choose templates</B>\n";
		exit;
	}
	echo "<INPUT TYPE='hidden' NAME='templateList' VALUE='$templateList'>\n";
	echo "<INPUT TYPE='hidden' NAME='templates' VALUE='continue'>\n";
	echo "<INPUT TYPE='hidden' NAME='numtemplates' VALUE='$numtemplates'>\n";

  echo"
	<TABLE BORDER=0 CLASS=tableborder>
	<TR>
		<TD VALIGN='TOP'>
		<TABLE CELLPADDING='10' BORDER='0'>
		<TR>
			<TD VALIGN='TOP'>
			<B>Alignment Run Name:</B>
			<INPUT TYPE='text' NAME='runname' VALUE='$runnameval'>
			</TD>
		</TR>\n";
		echo"<TR>
			<TD VALIGN='TOP'>
			<B>Alignment Description:</B><BR>
			<TEXTAREA NAME='description' ROWS='3' COLS='36'>$rundescrval</TEXTAREA>
			</TD>
		</TR>\n";
		echo"<TR>
			<TD VALIGN='TOP'>	 
			<B>Output Directory:</B><BR>
			<INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='38'>
			</TD>
		</TR>
		<TR>
			<TD>\n";

	if (!$stackIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo "
		Particles:<BR>
		<SELECT NAME='stackid'>\n";
		foreach ($stackIds as $stack) {
			$stackid = $stack['stackid'];
			$stackparams=$particle->getStackParams($stackid);
			$boxsz=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];
			$mpix=$particle->getStackPixelSizeFromStackId($stackid);
			$apixtxt=format_angstrom_number($mpix)."/pixel";
			$runname=$stackparams['shownstackname'];
			$totprtls=commafy($particle->getNumStackParticles($stackid));
			echo "<OPTION VALUE='$stackid'";
			// select previously set prtl on resubmit
			if ($stackidval == $stackid) echo " SELECTED";
			echo ">$stackid: $runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo"
		</TD>
	</TR>";
	echo"
	<TR>
		<TD VALIGN='TOP'>
		<INPUT TYPE='checkbox' NAME='commit' $commitcheck>
		<B>Commit to Database</B><BR>
		</TD>
	</TR>";
	echo"
	</TABLE>
	</TD>
	<TD CLASS='tablebg'>
	<TABLE CELLPADDING='5' BORDER='0'>
	<TR>";
	echo"
		<TD VALIGN='TOP'>
		<B>Particle Params:</B></A><BR>";
	echo"
		<INPUT TYPE='text' NAME='maskdiam' SIZE='5' VALUE='$maskdiam'>
		Last Ring Radius <FONT SIZE='-1'>(in pixels)</FONT><BR>";
	echo"
		<INPUT TYPE='text' NAME='imaskdiam' SIZE='5' VALUE='$imaskdiam'>
		First Ring Radius <FONT SIZE='-1'>(in pixels)</FONT><BR>";
	echo"
		<INPUT TYPE='text' NAME='lp' SIZE='5' VALUE='$lp'>
		Low Pass Filter <FONT SIZE='-1'>(in &Aring;ngstroms)</FONT><BR>";
	echo"
		</TD>
	</TR>
	<TR>
		<TD VALIGN='TOP'>
		<B>Alignment Params:</B></A><BR>";
	echo"
		<INPUT TYPE='text' NAME='iters' VALUE='$iters' SIZE='4'>
		Iterations<BR>";
	echo"
		<INPUT TYPE='text' NAME='xysearch' VALUE='$xysearch' SIZE='4'>
		Search range from center <FONT SIZE='-1'>(in pixels)</FONT><BR>";
	echo"
		<INPUT TYPE='text' NAME='xystep' VALUE='$xystep' SIZE='4'>
		Step size for parsing search range <FONT SIZE='-1'>(in pixels)</FONT><BR>";
	//echo"
	//	<INPUT TYPE='text' NAME='csym' VALUE='$csym' SIZE='4'>
	//	C-symmetry to apply<BR>";
	echo"
		<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>
		Number of Particles to Use<BR>";
	//echo"
	//	<INPUT TYPE='checkbox' NAME='staticref' $staticref>
	//	Use original references for each iteration<BR>";
	echo"
		<INPUT TYPE='checkbox' NAME='inverttempl' $inverttempl>
		Invert density of all templates before alignment<BR>";
	echo"
		</TD>
	</TR>
	</TR>
	</TABLE>
	</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>";
	echo"<INPUT TYPE='hidden' NAME='refid' VALUE='$templateid'>";
	echo getSubmitForm("Run Ref-Based Alignment");
	echo "
	  </TD>
	</TR>
	</TABLE>
	</FORM>
	</CENTER>\n";

	echo "$templateForm\n";
	echo "$templateTable\n";

	processing_footer();
	exit;
}

function runAlignment() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$stackid=$_POST['stackid'];
	$maskdiam=$_POST['maskdiam'];
	$imaskdiam=$_POST['imaskdiam'];
	$lp=$_POST['lp'];
	$csym=$_POST['csym'];
	$xysearch=$_POST['xysearch'];
	$xystep=$_POST['xystep'];
	$refid=$_POST['refid'];
	$iters=$_POST['iters'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$staticref = ($_POST['staticref']=="on") ? 'staticref' : '';
	$inverttempl = ($_POST['inverttempl']=="on") ? 'inverttempl' : '';

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createAlignmentForm("<B>ERROR:</B> Enter a brief description of the alignment run");

	//make sure a stack was selected
	$stackid=$_POST['stackid'];
	if (!$stackid) createAlignmentForm("<B>ERROR:</B> No stack selected");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// alignment
	$numpart=$_POST['numpart'];
	if ($numpart < 1) 
		createAlignmentForm("<B>ERROR:</B> Number of particles must be at least 1");
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) 
		createAlignmentForm("<B>ERROR:</B> Number of particles to aligne ($numpart) must be less than the number of particles in the stack ($totprtls)");

	$fileformat = ($_POST['fileformat']=='spider') ? 'spider' : '';

//	$command ="source /ami/sw/ami.csh;";
//	$command.="source /ami/sw/share/python/usepython.csh common32;";
//	$command.="source /home/$user/pyappion/useappion.csh;";
	$command="refBasedAlignment2.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--template-list=".templateCommand()." ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";

	if ($maskdiam) $command.="--last-ring=$maskdiam ";
	if ($imaskdiam) $command.="--first-ring=$imaskdiam ";
	$command.="--rundir=".$rundir." ";
	$command.="--description=\"$description\" ";
	$command.="--lowpass=$lp ";
	#if ($csym > 1) $command.="--csym=$csym ";
	$command.="--xy-search=$xysearch ";
	$command.="--xy-step=$xystep ";
	$command.="--num-iter=$iters ";
	$command.="--num-part=$numpart ";
	if ($inverttempl) $command.="--invert-templates ";
	#if ($staticref) $command.="--static-ref ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Run Ref-Based Alignment") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password))
			createAlignmentForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'partalign');
		// if errors:
		if ($sub)
			createAlignmentForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Alignment Run","Alignment Params");

		echo"
		<TABLE WIDTH='600' BORDER='1'>
		<TR><TD COLSPAN='2'>
		<B>Alignment Command:</B><BR>
		$command
		</TD></TR>
		<TR><TD>runname</TD><TD>$runname</TD></TR>
		<TR><TD>stackid</TD><TD>$stackid</TD></TR>
		<TR><TD>refids</TD><TD>".templateCommand()."</TD></TR>
		<TR><TD>iter</TD><TD>$iters</TD></TR>
		<TR><TD>numpart</TD><TD>$numpart</TD></TR>
		<TR><TD>last ring</TD><TD>$maskdiam</TD></TR>
		<TR><TD>first ring</TD><TD>$imaskdiam</TD></TR>
		<TR><TD>rundir</TD><TD>$rundir</TD></TR>
		<TR><TD>xysearch</TD><TD>$xysearch</TD></TR>
		<TR><TD>xystep</TD><TD>$xystep</TD></TR>
		<TR><TD>lowpass</TD><TD>$lp</TD></TR>";
		if ($csym > 1) echo"	<TR><TD>c-symmetry</TD><TD>$csym</TD></TR>";
		echo"	</TABLE>\n";
		processing_footer();
	}
}

/*
**
**
** GENERATE COMMANDLINE INFO FOR TEMPLATES
**
**
*/

function templateCommand () {
	$command = "";
	// get the list of templates
	$templateList=$_POST['templateList'];
	$templates=split(",", $templateList);
	foreach ($templates as $tmplt) {
		list($tmpltNum,$tmpltId)=split(":",$tmplt);
		$templateIds.="$tmpltId,";
	}
	$templateIds=substr($templateIds,0,-1);
	return $templateIds;
	$command.="refids=$templateIds ";
	return $command;
}

?>
