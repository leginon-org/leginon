<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc";

class Protomo2RefineForm extends BasicLayoutForm
{
	function __construct( $expId, $windowsize_x='512', $windowsize_y='512', $sampling='', $thickness='', $cos_alpha='', $lp_diam_x='0.5', $lp_diam_y='0.5', $lp_apod_x='', $lp_apod_y='', $hp_diam_x='0.001', $hp_diam_y='0.001', $hp_apod_x='', $hp_apod_y='', $corr_mode='mcf', $raw_path='', $iters='', $param='', $binning='true', $preprocessing='true', $select_images='', $exclude_images='', $border='', $clip_low='', $clip_high='', $gradient='true', $iter_gradient='', $filter='median', $kernel_x='', $kernel_y='', $window_area='0.95', $mask_apod_x='', $mask_apod_y='', $mask_width='N - 2.5 * apodization', $do_estimation='false', $max_correction='', $correlation_size_x='', $correlation_size_y='', $peak_search_radius_x='', $peak_search_radius_y='', $orientation='true', $azimuth='true', $elevation='true', $rotation='true', $logging='true', $loglevel='2', $map_size_x='', $map_size_y='', $map_size_z='', $filename_prefix='', $image_extension='mrc', $cachedir='cache', $protomo_outdir='out' )
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Refinement Launcher' );
		$this->setHeading( 'Protomo Refinement' );
		$this->setExeFile( 'protomo2aligner.py' );
		$this->setGuideURL( "http://ami.scripps.edu/redmine/projects/appion/wiki/" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
				
		$params->addParam( "windowsize_x", $windowsize_x, "Pixels in x to use for region matching" );
		$params->addParam( "windowsize_y", $windowsize_y, "Pixels in y to use for region matching" );
		$params->addParam( "sampling", $sampling, "Sampling rate of raw data" );
		$params->addParam( "thickness", $thickness, "Estimated thickness of unbinned specimen (in pixels)" );
		$params->addParam( "cos_alpha", $cos_alpha, "Cosine of the highest tilt angle" );
		$params->addParam( "lowpass_diameter_x", $lp_diam_x, "Lowpass diameter (x) in fractions of nyquist" );
		$params->addParam( "lowpass_diameter_y", $lp_diam_y, "Lowpass diameter (y) in fractions of nyquist" );
		$params->addParam( "lowpass_apod_x", $lp_apod_x, "Lowpass apodization (x) for rectangular and ellipsoidal masks" );
		$params->addParam( "lowpass_apod_y", $lp_apod_y, "Lowpass apodization (y) for rectangular and ellipsoidal masks" );
		$params->addParam( "highpass_diameter_x", $hp_diam_x, "Highpass diameter (x) in fractions of nyquist" );
		$params->addParam( "highpass_diameter_y", $hp_diam_y, "Highpass diameter (y) in fractions of nyquist" );
		$params->addParam( "highpass_apod_x", $hp_apod_x, "Highpass apodization (x) for rectangular and ellipsoidal masks" );
		$params->addParam( "highpass_apod_y", $hp_apod_y, "Highpass apodization (y) for rectangular and ellipsoidal masks" );
		$params->addParam( "correlation_mode", $corr_mode, "Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl)" );
		$params->addParam( "raw_path", $raw_path, "Full path to raw image files" );
		$params->addParam( "iters", $iters, "Number of alignment and geometry refinement iterations" );
		$params->addParam( "param_file", $param, "Override other parameters and use an external paramfile. Provide full path" );
		$params->addParam( "binning", $binning, "Enable/disable binning of raw images" );
		$params->addParam( "preprocessing", $preprocessing, "Enable/disable preprocessing of raw image files" );
		$params->addParam( "select_images", $select_images, "Select specific images in the tilt series" );
		$params->addParam( "exclude_images", $exclude_images, "Exclude images from the tilt series" );
		$params->addParam( "border_width", $border, "Width of area at the image edge to exclude from image statistics" );
		$params->addParam( "clip_low", $clip_low, "Lower threshold specified as a multiple of the standard deviation" );
		$params->addParam( "clip_high", $clip_high, "Upper threshold specified as a multiple of the standard deviation" );
		$params->addParam( "gradient", $gradient, "Enable/disable linear gradient subtraction for preprocessing masks" );
		$params->addParam( "iter_gradient", $iter_gradient, "Iterate gradient subtraction once" );
		$params->addParam( "filter", $filter, "Preprocessing filter. Options are 'median' or 'gauss'" );
		$params->addParam( "kernel_x", $kernel_x, "Filter window size (x)" );
		$params->addParam( "kernel_y", $kernel_y, "Filter window size (y)" );
		$params->addParam( "window_area_fraction", $window_area, "Fraction of extracted area that must lie within the source image. Real value between 0 and 1" );
		$params->addParam( "mask_apod_x", $mask_apod_x, "Apodization (x) for rectangular and ellipsoidal masks" );
		$params->addParam( "mask_apod_y", $mask_apod_y, "Apodization (y) for rectangular and ellipsoidal masks" );
		$params->addParam( "mask_width", $mask_width, "Rectangular mask width" );
		$params->addParam( "estimate_parameters", $do_estimation, "Estimate geometric parameters instead of using stored values from previous cycle" );
		$params->addParam( "max_correction", $max_correction, "Terminate alignment if correction exceeds specified value" );
		$params->addParam( "correlation_size_x", $correlation_size_x, "Size (x) of cross correlation peak image" );
		$params->addParam( "correlation_size_y", $correlation_size_y, "Size (y) of cross correlation peak image" );
		$params->addParam( "peak_search_radius_x", $peak_search_radius_x, "Peak search region (x)" );
		$params->addParam( "peak_search_radius_y", $peak_search_radius_y, "Peak search region (y)" );
		$params->addParam( "orientation", $orientation, "Include orientation angles in refinement" );
		$params->addParam( "azimuth", $azimuth, "Include tilt azimuth in refinement" );
		$params->addParam( "elevation", $elevation, "Include tilt axis elevation in refinement" );
		$params->addParam( "rotation", $rotation, "Include in-plane rotations in refinement" );
		$params->addParam( "logging", $logging, "Enable diagnostic terminal output" );
		$params->addParam( "logging_level", $loglevel, "Increase verbosity of diagnostic output" );
		$params->addParam( "map_size_x", $map_size_x, "Size (x) of the reconstructed tomogram" );
		$params->addParam( "map_size_y", $map_size_y, "Size (y) of the reconstructed tomogram" );
		$params->addParam( "map_size_z", $map_size_z, "Size (z) of the reconstructed tomogram" );
		$params->addParam( "filename_prefix", $filename_prefix, "Prefix for input and output files, with the exception of raw image files, which are specified in the geometry file" );
		$params->addParam( "image_extension", $image_extension, "Filetype extension for images. Protomo supports CCP4, EM, FFF, IMAGIC, MRC, SPIDER, SUPRIM,and TIFF" );
		$params->addParam( "cachedir", $cachedir, "Directory where cache files are stored" );
		$params->addParam( "outdir", $protomo_outdir, "Directory where Protomo output files are stored" );
		
		// Validations
		$params->addValidation( "windowsize_x", "req" );
		$params->addValidation( "windowsize_x", "num" );
		$params->addValidation( "windowsize_y", "req" );
		$params->addValidation( "windowsize_y", "num" );
		$params->addValidation( "sampling", "req" );
		$params->addValidation( "sampling", "num" );
		$params->addValidation( "thickness", "req" );
		$params->addValidation( "thickness", "num" );
		$params->addValidation( "iters", "req" );
		$params->addValidation( "iters", "num" );
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 8;
		
		$html .= "
	    <br />
	    <H4>Required Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "windowsize_x", $fieldSize );
		$html.= $params->insertTextField( "windowsize_y", $fieldSize );
		$html.= $params->insertTextField( "sampling", $fieldSize );
		$html.= $params->insertTextField( "thickness", $fieldSize );
		$html.= $params->insertTextField( "iters", $fieldSize );
		
