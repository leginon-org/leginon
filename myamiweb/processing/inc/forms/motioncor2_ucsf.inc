<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLoopForm.inc";
require_once "makeDDStackForm.inc";
class motioncor2_ucsf extends MakeDDStackForm

// Removed defergpu, alignoffset,alignccbox, nrw to make compatible with motioncor2 version
{
	function __construct(  $expId, $errorHTML='', $infoHTML='',$align=True,$bin=1, $nokeepstack=True, $ddstartframe=0, $ddnframe='',$alignlabel='a',$nrw=1, $MaskCentrow=0, $MaskCentcol=0, $MaskSizerows=1.0, $MaskSizecols=1.0, $Patchrows=5, $Patchcols=5, $Iter=7,$Tol=0.5,$Bft=100.0,$FmRef=0,$totaldose='', $doseweight=true, $gpuids=0 )
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'makeddrawframestack' );
		$this->setOutputDirectory( 'ddstack' );
		$this->setBaseRunName( 'ddstack' );
		$this->setTitle( 'makeDDAlignMotionCor2 Launcher' );
		$this->setHeading( 'Create a Direct Detector Aligned Frame Stack with MotionCor2' );
		$this->setExeFile( 'makeDDAlignMotionCor2_UCSF.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "makeDDStack" );
				
		$params->addParam( "align", $align, "align" );
#		$params->addParam( "defergpu", $defergpu, "defer gpu processing" );
		$params->addParam( "gpuids", $gpuids, "GPU ids used (',' separated)");
		$params->addParam( "bin", $bin, "binning" );
		$params->addParam( "no_keepstack", $nokeepstack, "remove generated stack after uploading aligned sum image" );
		$params->addParam( "ddstartframe", $ddstartframe, "start frame" );
		$params->addParam( "ddnframe", $ddnframe, "total frames" );
		$params->addParam( "MaskCent", $MaskCent,"" );
		$params->addParam( "MaskCentrow", $MaskCentrow, "" );
		$params->addParam( "MaskCentcol", $MaskCentcol, "Mask center coordinates" );
		$params->addParam( "MaskSize", $MaskSize,"" );
		$params->addParam( "MaskSizerows", $MaskSizerows, "");
		$params->addParam( "MaskSizecols", $MaskSizecols, "Mask size");
//		$params->addParam( "Patch", $Patch, "" );
		$params->addParam( "Patchrows", $Patchrows,"");
		$params->addParam( "Patchcols", $Patchcols, "Tile frames into m x n segments");
		$params->addParam( "Iter", $Iter, "Number of iterations to perform for alignment");
		$params->addParam( "Tol", $Tol, "Alignment error tolerance (pixels).");
		$params->addParam( "FmRef", $FmRef, "Reference frame which other frames are aligned to");
		$params->addParam( "doseweight", $doseweight, "Also Perform Dose Weighting and upload both results" );
		$params->addParam( "totaldose", $totaldose,"Total Dose used in dose weighting (e/A^2)","default uses database value");

		
		
#		$params->addParam( "alignoffset", $alignoffset, "frame offset" );dd
		$params->addParam( "Bft", $Bft, "B Factor in A^2" );
#		$params->addParam( "alignccbox", $alignccbox, "CC search boxsize in motioncor2" );
		$params->addParam( "alignlabel", $alignlabel, "append label to aligned image" );

#		Using 'nrw' notation from motioncor2_ucsf instead of 'nrw' in motioncorr-Purdue
		$params->addParam( "nrw", $nrw, "Number of frames in running average window");
#		$params->addParam( "flp", $flp, "Flip frames along Y axis.; 0 = no flip, 1 = flip");
	}
		
	public function addValidations()
	{
		$params = $this->getFormParams();
		// Validations
		$params->addValidation( "bin", "float" );
		$params->addValidation( "refimgid", "num" );
	}

	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 4;
		
		$html .= "<b>Make DD stack params:</b><br />\n";
		
		$html.= $params->insertCheckboxField( "align" );
		$html.= $params->insertTextFieldInRow( "alignlabel", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "gpuids", 2*$fieldSize );
		$html.= "<br/>\n";
		$html.= "<hr>\n";
//		$html.= $params->insertCheckboxField( "defergpu" );
//		$html.= $params->insertCheckboxField( "no_keepstack" );
	
		
		$html.= $params->insertTextFieldInRow( "bin", $fieldSize*2 );
		$html.= "<br/>\n";
//		$html.= $params->insertTextFieldInRow( "alignoffset",$fieldSize );
//		$html.= "<br/>\n";

		$html.= $params->insertTextFieldInRow( "Patchrows",$fieldSize );
		$html.= $params->insertTextFieldInRow( "Patchcols",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "MaskCentrow",$fieldSize );
		$html.= $params->insertTextFieldInRow( "MaskCentcol",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "MaskSizerows",$fieldSize );
		$html.= $params->insertTextFieldInRow( "MaskSizecols",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "Iter",$fieldSize );
		$html.= "<br/>\n";
	#	$html.= $params->insertTextFieldInRow( "Tol",$fieldSize );
	#	$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "FmRef",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "Bft", $fieldSize );
		$html.= "<br/>\n";
	#	$html.= $params->insertTextFieldInRow( "alignccbox",$fieldSize );
  	#	$html.= "<br/>\n";
                $html.= $params->insertTextFieldinRow( "nrw", $fieldSize );
                $html.= "<br/>\n";
#               $html.= $params->insertTextFieldinRow( "flp", $fieldSize );
		$html.= "<br/><br/>Frames used for sum image after alignment: <br/>\n";
		$html.= $params->insertTextFieldInRow( "ddstartframe", $fieldSize );
		$html.= $params->insertTextFieldInRow( "ddnframe", $fieldSize );
		$html.= "<br/>\n";
		$html.= "<br/>\n";
		$html.= $params->insertCheckboxField( "doseweight" );
		$html.= $params->insertTextFieldInRow( "totaldose",$fieldSize );
		$html.= "<br/>\n";
		
		return $html;
	}	
	
	public function validate( $postArray )
	{

		
		$msg = parent::validate( $postArray );
		$params = $this->getFormParams();
		$align = $params->getParamValue('align');
		if (!$align) return $msg;
		$nrw = $params->getParamValue('nrw');
		/*if ($nrw != 1 )
			$msg .= "<B>Error:</B> Grouping more than 1 will reduce alignment accuracy in the first few frames. This is not allowed for now".$nrw."<br/>";
		*/
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
				$msg .= "<B>Error:</B> no image found in preset";
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
// No alignoffset in motioncor2_ucsf, removing alignoffset check
//				$alignoffset = $params->getParamValue('alignoffset');
//				if ( $nframes / 2 < $alignoffset ) $msg .= "<B>Error</B> Align frame offset must be less than half of the number of frames saved.<br/>";
//				if ( $nrw > $nframes / 3 ) $msg .= "<B>Error</B> Number of frames in running average window should not be larger than 1/3 of number of frames saved.<br/>";
			}
		}
		$doseweight = $params->getParamValue('doseweight');
		$totaldose = $params->getParamValue('totaldose');
		if ($doseweight == false && $totaldose ) 
			$msg .= "Total dose is irrelevant without dose weighting";
		return $msg;
	}

	// Override the parent build Commnad function to accomodate the "-" in the no-keepstack flag. 
	// Dashes are not parsed correctly in the help.js file, so I have replaced them with an "_" in this file.
//	public function buildCommand( $postArray ){}		
	
}
?>
