<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------
require_once "../inc/formParameters.inc";
require_once "inc/publication.inc";


class BasicForm
{
	protected $defaultParamSets; 	// an array of parameter sets of type RefineFormParameters used for populating forms
	protected $formParams; 			// the current user selected or modified parameter set
	protected $pubKeyList;
	protected $filesToCopy;			// an array of filenames that should be copied to remote rundir
	
	function __construct() 
	{
		$this->formParams = $this->createFormParams();
		$this->setPublications();
		$this->setLogoImagePath();
	}	
	
	function __destruct() 
	{
		unset( $this->formParams );
		unset( $this->defaultParamSets );
		unset( $this->pubKeyList );
		unset( $this->logoImagePath );
	}
	
	// extending classes should use this to set the 
	// publication key list with key values that have been added 
	// to the array in publicationList.inc
	protected function setPublications($pubList='')
	{
		// Provide a default publication reference
		if ( $pubList === '' ) {
			$pubList = array("appion");
		}
		$this->pubKeyList = $pubList;
	}
	
	// Returns the HTML to display the references boxes for the publications associated with this Form.
	// Publications are set with setPublications().
	public function showReference()
	{
		foreach ( $this->pubKeyList as $pubKey ) {
			$pub = new Publication($pubKey);
			$html .= $pub->getHtmlTable();
		}
		
		return $html;
	}
	
	// extending classes should use this to set the 
	// logo image path relative to processing directory 
	// for example, 'img/dogpicker.jpg'
	protected function setLogoImagePath($relative_path='')
	{
		$this->logoImagePath = $relative_path;
	}
	
	// Override this function if your form needs to copy files to a remote server
	// Files should be in the local rundir and will be copied to the remote run dir.
	// This is called by copyFilesToCluster which is called by runAppionLoop.php.
	public function setFilesToCopy()
	{
		$this->filesToCopy = '';
	}
	
	// Copies any files to the cluster that may be needed. If the copy fails, returns a 
	// command the user can run to execute the copy manually. If the copy is successful,
	// this should return an empty string.
	// This is called by runAppionLoop.php. Returns empty string if no files are set to copy.
	public function copyFilesToCluster( $host, $directory )
	{
		$this->setFilesToCopy();
		if ( !$this->filesToCopy ) return "";
		
		$copyNeededFlag		= false; // this becomes true if files actually need to be copied 
		$printCommandFlag 	= false; // this becomes true if we are unable to execute the copy
		$returnCmdString	= ""; // the commands the user needs to enter manually if auto copy fails
		$clusterpath		= $directory;
			
		// if the user is not logged in, we cannot execute the copy for them
		$user = $_SESSION['username'];
		$pass = $_SESSION['password'];
		if (!($user && $pass)) {
			$printCommandFlag = true;
		}
	
		$runname = $_POST['runname'];
		$rundir = $_POST['outdir'].$runname;
		$clusterpath = $clusterpath.$runname;
		
		// create appion directory & copy list of files to copy
		// TODO: where exactly should files be copied to?
		$mkdircmd = "mkdir -p $clusterpath;\n";
		
		if ( !$printCommandFlag ) {
			$rvalue = exec_over_ssh($host, $user, $pass, $mkdircmd, false);
			if ($rvalue === false ){
				// if the mkdir failed, display the commands to the user to run manually
				$printCommandFlag = true;
				$errMsg = "Error: Could not create run directory on $host: ";
				$errMsg .= pconnError();
				$returnCmdString .= "<B>ERROR</B> $errMsg <br /><br />";
				//echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
			} else {
				// TODO: log this to a file
				//echo "<hr>\n<font color='#CC3333' size='+1'>Created run directory $clusterpath on $host.</font>\n";
			}
		}
		
		foreach ( $this->filesToCopy as $filepath ) {
			if ( !$filename ) {
				//echo "<hr>\n<font color='#CC3333' size='+1'>$filename not valid.</font>\n";
				continue;
			}
			
			// add the path to the current location of the file
			$filepath = $rundir."/".$filename;
			
		    // set path to copy the file to
		    $remoteFilePath = "$clusterpath/$filename";
		    	    
		    // copy the file to the cluster
		    if ( $filepath != $remoteFilePath ) {
		    	$copyNeededFlag = true;
		    	$cpycmd .= " cp $filepath $remoteFilePath; <br />";
		    	// if we have not had any errors above, try the copy
		    	if ( !$printCommandFlag ) {
		    		$rvalue = scp($host, $user, $pass, $filepath, $remoteFilePath);	
					if (!$rvalue) {
						// if there is an error with the copy, let the user know and display the manual commands
						$printCommandFlag = true;
						$errMsg = "Failed to copy file ($filepath) to $remoteFilePath on $host: ";
						$errMsg .= pconnError();
						$returnCmdString .= "<B>ERROR</B> $errMsg <br /><br />";
						//echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
					} else {
						// TODO: log this to a file
						//echo "<hr>\n<font color='#CC3333' size='+1'>Copied $filepath to $remoteFilePath on $host.</font>\n";
					}
		    	}
		    } else {
		    	// TODO: log this to a file
				//echo "<hr>\n<font color='#CC3333' size='+1'>No need to copy file $filepath to $remoteFilePath.</font>\n";
		    }
		}	
		
		// Build the return string if needed
		if ( $copyNeededFlag && $printCommandFlag ) {
			$returnCmdString .= "<b>You MUST manually execute the following commands (or similar) prior to running the refinement command:</b>";
			$returnCmdString .= "<br /><br />";
			$returnCmdString .= $mkdircmd;
			$returnCmdString .= "<br />";
			$returnCmdString .= $cpycmd;
		}
		
		return $returnCmdString;
	}
		