		$html .= "
	    <br />
	    <H4>Optional Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "cos_alpha", $fieldSize );
		$html.= $params->insertTextField( "lowpass_diameter_x", $fieldSize );
		$html.= $params->insertTextField( "lowpass_diameter_y", $fieldSize );
		$html.= $params->insertTextField( "lowpass_apod_x", $fieldSize );
		$html.= $params->insertTextField( "lowpass_apod_y", $fieldSize );
		$html.= $params->insertTextField( "highpass_diameter_x", $fieldSize );
		$html.= $params->insertTextField( "highpass_diameter_y", $fieldSize );
		$html.= $params->insertTextField( "highpass_apod_x", $fieldSize );
		$html.= $params->insertTextField( "highpass_apod_y", $fieldSize );
		$html.= $params->insertTextField( "correlation_mode", $fieldSize );
		$html.= $params->insertTextField( "raw_path", $fieldSize );
		$html.= $params->insertTextField( "param_file", $fieldSize );
		$html.= $params->insertTextField( "binning", $fieldSize );
		$html.= $params->insertTextField( "preprocessing", $fieldSize );
		$html.= $params->insertTextField( "select_images", $fieldSize );
		$html.= $params->insertTextField( "exclude_images", $fieldSize );
		$html.= $params->insertTextField( "border_width", $fieldSize );
		$html.= $params->insertTextField( "clip_low", $fieldSize );
		$html.= $params->insertTextField( "clip_high", $fieldSize );
		$html.= $params->insertTextField( "gradient", $fieldSize );
		$html.= $params->insertTextField( "iter_gradient", $fieldSize );
		$html.= $params->insertTextField( "filter", $fieldSize );
		$html.= $params->insertTextField( "kernel_x", $fieldSize );
		$html.= $params->insertTextField( "kernel_y", $fieldSize );
		$html.= $params->insertTextField( "window_area_fraction", $fieldSize );
		$html.= $params->insertTextField( "mask_apod_x", $fieldSize );
		$html.= $params->insertTextField( "mask_apod_y", $fieldSize );
		$html.= $params->insertTextField( "mask_width", $fieldSize );
		$html.= $params->insertTextField( "estimate_parameters", $fieldSize );
		$html.= $params->insertTextField( "max_correction", $fieldSize );
		$html.= $params->insertTextField( "correlation_size_x", $fieldSize );
		$html.= $params->insertTextField( "correlation_size_y", $fieldSize );
		$html.= $params->insertTextField( "peak_search_radius_x", $fieldSize );
		$html.= $params->insertTextField( "peak_search_radius_y", $fieldSize );
		$html.= $params->insertTextField( "orientation", $fieldSize );
		$html.= $params->insertTextField( "azimuth", $fieldSize );
		$html.= $params->insertTextField( "elevation", $fieldSize );
		$html.= $params->insertTextField( "rotation", $fieldSize );
		$html.= $params->insertTextField( "logging", $fieldSize );
		$html.= $params->insertTextField( "logging_level", $fieldSize );
		$html.= $params->insertTextField( "map_size_x", $fieldSize );
		$html.= $params->insertTextField( "map_size_y", $fieldSize );
		$html.= $params->insertTextField( "map_size_z", $fieldSize );
		$html.= $params->insertTextField( "filename_prefix", $fieldSize );
		$html.= $params->insertTextField( "image_extension", $fieldSize );
		$html.= $params->insertTextField( "cachedir", $fieldSize );
		$html.= $params->insertTextField( "outdir", $fieldSize );

		$html .= "<br></br>
	    <a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructForm'><b><center>[Click here to continue onto Reconstruction if protomo2aligner.py has finished and you're happy with the alignment result]</center></b></a>";

		return $html;
	}	

	// Override the default build Command Function because the --test flag is not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		if ( $postArray['testimage']=="on" ) {
			$command.= " --test";
		}
		
		return $command." ";
	}	
	
}
?>
