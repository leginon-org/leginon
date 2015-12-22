<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";
require_once "inc/particledata.inc";
require_once "inc/processing.inc";

// Filter Table parameters corresponds to appionlib/filterLoop.py
class FilterTable extends BasicForm
{

	function __construct( $lpv=15, $hpv=0, $medianv= 2, $pixlimitv=4, $binv=4,
	$invertv='',$planeregv='on' )
	{
		parent::__construct();
		
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		//Filter Values
		$params->addParam( "lpval", $lpv, "Low Pass" );
		$params->addValidation("lpval", "num");
		$params->addParam( "hpval", $hpv, "High Pass" );
		$params->addValidation("hpval", "num");
		$params->addParam( "medianval", $medianv, "Median" );
		$params->addValidation("medianval", "num");
		$params->addParam( "pixlimit", $pixlimitv, "Pixel Limit" );
		$params->addValidation("pixlimit", "float");
		$params->addParam( "binval", $binv, "Binning" );
		$params->addValidation("binval", "num");
		$params->addParam( "planereg", $planeregv, "Plane regression" );

		$params->addParam( "invert", $invertv, "Invert image density" );		
		//keepall is not set in gui
	}
			
	public function generateForm()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html.=  "<!-- BEGIN FilterLoop Param -->\n";

		// Binning
		$html.= $params->insertTextField( "binval", $fieldSize,"(power of 2)" );	
		$html.= "<hr/>\n";

		// Filter
		$html.= "<B>Filter Values:</B><br />\n";
		$html.= $params->insertTextField( "lpval", $fieldSize,"(in &Aring;ngstroms; 0 = off)" );	
		$html.= $params->insertTextField( "hpval", $fieldSize,"(in &Aring;ngstroms; 0 = off)" );	
		$html.= $params->insertTextField( "medianval", $fieldSize,"(in pixels; 0= off)" );	
		$html.= $params->insertTextField( "pixlimit", $fieldSize,"(in Standard Deviations; 0 = off)" );	
		$html.= $params->insertCheckboxField( "planereg" );
		$html.= "<br/>\n";
		$html.= "<B>Image Contrast:</B><br />\n";
		$html.= $params->insertCheckboxField( "invert" );
		$html.= "<br/>\n";
		$html.=  "<!-- END FilterLoop Param -->\n";

		return $html;	
	}	
	// No need to override the buildCommand
	
	// Non need to override the validate function
	
}

// Advanced Table parameters corresponds to appionlib/filterLoop.py
class MathParticleAdvancedTable extends BasicForm
{

	function __construct( 
	$peaktypev='centerofmass', $nojpegsv='', $doublesv='', $maxsizev='1.0', 
		$overlapmultv='1.5' )
	{
		parent::__construct();
		
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		//Peakfinding parameters
		$params->addParam( "peaktype", $peaktypev, "Peak extraction type" );
		$params->addParam( "nojpegs", $nojpegsv, "Do NOT create summary peak pairs" );
		$params->addParam( "doubles", $doublesv, "Pick only doubles" );
		$params->addParam( "maxsize", $maxsizev, "Maximum peak area multiple" );
		$params->addParam( "overlapmult", $overlapmultv, "Minimum peak overlap distance multiple" );
	}
			
	public function generateForm()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html.=  "<!-- BEGIN PeakType Param -->\n";

		$html.= "<B>Peak extraction type:</B><br />\n";
		$html.= $params->insertRadioField("peaktype", "centerofmass", "Center of mass","(default)");	
		$html.= $params->insertRadioField("peaktype", "maximum", "Maximum position");	

		$html.=  "<!-- END PeakType Param -->\n";
		$html.= "<br/>\n";
		$html.= $params->insertCheckboxField( "nojpegs" );
		$html.= $params->insertCheckboxField( "doubles" );
		$html .= $params->insertTextField( "maxsize", $fieldSize );
		$html .= $params->insertTextField( "overlapmult", $fieldSize );

		return $html;	
	}	
	// Override the buildCommand
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		$params = $this->getFormParams();

		$maxsize = $params->getParamValue('maxsize');
		if ($params->getParamValue('maxsize') && $maxsize > 0 && $maxsize != 1.0) $command.=" --maxsize=$maxsize";
		if ($overlapmult && $overlapmult > 0 && $overlapmult != 1.5) $command.=" --overlapmult=$overlapmult";
	
		return $command." ";
	}

	// Non need to override the validate function
	
}

class ParticleDiameterTable extends BasicForm
{

	function __construct( $pdiamv='' )
	{
		parent::__construct();

		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
	
		$params->setHelpSection( "appion" );

		$params->addParam( "pdiam", $pdiamv, "Particle diameter for filtering" );
		$params->addValidation("pdiam", "req");
	}
	
	public function generateForm()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html .= "<b>Particle Diameter:</b><br />\n";
		
		#$html.= $params->insertCheckboxField( "no_keepstack" );
		$html.= $params->insertTextField( "pdiam", $fieldSize,"(in &Aring;ngstroms)" );
	
		$html.= "<br/>\n";
		
