<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runCreateModel();
}

// IF METHOD IS SELECTED
elseif ($_POST['selectmethod']) {
	createSelectParameterForm();
}

// Create the form page
else {
	createEMANInitialModelForm();
}


#######################################################################################


function createEMANInitialModelForm($extra=false, $title='EMAN Common Lines createModel.py Launcher', $heading='Run EMAN Common Lines') {
   // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$norefClassId=$_GET['norefClass'];
	$norefClassfile=$_GET['file'];
	$norefId=$_GET['noref'];
	$exclude=$_GET['exclude'];
	
	// Set any existing parameters in form
	if (!$description) $description = $_POST['description'];
	if (!$norefClassId) $norefClassId = $_POST['norefClass'];
	if (!$norefId) $norefId = $_POST['noref'];
	if (!strlen($exclude)) $exclude = $_POST['exclude'];
	$commit = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	$startcsymcheck = ($_POST['method']=='startcsym') ? 'CHECKED' : '';

	// get outdir path
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='red'>$extra</font>\n<hr />\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	
	//query the database for parameters
	$particle = new particledata();
	
	# get outdir
	$noref = $particle->getNoRefParams($norefId);
	$outdir = $noref['path'];

	# get apix
	if (!$apix) {
		$apix=($particle->getStackPixelSizeFromStackId($noref["REF|ApStackData|stack"]))*1e10;
	}
	echo "<input type='hidden' name='apix' value='$apix'>";

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";

	# if norefClassId was given
	if ($norefClassId) {

		echo"
			<b>Reference Free Class Information:</b> <br />
			Name & Path: $norefClassfile <br />
			<input type='hidden' name='norefClassfile' value='$norefClassfile'>
			Noref Class ID: $norefClassId<br />
			<input type='hidden' name='norefClassId' value='$norefClassId'>
			<input type='hidden' name='norefId' value='$norefId'>
			<br />\n";

	# if norefClassId was unavailable
	} else {

		echo "<b>Select reference-free classes</b>:<br><br>";
		$norefclassruns = $particle->getAllNoRefClassRuns($expId);
		echo "<SELECT name='norefclass'>\n";
		foreach ($norefclassruns as $class){
			$classid  = $class['DEF_id'];
			$runname  = $class['name'];
			$numclass = $class['num_classes'];
			$descript = substr($class['description'],0,40);
			echo "<OPTION value='$classid'";
			if ($classid == $norefclassrun) echo " SELECTED";
			echo">$classid: $runname ($numclass classes) $descript...</OPTION>\n";
		}
		echo "</SELECT>\n<br/>\n<br/>\n";

		echo"<b>OR select from <a href='http://cronus3/laupw/dbem/processing/norefsummary.php?expId=$expId'>Reference-free Summary Page</a><br><br></b>";
	}

	echo docpop('commonlineemanprog','<b>EMAN Program:</b> ');
	echo "<input type='radio' name='method' value='startCSym' 'CHECKED'> StartCSym\n";
	echo "<input type='radio' name='method' value='startIcos' > StartIcos\n";
	echo "<input type='radio' name='method' value='startOct' > StartOct\n";
	echo "<input type='radio' name='method' value='startAny' > StartAny<br /><br />\n";

	if ($norefClassId) {
		echo docpop('outdir','<b>Output Directory:</b> ');
		echo "<input type='text' name='outdir' value='$outdir' size='38'><br />\n";
	}
	echo docpop('excludeClass','<b>Excluded Classes:</b> ');
	echo "<input type='text' name='exclude' value='$exclude' size='38'><br /><br />\n";
	echo "<b>Description:</b><br />\n";
	echo "<textarea name='descript' rows='3'cols='70'>$description</textarea>\n";
	echo "<br />\n";
	echo "<input type='checkbox' name='commit' $commit>\n";
	echo docpop('commit','<b>Commit model to database');
	echo "<br />\n";
	echo "</td><tr><td align='center'>";

	echo"<P><input type='SUBMIT' NAME='selectmethod' VALUE='Use this EMAN initial model method'>";

	echo "
	</td>
	</tr>
  	</table>
  	</form>\n";

	processing_footer();
	exit;
}

#######################################################################################


