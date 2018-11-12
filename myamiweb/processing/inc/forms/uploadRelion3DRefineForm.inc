<?php

/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values
require_once "inc/processing.inc";

class uploadRelion3DRefineForm extends BasicLayoutForm
{
	protected $stackIds;

	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='', $commit='on',$recenter=True, $session='')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('relion'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display

		$this->setJobType( 'uploadparticles' ); //Job type stored in database
		$this->setOutputDirectory( 'extract' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'relion3drefine' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Upload Relion 3D Refine' ); // Shows up in the browser tab
		$this->setHeading( 'Upload Relion 3D Refine' ); // shows at the top of the processing page
		$this->setExeFile( 'uploadRelion3DRefine.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False ); // Shows the processing host params to set processors and memory

		$params = $this->getFormParams();
		$params->addParam( "commit", $commit, "Commit to Database" );
		$params->addParam( "starfile", $starfile, "Relion 3D auto-refine run_data.star with path " );
		$params->addParam( "recenter", $recenter, "Recenter particles based on shifts during Relion 3D auto-refine" );
		$params->addParam( "noinsert", $noinsert, "Do not insert final particle picks from Relion 3D auto-refine" );
		$params->addParam( "session", $session, "Session name" );


	}

	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 15;

		$html .= "<H4>Upload parameters</H4><hr />";

		$html .= $params->insertTextField( "starfile", $fieldSize, '', 'uploadRelion3DRefine.starfile' );
		$html .= $params->insertCheckboxField( "recenter",'', 'uploadRelion3DRefine.recenter' );
		$html .= $params->insertCheckboxField( "noinsert",'', 'uploadRelion3DRefine.noinsert' );
		$html .= $params->insertCheckboxField("commit");


		return $html;
	}


	// Override the buildCommand function to adapt to the old python command
	// that uses "-" in params and parse the stack id.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		$params = $this->getFormParams();

		$sessionname=$_POST['sessionname'];
		var_dump($sessionname);
		$command.= " --session=$sessionname ";
		
		// If the commit box is checked, add --commit, otherwise --no-commit
		$commit  = ($params->getParamValue('commit') == 'on' ) ? true : false;
		if (!$commit) {
			$command.= " --no-commit ";
		}

		return $command;
	}

	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );

		$params = $this->getFormParams();
		if ($params->getParamValue('starfile') == '' ){
			$msg .= '<B>Error: enter path of star file.</B>';
		}
		return $msg;
	}
}
?>