		return $html;
	}	
}

class HelicalTable extends BasicForm
{

	function __construct( $helix='', $helicalstepv='',$ovrlpv=0  )
	{
		parent::__construct();

		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
	
		$params->setHelpSection( "appion" );

		$params->addParam( "helix", $helixv, "Pick along helices" );
		$params->addParam( "helicalstep", $helicalstepv, "Stepsize for Helical Insert" );
		$params->addValidation("helicalstep", "num");
		$params->addValidation("helicalstep", "exclude=helix");
		$params->addParam( "ovrlp", $ovrlpv, "Percent overlap" );
		$params->addValidation("ovrlp", "num");
	}
	
	public function generateForm()
	{
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html .= "<b>Helical Parameters:</b><br />\n";
		
		$html.= $params->insertCheckboxField( "helix" );
		$html .= "OR pick helix end points with these:<br />";
		$html.= $params->insertTextField( "helicalstep", $fieldSize,"(in &Aring;ngstroms)" );
		$html.= $params->insertTextField( "ovrlp", $fieldSize,"(%)" );
	
		$html.= "<br/>\n";
		
		return $html;
	}	

	public function buildCommand( $postArray )
	{
		$this->formParams->getPostedValues( $postArray );

		$params = $this->getFormParams();
		$helixv = $params->getParamValue('helix');

		if ( $helixv ) {
			$command = '--helix ';
		} else {
			if (isset($postArray['helicalstep']) && strlen($postArray['helicalstep']) )
			$command = '--helicalstep='.$postArray['helicalstep'].' ';
			$command .= '--ovrlp='.$postArray['ovrlp'].' ';
		}
		return $command;
	}

}

class ManualTable extends BasicForm
{

	function __construct( $shapev='plus', $shapesizev=0 )
	{
		parent::__construct();

		$this->shapeList = array('plus'=>'plus','circle'=>'circle','cross'=>'cross','point'=>'point','diamond'=>'diamond');

		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
	
		$params->setHelpSection( "appion" );

		//Single slice
		$params->addParam( "shape", $shapev, "Picking icon shape" );
		$params->addParam( "shapesize", $shapesizev, "Picking icon diameter" );
		$params->addValidation("shapesize", "num");
	}
	
	public function generateForm()
	{
		$params = $this->getFormParams();
		$fieldSize = 3;
		// Add the ManualPicker Form
		$html.=  "<!-- BEGIN Manual Picker Param -->\n";

		$html.= "<B>Picking Icon:</B><br />\n";
		$html.= "<I>(only for visual purposes, does not affect data):</I><br />\n";
		$html.= $params->insertSelectField( "shape", $this->shapeList );
		$html.= $params->insertTextField( "shapesize", $fieldSize,"(in pixels; 0= auto)" );	
		$html.= "<br /><br/>\n";
		$html.=  "<!-- End Manual Picker Param -->\n";
		
		$html.= parent::generateForm();
		return $html;
	}	

}

// Simple Particle Table parameters not involving mathmatical pickers
class SimpleParticleTable extends FilterTable
{

	function __construct( $defocpairv='' )
	{
		parent::__construct();
		
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		// Defocal pairs
		$params->addParam( "defocpair", $defocpairv, "Calculate shifts for defocal pairs" );
	}
			
	public function generateForm( )
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html.= parent::generateForm();

		$html.=  "<!-- BEGIN Simple Particle Param -->\n";
		$html.= "<B>Defocal pairs:</B><br />\n";
		$html.= $params->insertCheckboxField( "defocpair" );
		$html.= "</div>\n";
		$html.= "<br/>\n";
		$html.=  "<!-- END Simple Particle Param -->\n";

		return $html;	
	}	
	// No need to override the buildCommand
	
	// Non need to override the validate function
	
}



// Auto Pick Table parameters for template and dogpickers
class MathParticleTable extends BasicForm
{
	
	function __construct( $threshv=0.7, $maxthreshv=1.5,
	$maxpeaksv=1500 )
	{
		parent::__construct();
		
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		// Peak thresholds				
		$params->addParam( "minthresh", $threshv, "Minimum threshold" );
		$params->addValidation("minthresh", "float");
		$params->addParam( "maxthresh", $maxthreshv, "Maximum threshold" );
		$params->addValidation("maxthresh", "float");
		$params->addParam( "maxpeaks", $maxpeaksv, "Max number of particles allowed per image" );
		$params->addValidation("maxpeaks", "num");
	}
			
	public function generateForm()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		$fieldSize = 5;
		
		$html.=  "<!-- BEGIN Particle Param -->\n";

		$html.= "<B>Peak thresholds:</B><br />\n";
		$html.= $params->insertTextField( "minthresh", $fieldSize );	
		$html.= $params->insertTextField( "maxthresh", $fieldSize );	
		$html.= $params->insertTextField( "maxpeaks", $fieldSize );	
	
		$html.= "<hr/>\n";
		$html.= "<!-- END Particle Param -->\n";
		
		$html.= parent::generateForm();
			
		return $html;
	}	
	
}
?>