function createSelectParameterForm($extra=false, $title='createModel.py Launcher', $heading='Making an initial model... selecting parameters'){

	// get from previous from
	$expId = $_GET['expId'];
	$projectId=getProjectFromExpId($expId);

	$norefClassId=$_POST['norefClassId'];
	if (!$norefClassId) $norefClassId=$_POST['norefclass'];

	$norefId=$_POST['norefId'];
	if (!$norefId) {
		$particle = new particledata();
		$norefClassData = $particle->getNoRefClassRunData($norefClassId);
		$norefId = $norefClassData['REF|ApNoRefRunData|norefRun'];
		$norefData = $particle->getNoRefParams($norefId);
	}

	$norefClassfile=$_POST['norefClassfile'];
	if (!$norefClassfile) {
		$test = $particle->getNoRefClassRunData($norefClassId);
		$norefClassfile = $norefData['path']."/".$norefClassData['classFile'].".img";
	}
	
	$apix=$_POST['apix'];
	$outdir=$_POST['outdir'];
	if (!$outdir) {
		$outdir = $norefData['path'];
	}
	$commit=$_POST['commit'];
	$exclude=$_POST['exclude'];
	$method=$_POST['method'];

	$description=$_POST['descript'];
	if (!$description) createEMANInitialModelForm("<B>ERROR:</B> Enter a brief description");
	
	// Set any existing parameters in form
	if (!$description) $description = $_POST['descript'];		
	if (!$norefClassId) $norefClassId = $_POST['norefClass'];
	if (!$norefClassfile) $norefClassfile = $_POST['file'];
	if (!$norefId) $norefId = $_POST['noref'];
	if (!strlen($exclude)) $exclude = $_POST['exclude'];

	// get outdir path
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='red'>$extra</font>\n<hr />\n";
	}
	
	echo"<form name='viewerform' method='post' action='$formAction'>\n";

	echo "<input type='hidden' name='method' value='$method'>";
	echo "<input type='hidden' name='descript' value='$description'>";
	echo "<input type='hidden' name='exclude' value='$exclude'>";
	echo "<input type='hidden' name='commit' value='$commit'>";
	echo "<input type='hidden' name='norefClassId' value='$norefClassId'>";
	echo "<input type='hidden' name='norefId' value='$norefId'>";
	echo "<input type='hidden' name='outdir' value='$outdir'>";
	echo "<input type='hidden' name='apix' value='$apix'>";

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo"<INPUT TYPE='hidden' NAME='session' VALUE='$sessionname'>\n";
	}

	echo"

		<TABLE BORDER=3 CLASS=tableborder>
			<TR><TD VALIGN='TOP'>\n";
	
			if( $_POST['method'] == 'startCSym') {
				echo " <B>EMAN Program: StartCSym</B><br><br>";
			} elseif ( $_POST['method'] == 'startIcos') {
				echo " <B>EMAN Program: StartIcos</B><br><br>";	
			} elseif ( $_POST['method'] == 'startOct') {
				echo " <B>EMAN Program: StartOct</B><br><br>";
			} elseif ( $_POST['method'] == 'startAny') {
				echo " <B>EMAN Program: StartAny</B><br><br>";
			} 
	
			echo"
				<b>Reference Free Class Information:</b> <br />
				Name & Path: $norefClassfile <br />
				Noref Class ID: $norefClassId<br />
				<br />";

			$particle = new particledata();
			$syms = $particle->getSymmetries();

		#Options to display for each EMAN method	
		if( $_POST['method'] == 'startCSym') {
			echo "
			
			<TR>
			<TD VALIGN='TOP' CLASS='tablebg'>
				<TABLE WIDTH='450' BORDER='0'>
					<TR><TD COLSPAN='2'>
						
						<B>Required Parameters:</B><br>
						<TR><td>Model Symmetry:</TD>
						
							<td><SELECT NAME='symm'>
      						<OPTION VALUE=''>Select One</OPTION>\n";
							foreach ($syms as $sym) {
								#if ($sym['symmetry']=='C1') {
								echo "<OPTION VALUE='".$sym['DEF_id']."'";
								if ($sym['DEF_id']==$_POST['symm']) echo " SELECTED";
								echo ">".$sym['symmetry'];
								if ($sym['symmetry']=='C1') echo " (no symmetry)";					
								echo "</OPTION>\n";
								#}
							}
    					echo" </SELECT>";
					
						echo "<TR><td>";   
						echo docpop('partnum','<b>Particle Number:</b> ');
						echo "</TD><td><input type='text' name='partnum' value='$partnum'> <br/>";  
						echo "<TR><td>";   
						echo docpop('lp','<b>Low Pass Filter:</b> ');
						echo "</TD><td><input type='text' name='lp' value='$lp'> <FONT SIZE='-2'> (in &Aring;ngstroms)</FONT><br/>";  
						echo "<TR><td>";
						echo "<B>Optional Parameters:</B><br>";
						echo "<TR><td>";
						echo docpop('imask','<b>Internal Mask:</b> ');
						echo "</TD><td><INPUT TYPE='text' name='imask' value='$imask'> <FONT SIZE='-2'>(in &Aring;ngstroms)</FONT><br/>";
						
		} elseif ( $_POST['method'] == 'startIcos') {
			echo "
			
				<TR>
				<TD VALIGN='TOP' CLASS='tablebg'>
					<TABLE WIDTH='450' BORDER='0'>
						<TR><TD COLSPAN='2'>
						
						<B>Required Parameters:</B><br>";							
						
			echo "<TR><td>";   
			echo docpop('partnum','<b>Particle Number:</b> ');
			echo "</TD><td><input type='text' name='partnum' value='$partnum'> <br/>";  
			echo "<TR><td>";
			echo docpop('lp','<b>Low Pass Filter:</b> ');
			echo "</TD><td><input type='text' name='lp' value='$lp'> <FONT SIZE='-2'> (in &Aring;ngstroms)</FONT><br/>";  
			echo "<TR><td>";
			echo "<B>Optional Parameters:</B><br>";
			echo "<TR><td>";
			echo docpop('imask','<b>Internal Mask:</b> ');
			echo "</TD><td><INPUT TYPE='text' name='imask' value='$imask'> <br/>";
			
		} elseif ( $_POST['method'] == 'startOct') {
			echo "
			
				<TR>
				<TD VALIGN='TOP' CLASS='tablebg'>
					<TABLE WIDTH='450' BORDER='0'>
						<TR><TD COLSPAN='2'>
						
						<B>Required Parameters:</B><br>";

			echo "<TR><td>";   
			echo docpop('lp','<b>Low Pass Filter:</b> ');
			echo "</TD><td><input type='text' name='lp' value='$lp'> <FONT SIZE='-2'> (in &Aring;ngstroms)</FONT><br/>";  			
			echo "<TR><td>";   
			echo docpop('partnum','<b>Particle Number:</b> ');
			echo "</TD><td><input type='text' name='partnum' value='$partnum'> <br/>";

		} elseif ( $_POST['method'] == 'startAny') {
			echo "
			
			<TR>
			<TD VALIGN='TOP' CLASS='tablebg'>
			<TABLE WIDTH='450' BORDER='0'>
				<TR><TD COLSPAN='2'>
						
					<B>Required Parameters:</B><br>
					<TR><td>Model Symmetry:</TD>
						
					<td><SELECT NAME='symm'>
      			<OPTION VALUE=''>Select One</OPTION>\n";
						foreach ($syms as $sym) {
							echo "<OPTION VALUE='".$sym['DEF_id']."'";
							if ($sym['DEF_id']==$_POST['symm']) echo " SELECTED";
							echo ">".$sym['symmetry'];
							if ($sym['symmetry']=='C1') echo " (no symmetry)";					
							echo "</OPTION>\n";
						}
    					echo" </SELECT>";
					
					echo "<TR><td>";   
					echo docpop('lp','<b>Low Pass Filter:</b> ');
					echo "</TD><td><input type='text' name='lp' value='$lp'> <FONT SIZE='-2'> (in &Aring;ngstroms)</FONT><br/>";  
					echo "<TR><td>";
					echo "<B>Optional Parameters:</B><br>";
					echo "<TR><td>";
					echo docpop('mask','<b>Mask:</b> ');
					echo "</TD><td><INPUT TYPE='text' name='mask' value='$mask'> <FONT SIZE='-2'>(in &Aring;ngstroms)</FONT><br/>";
					echo "<TR><td>";
					echo docpop('rounds','<b>Rounds:</b> ');
					echo "</TD><td><INPUT TYPE='text' name='rounds' value='$rounds'> <FONT SIZE='-2'>(2-5)</FONT><br/>";
		
	} else {

		###print error
	}

	echo "
												
		</table>
		</TD>
	  	</tr>
		
	   </table>
		</TD>
  		</tr>
  		<TR>
    	<TD ALIGN='CENTER'>
     		<HR>
     		<br>
     		<INPUT type='SUBMIT' name='process' value='Create Model'><br>
     		<FONT class='apcomment'>Submission will NOT create the model,<br>
				only output a command that you can copy and paste into a unix shell</FONT>
    	</TD>
		</tr>
  		</table>
  		</FORM>
  		</CENTER>\n";

}