	// Extending classes should override this function to return the appropriate
	// class of form parameters if it has also extended the FormParameters class.
	// This createFormParams() function should always be used instead of 
	// directly creating an instance of FormParameters.
	// GOOD: $formParams = $this->createFormParams();
	// BAD:  $formParams = new FormParameters();
	public function createFormParams( $id='', $label='' ) 
	{ 
		return new FormParameters( $id, $label ); 
	}
			
	// adds a set of default values to the "Import Parameters"
	// drop dowm list.
	final protected function addDefaultParams( $newSet )
	{
		$this->defaultParamSets[$newSet->id] = $newSet;
	}
	
	// points the form parameters to the correct set of default
	// values based on the users selection.
	// Takes the default set Id, which corresponds to a set available
	// in the "Import Parameters" drop down list.	
	protected function updateFormParams( $defaultSetId='' )
	{
		if ( isset( $this->defaultParamSets[$defaultSetId] ) ) {
			// the user just selected an existing set of params to import
			$this->formParams = $this->defaultParamSets[$defaultSetId];			
		} else {
			// the form may be refreshing after posting an error, make sure to get any previous values from the POST array
			$this->formParams->getPostedValues($_POST);
		}
	}
	
	// returns an array of all form parameters
	// with the currently set values
	final protected function &getFormParams()
	{
		return $this->formParams;
	}
	
	// returns an array of all form parameters
	// with the currently set values
	final protected function getDefaultParamSets()
	{
		return $this->defaultParamSets;
	}

	// use this function in the form constructor
	// to completely hide the parameter in the form.	
	public function hideParam( $name )
	{
		$this->formParams->hideParam( $name );
	}
		
	public function disableAllParams()
	{
		$this->formParams->disableAllParams();
	}
	
	public function generateForm() {}
	
	public function generateReport( $title="", $width=650 )
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->updateFormParams();
		$params = $this->getFormParams();		
		$paramArray = $params->getParamArray();

		// Add a rounded border table
		$html.= "<table border='0' cellpadding='2' cellspacing='2' >\n";
		//$html.= "<tr><td>\n";
		//$html.= openRoundBorder();
		//$html.= "<table border='0' cellpadding='4' cellspacing='4'>\n";
		
		// Add title
		if ( $title ) {
			$html.= "<tr>\n";
			$html.= "<td colspan='2'>\n";
			$html.= "<h4>".$title."</h4>\n";
			$html.= "</td>\n";
			$html.= "</tr>\n";
		}
		
		// Add each parameter's label and value
		foreach ( $paramArray as $key=>$param ) {
			$html.= "<tr><td><b>".$param['label'].":</b></td><td>".$param['value']."</td></tr>\n";
			// Since just displaying the values does not add them to the post array, 
			// post them here so we can still add them to a command later 
			$html.= "<input type='hidden' NAME='".$param['name']."' value='".$param['value']."'>\n";
		}

		// Close the table
		$html.= "</table>\n";
		//$html.= closeRoundBorder();
		//$html.= "</td></tr>\n";
		//$html.= "</table>\n";
		
		$html.= "<br/>\n";

		return $html;
	}
	
	
	// A generic default implementation that will add
	// a flag to a command string for every parameter 
	// defined by the form in format --<name>=<value>
	public function buildCommand( $postArray )
	{
		$this->formParams->getPostedValues( $postArray );
		$paramArray = $this->formParams->getParamArray();
				
		// If the form does purely composite and does not define any params of its own,
		// the param array will be null.
		if ( $paramArray ) {
			foreach ( $paramArray as $key=>$param ) {
				$command = $this->addCommandFlag( $command, $param['name'] );
			}
		}
		
		return $command;
	}
	
	// Appends a new command flag to a command string
	// If value is not passed, the param value is looked up.
	// If $paramName is not passed, it is assumed to be the same 
	// as the flag name.
	// If the value is an empty string, it is not added to the command.
	// Returns the new command string.
	function addCommandFlag( $command, $flagName, $paramName='', $value='' )
	{
		if ( $paramName == '' ) {
			$paramName = $flagName;
		}
		if ( $value === '' ) {
			$value = $this->formParams->getParamValue( $paramName );
		}
		if ( $value !== '' ) {
			// if the value is 'on' it is just a flag, with no value specified
			if ( $value == 'on') {
				$command .= "--".$flagName." ";
			} else {
				$command .= "--".$flagName."=".$value." ";
			}
		}
		
		return $command;
	}
	
	// remove a specific flag from a command string
	function removeCommandFlag( $command, $flagName, $paramName='', $value='' )
	{
		if ( $paramName == '' ) {
			$paramName = $flagName;
		}
		if ( $value === '' ) {
			$value = $this->formParams->getParamValue( $paramName );
		}
		if ( $value !== '' ) {
			// if the value is 'on' it is just a flag, with no value specified
			if ( $value == 'on') $flagString = "--".$flagName;
			else $flagString = "--".$flagName."=".$value." ";
			$command = str_replace( $flagString,"", $command );
		}
		
		return $command;
	}
	
	public function validate( $postArray )
	{
		$this->formParams->getPostedValues( $postArray );
		$msg = $this->formParams->validate();
		
		return $msg;
	}
}

?>
