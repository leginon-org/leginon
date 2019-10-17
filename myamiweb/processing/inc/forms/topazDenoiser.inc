<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLoopForm.inc";
class topazDenoiser extends BasicLoopForm

{
	function __construct(  $expId, $errorHTML='', $infoHTML='',$bin=1, $denoiselabel='td', $patchsize=1536, $patchpadding=128, $device=0, $earlyreturn=False)
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion','topaz');
		$this->setPublications( $pubList );
		$this->setJobType( 'topazdenoise' );
		$this->setOutputDirectory( 'topaz_denoise' );
		$this->setBaseRunName( 'topaz_denoise' );
		$this->setTitle( 'Topaz Denoiser' );
		$this->setHeading( 'Topaz Denoiser' );
		$this->setExeFile( 'topazDenoiser.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		//$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		$params->setHelpSection( "topazDenoise" );
		$params->addParam( "device", $device, "device" );
		$params->addParam( "denoiselabel", $denoiselabel, "append label to denoised image" );
		$params->addParam( "patchsize", $patchsize, "patch size" );
		$params->addParam( "patchpadding", $patchpadding, "patch padding" );
		$params->addParam( "earlyreturn", $earlyreturn, "early return" );
	}
		
	public function addValidations()
	{
		$params = $this->getFormParams();
		// Validations
	}

	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 4;
		
		$html .= "<b>Topaz denoiser params:</b><br />\n";
		$html.= $params->insertTextFieldInRow( "device", $fieldSize );
		$html.= "<br/>\n";
		
		$html.= $params->insertTextFieldInRow( "denoiselabel", $fieldSize );
		$html.= "<br/>\n";
		$html.= "<hr>\n";
		
		$html.= $params->insertTextFieldInRow( "patchsize", $fieldSize );
		$html.= "<br/>\n";

		$html.= $params->insertTextFieldInRow( "patchpadding", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertCheckboxField( "earlyreturn" );
		$html.= "<br/>\n";
		
		$html.= "<script>var select = document.getElementsByName('preset')[0];select.selectedIndex = select.options.length-1;</script>";
		
		return $html;
	}	
	
	public function validate( $postArray )
	{

		
		$msg = parent::validate( $postArray );
		$params = $this->getFormParams();
		$preset = $postArray['preset'];
		$testfilename = $postArray['testfilename'];
		$leginondata = new leginondata();
			// preset
		$images = $leginondata->getFilenames($this->expId, $preset);
		if ( !is_array($images ) || empty($images) ) {
			$msg .= "<B>Error:</B> no image found in preset";
		} else {
			$imageId = $images[0]['id'];
		}
		$_POST['queue'] = "gpu";
		return $msg;
	}
}
?>
