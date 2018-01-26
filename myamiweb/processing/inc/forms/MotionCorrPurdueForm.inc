<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLoopForm.inc";

class MotionCorrPurdueForm extends BasicLoopForm

{
	function __construct(  $expId, $errorHTML='', $infoHTML='',$align=True, $defergpu='', $bin=1, $nokeepstack='', $ddstartframe=0, $ddnframe='',$alignoffset=7,$alignbfactor=1000,$alignccbox=96,$alignlabel='a', $flp=0, $nrw=3, $gpuid=0 ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('gpudriftcorr','purduedriftcorr','appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'makeddrawframestack' );
		$this->setOutputDirectory( 'ddstack' );
		$this->setBaseRunName( 'ddstack' );
		$this->setTitle( 'makeDDAlignMotionCorr_Purdue.py Launcher' );
		$this->setHeading( 'Create a Direct Detector Frame Stack' );
		$this->setExeFile( 'makeDDAlignMotionCorr_Purdue.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
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
		$params->addParam( "alignoffset", $alignoffset, "frame offset" );
		$params->addParam( "alignbfactor", $alignbfactor, "b factor in motioncorr" );
		$params->addParam( "alignccbox", $alignccbox, "CC search boxsize in motioncorr" );
		$params->addParam( "alignlabel", $alignlabel, "append label to aligned image" );
		$params->addParam( "nrw", $nrw, "Number (1, 3, 5, ...) of frames in running average window");
		$params->addParam( "flp", $flp, "Flip frames along Y axis.; 0 = no flip, 1 = flip");
		$params->addParam( "gpuid", $gpuid, "GPU id used");
		// Validations
		$params->addValidation( "bin", "num" );
		$params->addValidation( "gpuid", "num" );
	}
		
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 4;
		
		$html .= "<b>Make DD stack params:</b><br />\n";
		
		$html.= $params->insertCheckboxField( "align" );
		$html.= $params->insertCheckboxField( "defergpu" );
		$html.= $params->insertTextFieldInRow( "alignlabel", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertCheckboxField( "no_keepstack" );
		$html.= $params->insertTextFieldInRow( "gpuid", $fieldSize );
		$html.= "<hr>\n";
	
		
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "bin", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignoffset",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignbfactor", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignccbox",$fieldSize );
  		$html.= "<br/>\n";
                $html.= $params->insertTextFieldinRow( "nrw", $fieldSize );
                $html.= "<br/>\n";
                $html.= $params->insertTextFieldinRow( "flp", $fieldSize );
		$html.= "<br/><br/>Frames used for sum image after alignment: <br/>\n";
		$html.= $params->insertTextFieldInRow( "ddstartframe", $fieldSize );
		$html.= $params->insertTextFieldInRow( "ddnframe", $fieldSize );
		
		return $html;
	}	
	
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		$params = $this->getFormParams();
		$align = $params->getParamValue('align');
		if (!$align) return $msq;
		$nrw = $params->getParamValue('nrw');
		if ( $nrw%2 == 0 )
		{
			$msg .= "<B>Error:</B> Number of frames in running average window must be odd. <br/>";
		}
		// Get recent image to check nframes against alignoffset and nrw.
		$preset = $postArray['preset'];
		$testfilename = $postArray['testfilename'];
		$leginondata = new leginondata();
		if ( $testfilename ) {
			// testing
			$images = $leginondata->getFilename($testfilename, $this->expId);
			if ( !is_array($images ) || empty($images) ) {
				$msg .= "<B>Error:</B> image ".$testfilename." not found in the session <br/>";
			} else {
				$imageId = $images[0]['id'];
			}
		} else {
			// preset
			$images = $leginondata->getFilenames($this->expId, $preset);
			if ( !is_array($images ) || empty($images) ) {
				$msg .= "<B>Error:</B> no image not found in preset";
			} else {
				$imageId = $images[0]['id'];
			}
		}

		if ( $imageId ) {
			$nframes = $leginondata->getNFramesSavedFromImage($imageId);
			if ( $nframes == false ) { 
				if ( $testfilename ) {
					$msg .= "<B>Error</B> Image does not have frames saved. Can not align";
				}	else {
					$msg .= "<B>Error</B> Last image of the specified preset does not have frames saved. Can not validate. Try again later.";
				}
			} else {
				$alignoffset = $params->getParamValue('alignoffset');
				if ( $nframes / 2 < $alignoffset ) $msg .= "<B>Error</B> Align frame offset must be less than half of the number of frames saved.<br/>";
				if ( $nrw > $nframes / 3 ) $msg .= "<B>Error</B> Number of frames in running average window should not be larger than 1/3 of number of frames saved.<br/>";
			}
		}
		return $msg;
	}

	// Override the parent build Commnad function to accomodate the "-" in the no-keepstack flag. 
	// Dashes are not parsed correctly in the help.js file, so I have replaced them with an "_" in this file.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand($postArray);
						
		$command = $this->addCommandFlag($command, "no-keepstack", "no_keepstack" );

		// if we are not testing an image, add the parellel flag
		if ( !($postArray['testimage']=="on") ) {
			$command = $this->addCommandFlag($command, "parallel", "parallel", "on" );
		}
		
		// remove params not needed in command
		$command = $this->removeCommandFlag($command, "no_keepstack" );
		
		return $command;
	}		
	
}
?>
