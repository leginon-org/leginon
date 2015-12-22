<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------
require_once "inc/processing.inc";
require_once "basicForm.inc";
require_once "inc/particledata.inc";
require_once "inc/forms/runParametersForm.inc";
require_once "inc/forms/remoteJobParamsForm.inc";


class BasicLayoutForm extends BasicForm
{
	protected $javaFunctions;
	protected $title;
	protected $heading;
	protected $errorHTML;
	protected $infoHTML;
	protected $outDir;
	protected $useLegOutDir; // Boolean, (default) False-> outDir is set to Appion directory, True-> outDir uses Leginon Directory
	protected $expId;
	protected $baseRunName; // Used to find the next run number to build the run name.
	protected $exeFile; // The name of the executable file that the parameters apply to. Usually a python file.
	protected $jobType; // jobtype is added to the command string and is needed for most Appion jobs.
	protected $guideURL; // The URL that links to an appropriate page in the online Appion User Guide.
	protected $testable; // Set to true if the form should include a test image input box.
	protected $showDesc; // If False (default), hides the run decription field, True shows it. 
	protected $useCluster; // If False (default),uses run parameters form, true uses remoteJobForm params.
	protected $showRemoteOutDir; // If False (default), hides the remoteRunDir field, True shows it if also useCluster is True.  
	// $enableLocalHost: If True, the local helper host used by cluster jobs to rsync data back to the local run dir is added 
	// to the command. If False (default), the localhost flag is not added to the command. This is getting to be a messy implementation.
	// Apologies. With more time I would create 2 different types of remote params forms.
	protected $enableLocalHost; 
	protected $logoImagePath;
	
	function __construct( $expId, $errorHTML='', $infoHTML='' ) 
	{
		parent::__construct();
		
		$this->setExpId( $expId );
		$this->setErrorHTML( $errorHTML );
		$this->setInfoHTML( $infoHTML );
		$this->addTestImageJava();
		$this->addPopupHelpJava();
		
		$params = $this->getFormParams();		
	}
	
	// Override this to output the html required to display program specific parameters
	// This html will be displayed in the grey column on the right hand side of the appion loop params
	public function generateAdditionalFormRight() { return False;}
	
	// Override this to output the html required to display program specific parameters
	// This html will be displayed directly below the appion loop params on the left hand side of the form
	// TODO: add this function to the generateForm() function when this class is used for something that uses it.

	public function generateAdvancedTableRight() { return False;}
	// Override this to output the html required to display program specific parameters
	// This html will be displayed directly below the program params on the right hand side of the form
	// TODO: add this function to the generateForm() function when this class is used for something that uses it.


	public function generateAdvancedFormRight() {
		// Only hide advanced parameters if there is not an advanced user logged in.
		// Modify user profile to set to an advanced user. 
		// NOTE: this assumes the Appion user name and the username that is used to log in to the processing page are the same.
		// We may want to change that someday.
		$advancedTableRight = $this->generateAdvancedTableRight();
		if ( !$advancedTableRight ) { return false; };

		$displayAdvanced = $_SESSION['advanced_user'];
		if ( !$displayAdvanced ) {
			$html.= "<a id='Advanced_Program_Options_toggle' href='javascript:toggle(\"Advanced_Program_Options\");' style='color:blue'>";
			$html.= "Show Advanced Options</a><br/>\n";
			$html.= "<div id='Advanced_Program_Options' style='display: none'>\n";
		} 
		//$html.= "<B>Advanced Options:</B><br />\n";
			$html .= $this->generateAdvancedTableRight();
		$html.= "<hr/>\n";
		$html.= "</div>\n";
	
		//
		// ENDING ADVANCED SECTION
		//
	
		return $html;
	}

	public function generateFormLogo() {
		if (file_exists($this->logoImagePath)) {
			$html .="<center><img src=$this->logoImagePath WIDTH='300'></center><br />\n";
		}
		return $html;
	}

	public function generateAdditionalFormLeft() {return False;}
	