#######################################################################################


function runCreateModel() {
	$expId = $_GET['expId'];

	$session=$_POST['session'];
	$method=$_POST['method'];
	$norefClassId=$_POST['norefClassId'];
	$norefId=$_POST['norefId'];
	$apix=$_POST['apix'];
	$outdir=$_POST['outdir'];
	$commit=$_POST['commit'];
	$exclude=$_POST['exclude'];
	$lp=$_POST['lp'];

	$command.="createModel.py ";

	$symmetry=$_POST['symm'];

	if ($symmetry) {
		$particle = new particledata();
		$syminfo = $particle->getSymInfo($symmetry);
		$symm_name = $syminfo['symmetry'];

		$symm_name_array=explode(" ",$symm_name);
		$symm_name = $symm_name_array[0];
	}

	if ($method == 'startCSym') {

		$particleNum=$_POST['partnum'];
		$imask=$_POST['imask'];

	} elseif ($method == 'startIcos') {

		$particleNum=$_POST['partnum'];
		$imask=$_POST['imask'];

	} elseif ($method == 'startOct') {
		
		$particleNum=$_POST['partnum'];

	} elseif ($method == 'startAny') {

		$mask=$_POST['mask'];
		$rounds=$_POST['rounds'];
	}


	//make sure a description is provided
	$description=$_POST['descript'];
	if (!$description) createSelectParameterForm("<B>ERROR:</B> Enter a brief description");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$procdir = $outdir.$runid;
 
	//putting together command
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--method=$method ";
	$command.="--session=$session ";
	$command.="--noref=$norefId ";
	$command.="--norefClass=$norefClassId ";
	$command.="--description=\"$description\" ";
	$command.="--lp=$lp ";
	$command.="--apix=$apix ";
	if ($exclude) $command.="--exclude=$exclude ";
	if ($symmetry) $command.="--symm=$symmetry,$symm_name ";
	if ($particleNum) $command.="--partnum=$particleNum ";
	if ($mask) $command.="--mask=$mask ";
	if ($imask) $command.="--imask=$imask ";
	if ($rounds) $command.="--rounds=$rounds ";
	

	if ($outdir) $command.="--rundir=$procdir ";
	$command.= ($commit=='on') ? "-C " : "--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Create Initial Model") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createEMANInitialModelForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'makestack');
		// if errors:
		if ($sub) createEMANInitialModelForm("<b>ERROR:</b> $sub");
		exit();
	}

	processing_header("Creating an Initial Model", "Creating an Initial Model");

	//rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>createModel.py command:</b><br />
	$command
	</td></tr>\n";
	echo "<tr><td>EMAN method</td><td>$method</td></tr>\n";
	echo "<tr><td>noref id</td><td>$norefId</td></tr>\n";
	echo "<tr><td>noref class id</td><td>$norefClassId</td></tr>\n";
	echo "<tr><td>description</td><td>$description</td></tr>\n";
	echo "<tr><td>outdir</td><td>$procdir</td></tr>\n";
	echo "<tr><td>apix</td><td>$apix</td></tr>\n";
	if ($exclude) echo "<tr><td>Excluded classes</td><td>$exclude</td></tr>\n";
	if ($symmetry) echo "<tr><td>Symmetry</td><td>$symmetry,$symm_name</td></tr>\n";
	if ($particleNum) echo "<tr><td>Particle Number</td><td>$particleNum</td></tr>\n";
	if ($mask) echo "<tr><td>Mask</td><td>$mask</td></tr>\n";
	if ($imask) echo "<tr><td>Internal mask</td><td>$imask</td></tr>\n";
	if ($rounds) echo "<tr><td>Rounds</td><td>$rounds</td></tr>\n";
	echo"</table>\n";
	processing_footer();
}

?>
