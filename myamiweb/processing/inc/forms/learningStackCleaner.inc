<?php

/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up stack list
require_once "inc/summarytables.inc"; // needed to create stack form

class LearningStackCleaner extends BasicLayoutForm
{
	protected $stackIds;

	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='',$stackId='' ,$commit='on'
		)
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('appion'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display

		$this->setJobType( 'makestack' ); //Job type stored in database
		$this->setOutputDirectory( 'stacks' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'learnstack' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Learning Stack Cleaner Launcher' ); // Shows up in the browser tab
		$this->setHeading( 'Learning Stack Cleaner' ); // shows at the top of the processing page
		$this->setExeFile( 'runLearnStackCleaner.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/LaerningStackCleaner" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False ); // Shows the processing host params to set processors and memory
		
		//------ Set Parameters specific to the program that requires this new form -----//

		$particle = new particledata();
		$this->stackIds = $particle->getStackIds($expId);

		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "stackid", $stackId, "Select a stack of particles to use" );

	}

	public function generateForm() {
		// get parent pre-form elements
		$html  .= parent::generateForm();
		if ($_GET['stackId']) {
			$formClass = get_class($this);
			$formAction = $_SERVER['PHP_SELF']."?expId=$this->expId&form=$formClass";
		}
		return $html;
		
	}
	
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		if (!$this->stackIds) {
			$html = "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} elseif ($_GET['stackId']) {
			$stackid = $_GET['stackId'];
			$html = ministacksummarytable($stackid);
			$html .= "<form type='hidden' name='stackid' value='$stackid'>\n";
		} else {
			$particle 	= new particledata();
			$options 	= $particle->getStackOptions($this->stackIds);
			$html 		= $params->insertStackedSelectField( "stackid", $options, '', '', '' );
		}

		$html .= "<br />";

		return $html;
	}
}
?>