	public function generateForm() 
	{
		//TODO: Don't like this direct echo from the function. Should make this a wrapper for a function that returns the guts.
		processing_header($this->title, $this->heading, $this->javaFunctions, True, True, False, $this->getGuideURL());	
		
		// check if coming directly from a session
		if ( $this->expId ) {
			$sessionId = $this->expId;
			$formClass = get_class($this);
			$formAction = $_SERVER['PHP_SELF']."?expId=$this->expId&form=$formClass";
		}	else {
			$sessionId = $_POST['sessionId'];
			$formAction = $_SERVER['PHP_SELF'];	
		}
		
		// Set the session path
		$projectId   = getProjectId();
		$sessiondata = getSessionList( $projectId, $sessionId );
		$sessioninfo = $sessiondata['info'];
		if (!empty($sessioninfo)) {
			$sessionname = $sessioninfo['Name'];
			$sessionpath = $sessioninfo['Image path'];

			// check for which session path to use [appion = false, leginon = true]
			if ( !$this->getUseLegOutDir() ) {
				$sessionpath = getBaseAppionPath($sessioninfo).'/'.$this->outDir;
			} else {
				$sessionpath = preg_replace("%rawdata%","",$sessionpath);		
			}
		}		
		
		// Set the default run name
		// the default run name is the baseRunName followed by an ever incrementing number
		$particle 		= new particledata();
		$lastrunnumber 	= $particle->getMaxRunNumber( $this->getJobType(), $this->expId ); 
		// sanity check - make certain we are not going to overwrite data
		$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
		$sessionpathval = (substr($sessionpathval, -1) == '/')? $sessionpathval : $sessionpathval.'/';
		
		while (file_exists($sessionpathval.$this->baseRunName.($lastrunnumber+1))) {
			$lastrunnumber += 1;
		}		
	    $defrunname = ($_POST['runname']) ? $_POST['runname'] : $this->baseRunName.($lastrunnumber+1);
		$outdir 	= $sessionpathval;
		
	    // Check the test image params
		$testcheck 		= ($_POST['testimage']=='on') ? 'CHECKED' : '';
		$testdisabled 	= ($_POST['testimage']=='on') ? '' : 'DISABLED';
		$testvalue 		= ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';
	
		$process = ($_POST['process']) ? $_POST['process'] :'';
		
		// create the main form and table
		$html .= "<form name='viewerform' method='POST' ACTION='$formAction'>\n";
		$html .= "<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";
		$html .= "<INPUT TYPE='HIDDEN' NAME='sessionpath' VALUE='$sessionpath'>\n";
		$html .= "<input type='hidden' name='sessionname' value='$sessionname'>\n";		
		// test command and results also show up here in a table.
		if ( !empty($this->infoHTML) ) {
			$html .= "<font color='BLACK' >$this->infoHTML</font>\n<hr/>\n";
		}
		// write out errors,in larger and red font if any came up.
		if ( !empty($this->errorHTML) ) {
			$html .= "<font color='#cc3333' size='+2'>$this->errorHTML</font>\n<hr/>\n";
		}
		
		$html .= "<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
				  <tr>
					<td VALIGN='TOP'>";
		
		$html .= $this->generateFormLogo();		
		$showDesc = $this->getShowDesc();
		if ($this->getUseCluster() ) {
			$remoteParamsForm = new RemoteJobParamsForm($defrunname, $outdir,'', $showDesc );
			$remoteParamsForm->setShowRemoteOutDir( $this->showRemoteOutDir );
			$html.= $remoteParamsForm->generateForm();
		} else {
			// Add the Run Parameters Form
			$runParamsForm = new RunParametersForm( $runname=$defrunname, $outdir=$outdir, $description='', $showDesc );
			$html .= $runParamsForm->generateForm();
		}
		
		$html .= $this->generateAdditionalFormLeft();		
		$html .= "</td>\n";

		// Add parameters specific to the method selected
		$formRight = $this->generateAdditionalFormRight();
		$formRightAdvanced = $this->generateAdvancedFormRight();
		if ( $formRight || $formRightAdvanced) {
			$html .= "<td class='tablebg' VALIGN='TOP'>\n";
			$html .= "<table cellpading='5' border='0'>\n";
			$html .= "<tr><td valign='top'>\n";
			$html .= $formRight;
			$html .= "</td>\n";
			$html .= "</tr>\n";
			$html .= "<tr><td valign='top'>\n";
			$html .= $formRightAdvanced;
			$html .= "</td>\n";
			$html .= "</tr>\n";
			$html .= "</table>\n";
			$html .= "</td>\n";
		}
		$html .= "</tr>\n";
		
		// Add the test image input box
		if ( $this->getTestable() ) {
			$html .= "
				<tr>
					<td COLSPAN='2' ALIGN='CENTER'>
						<HR>
						<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
							Test these settings on image:
						<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
						<hr>
					</td>
				</tr>";
		} else {
			$html .= "<tr><td COLSPAN='2'><HR></td></tr>\n";
		}
		
		// Add the submit buttons
		// TODO: should we pass false to getSubmitForm if using cluster params instead of runParams?
		$html .= "<tr><td COLSPAN='2' ALIGN='CENTER'>";
		// if we are using the remoteJob form, do not include the host here
		$includeHost = !$this->useCluster;
		$html .= getSubmitForm("Run Command", $includeHost);
		$html .= "</td></tr>";
		
		// Add any publication references for this method
		$html .= "<tr><td COLSPAN='2' ALIGN='CENTER'>";
		$html .= $this->showReference();
		$html .= "</td></tr>";
		
		// Close up the form
		$html .= "</table></form>";
		$html .= processing_footer();

		return $html;
	}	
	
