<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require_once "basicLoopForm.inc";

class gctf extends BasicLoopForm
{
	function __construct( $expId, $extraHTML='', $ampcontrast='0.07', $bestdb=true, 
		$apcontinue='1', $fieldsize='1024', $dast='0.1',  $bestdb=true,$parallel=true, $do_basic_rotave='0', $do_EPA='0', $overlap='0.5',$convsize='85', $do_Hres_ref='0', $defstep='0.1', $resmin='50',$resmax='4')
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('gctf');
		$this->setPublications( $pubList );
		$this->setJobType( 'gctf' );
		$this->setOutputDirectory( 'gctf' );
		$this->setBaseRunName( 'gctfrun' );
		$this->setTitle( 'GCTF Launcher' );
		$this->setHeading( 'GPU Accelerated CTF Estimation with GCTF' );
		$this->setExeFile( 'gctf.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "gctf" );
				
		$params->addParam( "ampcontrast", $ampcontrast, "Amplitude contrast" );
		$params->addParam( "defstep", $defstep, "Step of defocus value, in &mu;m" );
		$params->addParam( "dast", $dast, "Estimated astigmation in &mu;m" );
		$params->addParam( "bestdb", $bestdb, "Use best values from database" );
		$params->addParam( "nominal", $nominal, "Override Nominal Value ( in &mu;m)" );

		$params->addParam( "bfactor", $bfactor, "Bfactor");
		$params->addParam( "resmin", $resmin, "Lowest resolution for search, in &Aring;");
		$params->addParam( "resmax", $resmax, "Highest resolution for search, in &Aring;");
		$params->addParam( "fieldsize", $fieldsize, "FFT boxsize");
		$params->addParam( "do_basic_rotave", $do_basic_rotave, "Rotational averaging");
		$params->addParam( "do_EPA", $do_EPA, "Equiphase averaging"); 
		$params->addParam( "overlap", $overlap, "Overlapping factor");
		$params->addParam( "convsize", $convsize, "Smoothing boxsize");
		$params->addParam( "do_Hres_ref", $do_Hres_ref, "Use high-resolution refinement");
		$params->addParam( "Href_resL", $Href_resL, "Low resolution limit for high-resolution refinement");
		$params->addParam( "Href_resH", $Href_resH, "High resolution limit for high-resolution refinement");
		$params->addParam( "Href_bfac", $Href_bfac, "Bfactor for high-resolution refinement");
		$params->addParam( "mdef_aveN", $mdef_aveN, "Average number of movie frames for movie CTF refinement");
		$params->addParam( "mdef_fit", $mdef_fit, "Linear fitting defocus changes in Z-direction");
		$params->addParam( "mdef_ave_type", $mdef_ave_type, "Averaging type");
		$params->addParam( "do_local_refine", $do_local_refine, "Do local refinement");
		$params->addParam( "local_radius", $local_radius, "Radius for local refinement");
		$params->addParam( "local_boxtype", $local_boxtype, "Local refinement box type");
		$params->addParam( "local_boxsize", $local_boxsize, "Local refinement boxsize");
		$params->addParam( "local_overlap", $local_overlap, "Local refinement overlapping factor");
		$params->addParam( "local_resL", $local_resL, "Low resolution limit for local CTF");
		$params->addParam( "local_resH", $local_resH, "High resolution limit for local CTF");
		$params->addParam( "refine_local_astm", $refine_local_astm, "Local refinement astigmation");

		$params->addParam( "refine_tilt", $refine_tilt, "Do tilt refinement");
		$params->addParam( "init_tilt_ang", $init_tilt_ang, "Initial tilt angle");
		$params->addParam( "init_tilt_err", $init_tilt_error, "Error of tilt angle");


		$params->addParam( "do_phase_flip", $do_phase_flip, "Do phase flipping");

		$params->addParam( "do_validation", $do_validation, "Do validation of CTF determination.");

		$params->addParam( "boxsuffix", $boxsuffix, "Input suffix for local refinement");
		$params->addParam( "ctfstar", $ctfstar, "Output star files to write all CTF parameters");
		$params->addParam( "logsuffix", $logsuffix, "Output suffix for log files");
		$params->addParam( "write_local_ctf", $write_local_ctf, "Write local CTF");
		$params->addParam( "plot_res_ring", $plot_res_ring, "Plot an estimated resolution ring on the final .ctf diagnosis file.");
		$params->addParam( "output_time", $output_time, "Include process time measurements in output");
		$params->addParam( "gid", $gid, "GPU ID");
		
		



		// Validations
	}
	

	
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		$html .= "
	    <br />
	    <H4>Required Parameters</H4>
	    <hr />";
			
		$html.= $params->insertTextField( "ampcontrast", $fieldSize );
	        $html .= "
	    <br />
	    <H4>Additional Parameters</H4>
	    <hr />";

		$html.= $params->insertTextField( "defstep", $fieldSize );
		//$html.= $params->insertTextField( "defL", $fieldSize );
		//$html.= $params->insertTextField( "defH", $fieldSize );
		//$html.= $params->insertTextField( "defS", $fieldSize );
		//$html.= $params->insertTextField( "bfactor", $fieldSize );
		$html.= $params->insertTextField( "resmin", $fieldSize );
		$html.= $params->insertTextField( "resmax", $fieldSize );
		$html.= $params->insertTextField( "fieldsize", $fieldSize );
                $html.= $params->insertTextField( "dast", $fieldSize );


/*
	        $html .= "
            <br />
            <H4>Additional Advanced Parameters</H4>
            <hr />";

		$html.= $params->insertTextField( "do_basic_rotave", $fieldSize );
		
		$html.= $params->insertTextField( "do_EPA", $fieldSize );
		$html.= $params->insertTextField( "overlap", $fieldSize );
		$html.= $params->insertTextField( "convsize", $fieldSize );
		$html.= $params->insertTextField( "do_Hres_ref", $fieldSize );
		$html.= $params->insertTextField( "Href_resL", $fieldSize );
		$html.= $params->insertTextField( "Href_resH", $fieldSize );
		$html.= $params->insertTextField( "refine_local_astm", $fieldSize );

                $html .= "
            <br />
            <H4>Tilt Refinement Parameters</H4>
            <hr />";



		$html.= $params->insertTextField( "refine_tilt", $fieldSize );
		$html.= $params->insertTextField( "init_tilt_ang", $fieldSize );
		$html.= $params->insertTextField( "init_tilt_err", $fieldSize );


                $html .= "
            <br />
            <H4>Correction and Validation Parameters (Recommended)</H4>
            <hr />";

		$html.= $params->insertTextField( "do_phase_flip", $fieldSize );
		$html.= $params->insertTextField( "do_validation", $fieldSize );


	                $html .= "
            <br />
            <H4>I/O Parameters</H4>
            <hr />";

		$html.= $params->insertTextField( "boxsuffix", $fieldSize );
		$html.= $params->insertTextField( "ctfstar", $fieldSize );
		$html.= $params->insertTextField( "logsuffix", $fieldSize );
		$html.= $params->insertTextField( "write_local_ctf", $fieldSize );
		$html.= $params->insertTextField( "plot_res_ring", $fieldSize );
		$html.= $params->insertTextField( "output_time", $fieldSize );
		$html.= $params->insertTextField( "gid", $fieldSize );
*/

		return $html;
	}	

}
?>
