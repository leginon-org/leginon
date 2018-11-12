<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "basicLoopForm.inc";
require_once "ddstackSelectTable.inc";
require_once "dbDefocusTable.inc";

class gctf extends BasicLoopForm
{
	protected $alignedDDStackIds;


	function __construct( $expId, $extraHTML='', $ampcontrast='0.07', $mdef_aveN='7', $do_EPA=true,$do_local_refine=false, $local_raster='200', $local_radius='1024', $local_boxsize='512', $local_overlap='0.5',
	$apcontinue='1', $fieldsize='1024', $dast='0.1',  $bestdb=true, $nominal='', $parallel=true, $do_basic_rotave='0', $overlap='0.5',$convsize='85', $do_Hres_ref='0', $defstep='0.1', $resmin='50',$resmax='4',$useDDStack=false, $ddstackid=false,$max_phase_shift='180',$min_phase_shift='0',$phase_search_step='1',$phaseplate=false, $speedmode='fastmode')
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('gctf');
		$this->setPublications( $pubList );
		$this->setJobType( 'gctf' );
		$this->setOutputDirectory( 'ctf' );
		$this->setBaseRunName( 'gctfrun' );
		$this->setTitle( 'GCTF Launcher' );
		$this->setHeading( 'GPU Accelerated CTF Estimation with GCTF' );
		$this->setExeFile( 'gctf.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.

		//Other forms to include	
		$this->ddStackSelectTable = new DDStackSelectTable($expId, $useDDStack, $ddstackid);
		$this->ddStackSelectTable->setOnlyAligned(false);
		$this->dbDefocusTable = new dbDefocusTable($expId, $bestdb, $nominal);

		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help, $ddstackid=false.
		$params->setHelpSection( "gctf" );
				
		// Gctf parameters
		$params->addParam( "ampcontrast", $ampcontrast, "Amplitude contrast" );
		$params->addValidation("ampcontrast", "float");
		$params->addParam( "defstep", $defstep, "Step of defocus value, in &mu;m" );
		$params->addValidation("defstep", "float");
		$params->addParam( "dast", $dast, "Estimated astigmation in &mu;m" );
		$params->addValidation("dast", "float");

		$params->addParam( "bfactor", $bfactor, "Bfactor");
		$params->addParam( "resmin", $resmin, "Lowest resolution for search, in &Aring;");
		$params->addParam( "resmax", $resmax, "Highest resolution for search, in &Aring;");
		$params->addParam( "fieldsize", $fieldsize, "FFT boxsize");
		$params->addValidation("fieldsize", "num");
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
		$params->addParam( "local_raster", $local_raster, "Raster spacing"); 
		$params->addValidation("local_raster", "num");
		$params->addParam( "local_radius", $local_radius, "Local Radius (no weighting beyond radius)");
		$params->addParam( "local_boxtype", $local_boxtype, "Local refinement box type");
		$params->addParam( "local_boxsize", $local_boxsize, "Local Box Size");
		$params->addParam( "local_overlap", $local_overlap, "Local overlap factor for sampling");
		$params->addParam( "local_resL", $local_resL, "Low resolution limit for local CTF");
		$params->addParam( "local_resH", $local_resH, "High resolution limit for local CTF");
		$params->addParam( "refine_local_astm", $refine_local_astm, "Local refinement astigmation");
		//$params->addParam( "refine_tilt", $refine_tilt, "Do tilt refinement. 0: no tilt refinement; 1: refine global tilt before local refinement");
		//$params->addParam( "init_tilt_ang", $init_tilt_ang, "Initial tilt angle");
		//$params->addParam( "init_tilt_err", $init_tilt_error, "Error of tilt angle");
		$params->addParam( "do_phase_flip", $do_phase_flip, "Do phase flipping");
		$params->addParam( "do_validation", $do_validation, "Do validation of CTF determination.");
		$params->addParam( "boxsuffix", $boxsuffix, "Input suffix for local refinement");
		$params->addParam( "ctfstar", $ctfstar, "Output star files to write all CTF parameters");
		$params->addParam( "logsuffix", $logsuffix, "Output suffix for log files");
		$params->addParam( "write_local_ctf", $write_local_ctf, "Write local CTF");
		$params->addParam( "plot_res_ring", $plot_res_ring, "Plot an estimated resolution ring on the final .ctf diagnosis file.");
		$params->addParam( "output_time", $output_time, "Include process time measurements in output");
		$params->addParam( "gid", $gid, "GPU ID");
		$params->addParam( "speedmode", $speedmode, "Do not create images" );

		//Phase plate parameters
		$params->addParam( "max_phase_shift", $max_phase_shift,"Maximum phase shift");
		$params->addParam( "min_phase_shift", $min_phase_shift,"Minimum phase shift");
		$params->addParam( "phase_search_step", $phase_search_step,"Phase search step");
		$params->addParam( "phaseplate", $phaseplate,"Do phase search");
		
	}
	
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		$html .=$this->ddStackSelectTable->generateForm();
		$html.= $params->insertTextField( "mdef_aveN",4);
		$html.= "<hr>";