	function addJavaScript( $javaFunctions ) 
	{
		$this->javaFunctions .= $javaFunctions;
	}
	function setTitle( $title )
	{
		$this->title = $title;
	}
	function setHeading( $heading )
	{
		$this->heading = $heading;
	}
	function setErrorHTML( $errorHTML )
	{
		$this->errorHTML = $errorHTML;
	}
	function setInfoHTML( $infoHTML )
	{
		$this->infoHTML = $infoHTML;
	}
	function setExpId( $expId )
	{
		$this->expId = $expId;
	}
	function setOutputDirectory( $outDir )
	{
		$this->outDir = $outDir;
	}
	function setBaseRunName( $baseRunName )
	{
		$this->baseRunName = $baseRunName;
	}
	function setExeFile( $exeFile )
	{
		$this->exeFile = $exeFile;
	}
	function setJobType( $jobType )
	{
		$this->jobType = $jobType;
	}
	function getJobType()
	{
		return $this->jobType;
	}
	function setGuideURL( $guideURL )
	{
		$this->guideURL = $guideURL;
	}
	function getGuideURL()
	{
		// If the guide URL has not been set, use the main guide menu page.
		if ( empty($this->guideURL) ){
			$this->setGuideURL("http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing");
		}
		return $this->guideURL;
	}
	function setTestable( $testable )
	{
		$this->testable = $testable;
	}
	function getTestable()
	{
		// If the guide URL has not been set, use the main guide menu page.
		if ( empty($this->testable) ){
			$this->setTestable(False);
		}
		return $this->testable;
	}
	// Boolean, (default) False-> outDir is set to Appion directory, True-> outDir uses Leginon Directory
	function setUseLegOutDir( $useLegOutDir )
	{
		$this->useLegOutDir = $useLegOutDir;
	}
	function getuseLegOutDir()
	{
		if ( empty($this->useLegOutDir) ){
			$this->setUseLegOutDir(False);
		}
		return $this->useLegOutDir;
	}
	function setShowDesc( $showDesc )
	{
		$this->showDesc = $showDesc;
	}
	function getShowDesc()
	{
		// Default showDesc to False.
		if ( empty($this->showDesc) ){
			$this->setShowDesc(False);
		}
		return $this->showDesc;
	}
	function setUseCluster( $useCluster )
	{
		$this->useCluster = $useCluster;
	}
	function getUseCluster()
	{
		// Default useCluster to False.
		if ( empty($this->useCluster) ){
			$this->setUseCluster(False);
		}
		return $this->useCluster;
	}
	function setShowRemoteOutDir( $showRemoteOutDir )
	{
		$this->showRemoteOutDir = $showRemoteOutDir;
	}
	function getShowRemoteOutDir()
	{
		// Default showDesc to False.
		if ( empty($this->showRemoteOutDir) ){
			$this->setShowRemoteOutDir(False);
		}
		return $this->showRemoteOutDir;
	}
	function setEnableLocalHost( $enableLocalHost )
	{
		$this->enableLocalHost = $enableLocalHost;
	}
	function getEnableLocalHost()
	{
		// Default showDesc to False.
		if ( empty($this->enableLocalHost) ){
			$this->setEnableLocalHost(False);
		}
		return $this->enableLocalHost;
	}
	function addTestImageJava()
	{
		$javafunctions ="
			<script src='../js/viewer.js'></script>
			<script LANGUAGE='JavaScript'>
				function enabledtest(){
					if (document.viewerform.testimage.checked){
						document.viewerform.testfilename.disabled=false;
						document.viewerform.testfilename.value='';
						document.viewerform.commit.disabled=true;
						document.viewerform.commit.checked=false;
					}	else {
						document.viewerform.testfilename.disabled=true;
						document.viewerform.testfilename.value='mrc file name';
						document.viewerform.commit.disabled=false;
						document.viewerform.commit.checked=true;
					}
				}
			</script>\n";
		$this->addJavaScript( $javafunctions );
	}
	
