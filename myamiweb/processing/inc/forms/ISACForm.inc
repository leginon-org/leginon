
<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "basicLoopForm.inc";


class ISACForm extends BasicLoopForm 
{
	function __construct(  $expId)
	{
		parent::__construct($expId);
	
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
	
		// Set the publications to be references on the web pages
		$pubList = array('isac');
		$this->setPublications( $pubList );
		$this->setJobType( 'isac' );
		$this->setOutputDirectory( 'isac' );
		$this->setBaseRunName( 'isac' );
		$this->setTitle( 'isac.py Launcher' );
		$this->setHeading( 'Create a Direct Detector Frame Stack' );
		$this->setExeFile( 'isac.py' );
		$this->setGuideURL( "http://ami.scripps.edu/redmine/projects/appion/wiki/ISAC_Iterative_Stable_Alignment_and_Clustering" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
	
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
	
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "makeDDStack" );
	
		$params->addParam( "align", $align, "align" );
		$params->addParam( "defergpu", $defergpu, "defer gpu processing" );
		$params->addParam( "bin", $bin, "binning" );
		$params->addParam( "no_keepstack", $nokeepstack, "remove generated stack after uploading aligned sum image" );
		$params->addParam( "ddstartframe", $ddstartframe, "start frame" );
		$params->addParam( "ddnframe", $ddnframe, "total frames" );
	
		// Validations
		//$params->addValidation( "numpart", "req" );
	}
	
	
	// This function returns the html code that defines the GUI layout of this method's parameters. 
	// It is called from the BasicRefineForm class which places this html in an appropriate location on the screen.
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// This help section key corresponds to the section in help.js that defines
		// help messages for this piece of the GUI.
		$params->setHelpSection( "isac" );		
		
		$fieldSize = 3;
		
		$html .= "<b>ISAC Options</b><br/>\n";
		$html .= $params->insertCheckboxField( "ctf" );
		$html .= $params->insertCheckboxField( "ctf_corrected_ref" );		
		$html .= $params->insertTextField( "ini_high", $fieldSize, "(&Aring;ngstroms)" );
		$html .= "<br/>\n";
		
		
		$html .= "<b>Advanced Relion Options</b><br/>\n";
		$html .= $params->insertCheckboxField( "ctf_intact_first_peak" );
		$html .= $params->insertTextField( "offset_range", $fieldSize, "(pix)" );
		$html .= $params->insertTextField( "offset_step", $fieldSize, "(pix)" );
		$healpixOptions = array(30, 15, 7.5, 3.5, 1.8, 0.9, 0.5, 0.2, 0.1);
		$healpixOptions = array_combine( $healpixOptions, $healpixOptions ); //need a dict with key and value set to degrees
		$html .= $params->insertSelectField( "healpix_order", $healpixOptions, "(degrees)" );
		$html .= $params->insertSelectField( "auto_local_healpix_order", $healpixOptions, "(degrees)" );
		$html .= "<br/>\n";	
		
		return $html;
	}
	
	
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults()
	{
		$stack = $this->getStackInfo();
		$box = $stack['boxsize'];
		$apix = $stack['apix'];
		$sym = $this->getSymmetry();
		
		// There are different default values for icosohedral symmetries
		if ( stripos($sym, "icos") ) {
			$healpix_order = 3.7;
			$auto_local_healpix_order = 0.9;
		} else {
			$healpix_order = 7.5;
			$auto_local_healpix_order = 1.8;
		}
		
		$radPix = ($box/2)-2;
		$radAng = round($radPix * $apix);
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $radAng;
	      if (obj.symmetry) obj.symmetry.value = '$sym';
	      if (obj.ctf) obj.ctf.checked = true;
	      if (obj.ctf_intact_first_peak) obj.ctf_intact_first_peak.checked = false;
	      if (obj.ctf_corrected_ref) obj.ctf_corrected_ref.checked = false;
	      if (obj.ini_high) obj.ini_high.value = '60';
	      if (obj.healpix_order) obj.healpix_order.value = $healpix_order;
	      if (obj.auto_local_healpix_order) obj.auto_local_healpix_order.value = $auto_local_healpix_order;
	      if (obj.offset_range) obj.offset_range.value = '5';
	      if (obj.offset_step ) obj.offset_step.value = '1';

	      return;
	    }
	  </script>\n";
		return $javafunc;
	}	

	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		
		// endIter is always 1 for relion
		$command .= " --endIter=1 ";
		
		return $command;
	}
} // End of ISAC Form class

?>