		$html.= parent::generateAdditionalFormLeft();
		return $html;
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
	    <H4>Appion Parameters</H4>
	    <hr />";
		$html .=$this->dbDefocusTable->generateForm();


	   $html.= "<p>Processing Speed: <br/>\n";
		$html.= $params->insertRadioField("speedmode", "fastmode", "Fast: Do not create CTF summary images","");	
		$html.= $params->insertRadioField("speedmode", "slowmode", "Slow: Create CTF summary images","");	
		$html.= "</p>";

		$html .= "
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
		$html.= $params->insertCheckBoxField( "do_EPA");
/*
		$html .= "
	    <br />
	    <H4>Additional Advanced Parameters</H4>
	    <hr />";
/*

		$html.= $params->insertTextField( "do_basic_rotave", $fieldSize );
		$html.= $params->insertTextField( "overlap", $fieldSize );
		$html.= $params->insertTextField( "convsize", $fieldSize );
		$html.= $params->insertTextField( "do_Hres_ref", $fieldSize );
		$html.= $params->insertTextField( "Href_resL", $fieldSize );
		$html.= $params->insertTextField( "Href_resH", $fieldSize );
		$html.= $params->insertTextField( "refine_local_astm", $fieldSize );
*/


		$html .= "

	    <br />

	    <H4>Local CTF Estimation Parameters</H4>
	    <hr />";

		$html.= $params->insertCheckBoxField( "do_local_refine");
		$html.= $params->insertTextField( "local_raster", $fieldSize);
		$html.= $params->insertTextField( "local_radius", $fieldSize);
		$html.= $params->insertTextField( "local_boxsize", $fieldSize);
		$html.= $params->insertTextField( "local_overlap", $fieldSize);

		$html .= "

	    <br />

	    <H4>Phase Plate Parameters</H4>
	    <hr />";
		$html.= $params->insertCheckBoxField( "phaseplate");
		$html.= "<br />";		
		$html.= $params->insertTextField( "max_phase_shift", $fieldSize );
		$html.= $params->insertTextField( "min_phase_shift", $fieldSize );
		$html.= $params->insertTextField( "phase_search_step", $fieldSize );

/*	Hide until python function is implemented
		$html .= "
	    <br />


	    <H4>Tilt Refinement Parameters</H4>
	    <hr />";
		$html.= $params->insertTextField( "refine_tilt", $fieldSize );
		$html.= $params->insertTextField( "init_tilt_ang", $fieldSize );
		$html.= $params->insertTextField( "init_tilt_err", $fieldSize );
*/
/*
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
 $msg = parent::validate( $postArray );		$html.= $params->insertTextField( "logsuffix", $fieldSize );
		$html.= $params->insertTextField( "write_local_ctf", $fieldSize );
		$html.= $params->insertTextField( "plot_res_ring", $fieldSize );
		$html.= $params->insertTextField( "output_time", $fieldSize );
		$html.= $params->insertTextField( "gid", $fieldSize );
*/

		return $html;
	}	

	public function validate($postArray )
	{
		$msg = parent::validate( $postArray );
		$msg .= $this->ddStackSelectTable->validate( $postArray);
		$msg .= $this->dbDefocusTable->validate( $postArray);
	return $msg;
	}

	 public function buildCommand( $postArray )
	{

		$command = parent::buildCommand( $postArray );
		$command .= $this->dbDefocusTable->buildCommand( $postArray);
		$command .= $this->ddStackSelectTable->buildCommand( $postArray);

		$this->formParams->getPostedValues( $postArray );
		$paramArray = $this->formParams->getParamArray();
		// If the form does purely composite and does not define any params of its own,
		// the param array will be null.

		if ( $paramArray ) {
			foreach ( $paramArray as $key=>$param ) {
				if (($param['name'] == 'phaseplate')&&($paramArray['phaseplate']['value'] == false )) {
					$command = $this->removeCommandFlag($command,'max_phase_shift',$param['max_phase_shift']);
					$command = $this->removeCommandFlag($command,'min_phase_shift',$param['min_phase_shift']);
					$command = $this->removeCommandFlag($command,'phase_search_step',$param['phase_search_step']);
				}
				if (($param['name'] == 'do_local_refine')&&($paramArray['do_local_refine']['value'] == false )) {
					$command = $this->removeCommandFlag($command,'local_raster',$param['local_raster']);
					$command = $this->removeCommandFlag($command,'local_radius',$param['local_radius']);
					$command = $this->removeCommandFlag($command,'local_boxsize',$param['local_boxsize']);
					$command = $this->removeCommandFlag($command,'local_overlap',$param['local_overlap']);
				}
			}
		}

		$command = $this->removeCommandFlag($command, 'speedmode');
		$params = $this->getFormParams();
		$speedmode = $params->getParamValue( "speedmode" );
		$command .= " --".$speedmode." ";

		return $command;
	}


	}
