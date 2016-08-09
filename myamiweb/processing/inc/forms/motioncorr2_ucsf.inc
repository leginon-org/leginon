<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLoopForm.inc";
require_once "makeDDStackForm.inc";
class motioncorr2_ucsf extends MakeDDStackForm

// Removed defergpu, alignoffset,alignccbox, nrw to make compatible with new motioncorr version
{
	function __construct(  $expId, $errorHTML='', $infoHTML='',$align=True,$bin=1, $nokeepstack='', $ddstartframe=0, $ddnframe='',$alignlabel='a',$Group=1, $MaskCentrows=0.0, $MaskCentcols=0.0, $MaskSizerows=1.0, $MaskSizecols=1.0, $Patchrows=0, $Patchcols=0, $Iter=7,$Tol=0.5,$Bft=100.0,$FmRef=0,$FmDose='' )
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'makeddrawframestack' );
		$this->setOutputDirectory( 'ddstack' );
		$this->setBaseRunName( 'ddstack' );
		$this->setTitle( 'makeDDRawFrameStackv2_ucsf.py Launcher' );
		$this->setHeading( 'Create a Direct Detector Frame Stack with MotionCorrv2 - Official' );
		$this->setExeFile( 'makeDDRawFrameStackv2_ucsf.py' );
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
		$params->addParam( "bin", $bin, "binning" );
		$params->addParam( "no_keepstack", $nokeepstack, "remove generated stack after uploading aligned sum image" );
		$params->addParam( "ddstartframe", $ddstartframe, "start frame" );
		$params->addParam( "ddnframe", $ddnframe, "total frames" );
		$params->addParam( "MaskCent", $MaskCent,"" );
		$params->addParam( "MaskCentrows", $MaskCentrows, "" );
		$params->addParam( "MaskCentcols", $MaskCentcols, "Mask center coordinates" );
		$params->addParam( "MaskSize", $MaskSize,"" );
		$params->addParam( "MaskSizerows", $MaskSizerows, "");
		$params->addParam( "MaskSizecols", $MaskSizecols, "Mask size");
//		$params->addParam( "Patch", $Patch, "" );
		$params->addParam( "Patchrows", $Patchrows,"");
		$params->addParam( "Patchcols", $Patchcols, "Tile frames into m x n segments");
		$params->addParam( "Iter", $Iter, "Number of iterations to perform for alignment");
		$params->addParam( "Tol", $Tol, "Alignment error tolerance (pixels).");
		$params->addParam( "FmRef", $FmRef, "Reference frame which other frames are aligned to");
		$params->addParam( "FmDose", $FmDose,"Dose weighting in e/A^2");

		
		
#		$params->addParam( "alignoffset", $alignoffset, "frame offset" );dd
		$params->addParam( "Bft", $Bft, "B Factor in A^2" );
#		$params->addParam( "alignccbox", $alignccbox, "CC search boxsize in motioncorr" );
		$params->addParam( "alignlabel", $alignlabel, "append label to aligned image" );

#		Using 'Group' notation from motioncorrc2_ucsf instead of 'nrw' in motioncorr-Perdue
		$params->addParam( "Group", $Group, "Number (1, 3, 5, ...) of frames in running average window");
#		$params->addParam( "flp", $flp, "Flip frames along Y axis.; 0 = no flip, 1 = flip");
		// Validations
		$params->addValidation( "bin", "num" );
	}
		
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 4;
		
		$html .= "<b>Make DD stack params:</b><br />\n";
		
		$html.= $params->insertCheckboxField( "align" );
//		$html.= $params->insertCheckboxField( "defergpu" );
		$html.= $params->insertCheckboxField( "no_keepstack" );
	
		
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "bin", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignlabel", $fieldSize );
		$html.= "<br/>\n";
//		$html.= $params->insertTextFieldInRow( "alignoffset",$fieldSize );
//		$html.= "<br/>\n";

		$html.= $params->insertTextFieldInRow( "Patchrows",$fieldSize );
		$html.= $params->insertTextFieldInRow( "Patchcols",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "MaskCentrows",$fieldSize );
		$html.= $params->insertTextFieldInRow( "MaskCentcols",$fieldSize );
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
		$html.= $params->insertTextFieldInRow( "FmDose",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "Bft", $fieldSize );
		$html.= "<br/>\n";
	#	$html.= $params->insertTextFieldInRow( "alignccbox",$fieldSize );
  	#	$html.= "<br/>\n";
                $html.= $params->insertTextFieldinRow( "Group", $fieldSize );
                $html.= "<br/>\n";
#               $html.= $params->insertTextFieldinRow( "flp", $fieldSize );
		$html.= "<br/><br/>Frames used for sum image after alignment: <br/>\n";
		$html.= $params->insertTextFieldInRow( "ddstartframe", $fieldSize );
		$html.= $params->insertTextFieldInRow( "ddnframe", $fieldSize );
		
		return $html;
	}	
	
	public function validate( $postArray )
	{

		
//		$msg = parent::validate( $postArray );
		$msg = '';
		$params = $this->getFormParams();
		$align = $params->getParamValue('align');
		if (!$align) return $msg;
		$Group = $params->getParamValue('Group');
		if ( $Group%2 == 0 )
		{
			$msg .= "<B>Error:</B> testNumber of frames in running average window must be odd. Group = ".$Group."<br/>";
		}
		// Get recent image to check nframes against alignoffset and Group.
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
// No alignoffset in motioncorrv2_ucsf, removing alignoffset check
//				$alignoffset = $params->getParamValue('alignoffset');
//				if ( $nframes / 2 < $alignoffset ) $msg .= "<B>Error</B> Align frame offset must be less than half of the number of frames saved.<br/>";
//				if ( $Group > $nframes / 3 ) $msg .= "<B>Error</B> Number of frames in running average window should not be larger than 1/3 of number of frames saved.<br/>";
			}
		}
		return $msg;
	}

	// Override the parent build Commnad function to accomodate the "-" in the no-keepstack flag. 
	// Dashes are not parsed correctly in the help.js file, so I have replaced them with an "_" in this file.
//	public function buildCommand( $postArray ){}		
	
}
?>