	function addPopupHelpJava()
	{	
		$javaFunction = writeJavaPopupFunctions('appion');
		$this->addJavaScript( $javaFunction );
	}
	
	// Override the validate function so that we can verify the appionLoopTable parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		if ($this->getUseCluster()) {
			$remoteParamsForm = new RemoteJobParamsForm($this->outDir);
			$msg .= $remoteParamsForm->validate( $postArray );
		} else {
			$runParametersForm = new RunParametersForm();
			$msg .= $runParametersForm->validate( $postArray );
		}
		
		return $msg;
	}
	
	// Override buildCommand so that we can call it from AppionLoopTable
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		if ( $this->getUseCluster() ) {
			$remoteParamsForm = new RemoteJobParamsForm( $this->outDir );
			$enableLocalHost = $this->getEnableLocalHost();
			$remoteParamsForm->setEnableLocalHost( $enableLocalHost );
			$command .= $remoteParamsForm->buildCommand( $postArray );
		} else {
			// add params from run parameters form
			$runParametersForm = new RunParametersForm();
			$command .= $runParametersForm->buildCommand( $postArray );
		}

		// add the executable file to the front of the command
		$command = $this->exeFile . " " . $command;
		
		return $command;		
	}

	static public function getTestCommand( $command )
	{
		$wrappedcmd = addAppionWrapper($command);
		
		$html = "<table width='600' border='0'>\n";
		$html.= "<tr><td>\n";
		$html.= "<B>Test Command:</B><br />$wrappedcmd";
		$html.= "</td></tr>\n";
		$html.= "<tr><td>\n";
		# Refresh Test Results avoids resubmit to cluster that would rerun the test
		$html.= "<input type='submit' name='process' value='Refresh Test Results' onclick='pleasewait()'>\n";
		$html.= "</td></tr></table>\n";
		$html.= "<br />\n";

		return $html;
	}
	
	// Override this function if your program can test a single image.
	// getTestResults() should return the HTML code needed to display test results any way this method
	// prefers to have them displayed. The results will be placed below a printout of the test command and 
	// above the launch form. 
	static public function getTestResults( $outdir, $runname, $testfilename )
	{
		// Tell the users what to do if the test results are not found.
		$html .=  "<FONT COLOR='RED'><B>Currently, code has not been written to display test results to the browser.</B><br></FONT>";
		$html .=  "<FONT COLOR='RED'><B>You may try viewing results directly in the run directory.</B><br></FONT>";
		
		return $html;
	}	
	
}

?>
