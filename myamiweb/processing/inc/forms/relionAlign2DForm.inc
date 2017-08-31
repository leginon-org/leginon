<?php

/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

class RelionAlign2DForm extends BasicLayoutForm
{
	protected $stackIds;

	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='', $stackId='', $clip='', $bin='1', $numpart='3000',
		$lowpass='10', $highpass='1000', $numRef='3', $maxIter='30', $angStep='5', $tau='2', $partDiam='',
		$flat='on', $zero_mask=False,$mpinodes='2',$mpiprocs='4',$mpithreads='1',$mpimem='4', $commit='on')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('relion'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display

		$this->setJobType( 'partalign' ); //Job type stored in database
		$this->setOutputDirectory( 'align' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'rmaxlike' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Relion 2D Maximum Likelihood Alignment Launcher' ); // Shows up in the browser tab
		$this->setHeading( 'Relion 2D Maximum Likelihood Alignment' ); // shows at the top of the processing page
		$this->setExeFile( 'relionMaxlikeAlignment.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Relion_2D_Alignment" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( True ); // Shows the processing host params to set processors and memory

		//------ Add JavaScript functions needed for this form -------------------------//

		$javascript = "<script src='../js/viewer.js'></script>\n";
		// javascript to switch the defaults based on the stack
		$javascript .= "<script>\n";
		$javascript .= "function switchDefaults(stackval) {\n";
		$javascript .= "	var stackArray = stackval.split('|--|');\n";
		// remove commas from number : list($stackid, $apix, $boxsz, $totpart)
		$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
		$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
		$javascript .= "	document.viewerform.clip.value = stackArray[2];\n";
		$javascript .= "	document.viewerform.partDiam.value = Math.floor(document.viewerform.clip.value*stackArray[1]*2/6)*2;\n";

		// set binning
		$javascript .= "	var bestbin = Math.floor(stackArray[2]/80);\n";
		$javascript .= "	if (bestbin < 1) {\n";
		$javascript .= "		var bestbin = 1 ;}\n";
		$javascript .= "	document.viewerform.bin.value = bestbin;\n";
		//number of references is the natural log of the number of particles
		$javascript .= "	var bestref = Math.floor(Math.log(stackArray[3])/2)*2;\n";
		$javascript .= "	if (bestref < 2) {\n";
		$javascript .= "		var bestref = 2 ;}\n";
		$javascript .= "	document.viewerform.numRef.value = bestref;\n";

		// set particle & mask radius and lp
		$javascript .= "}\n";
		$javascript .= "</script>\n";
		
		$javascript .= "
			<script>
			function estimatetime() {
				var secperiter = 0.12037;
				var numpart = document.viewerform.numpart.value;
				var boxsize = document.viewerform.clip.value;
				var maxiter = document.viewerform.maxIter.value;
				var angle = document.viewerform.angStep.value;
				var nproc = document.viewerform.mpinodes.value
					* document.viewerform.mpiprocs.value
					* document.viewerform.mpithreads.value ;
				var numref = document.viewerform.numRef.value;
				
				var numpix = Math.pow(boxsize/document.viewerform.bin.value, 2);
				
				var calctime = (numpart/1000.0) * numref * numpix * maxiter * secperiter / angle / nproc;
				if (calctime < 70) {
					var time = Math.round(calctime*100.0)/100.0
					document.viewerform.timeestimate.value = time.toString()+' seconds';
				} else if (calctime < 3700) {
					var time = Math.round(calctime*0.6)/100.0
					document.viewerform.timeestimate.value = time.toString()+' minutes';
				} else if (calctime < 3700*24) {
					var time = Math.round(calctime/36.0)/100.0
					document.viewerform.timeestimate.value = time.toString()+' hours';
				} else {
					var time = Math.round(calctime/36.0/24.0)/100.0
					document.viewerform.timeestimate.value = time.toString()+' days';
				}
			}\n";
		$javascript .= "</script>\n";

		
		$this->addJavaScript( $javascript );

		//------ Set Parameters specific to the program that requires this new form -----//

		$particle = new particledata();
		$this->stackIds = $particle->getStackIds($expId);

		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "relion2DMaxlike" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")

		$params->addParam( "nompi", $nompi, "Disable MPI (single workstation mode)" );
		$params->addParam( "mpinodes", $mpinodes, "MPI Nodes", "onChange='estimatetime()'" );
		$params->addParam( "mpiprocs", $mpiprocs, "MPI Processors", "onChange='estimatetime()'" );
		$params->addParam( "mpithreads", $mpithreads, "MPI Threads", "onChange='estimatetime()'" );
		$params->addParam( "mpimem", $mpimem, "Memory per MPI Thread (Gb)" );

		$params->addParam( "stack", $stackId, "Select a stack of particles to use", "onChange='estimatetime()'" );
		$params->addParam( "clip", $clip, "Unbinned Clip Diameter", "onChange='estimatetime()'" );
		$params->addParam( "bin", $bin, "Particle Binning", "onChange='estimatetime()'" );
		$params->addParam( "numpart", $numpart, "Number of Particles" );
		$params->addParam( "lowpass", $lowpass, "Low Pass Filter Radius" );
		$params->addParam( "highpass", $highpass, "High Pass Filter Radius" );
		$params->addParam( "partDiam", $partDiam, "Particle Diameter" );
		$params->addParam( "numRef", $numRef, "Number of References", "onChange='estimatetime()'" );
		$params->addParam( "maxIter", $maxIter, "Maximum Number of Iterations", "onChange='estimatetime()'" );
		$params->addParam( "angStep", $angStep, "In-plane Rotation Angle Interval", "onChange='estimatetime()'" );
		$params->addParam( "tau", $tau, "Regularisation parameter" );
		$params->addParam( "flat", $flat, "Flatten Solvent on References " );
		$params->addParam( "zero_mask", $zero_mask, "Zero Masking");
		$params->addParam( "commit", $commit, "Commit to Database" );
		$params->addParam( "correctnorm",$correctnorm,"Perform normalization error correction");
		// Validations
		$params->addValidation( "numpart", "minval=4" );

	}

	// Generate a form for the parameters that are specific to this program
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft()
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		$fieldSize = 5;

		$html = "";

		$html .= "<br /><H4>Stack Selection</H4><hr />";

		if (!$this->stackIds) {
			$html .=  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	= "switchDefaults(this.value)";
			$particle 	= new particledata();
			$options 	= $particle->getStackOptions($this->stackIds);
			$html .= $params->insertStackedSelectField( "stack", $options,'', '', $onchange );
		}

		$html .= "
		<br />
		<H4>Data limiting numbers</H4>
		<hr />";

		$html .= $params->insertTextField( "clip", $fieldSize, "(pixels)", 'relion2DMaxlike.unbinnedclipdiameter' );
		$html .= $params->insertTextField( "bin", $fieldSize, '', 'relion2DMaxlike.particlebinning' );
		$html .= $params->insertTextField( "numpart", $fieldSize, '', 'relion2DMaxlike.numberofparticles' );

		$html .= "
		<br />
		<H4>Filters</H4>
		<hr />";

		$html .= $params->insertTextField( "lowpass", $fieldSize, "(&Aring;ngstroms)",'relion2DMaxlike.lowpassfilterradius' );
		$html .= $params->insertTextField( "highpass", $fieldSize, "(&Aring;ngstroms)", 'relion2DMaxlike.highpassfilterradius' );

		$html .= "
		<br />
		<H4>Alignment Parameters</H4>
		<hr />";

		$html .= $params->insertTextField( "partDiam", $fieldSize,"(&Aring;ngstroms)",'relion2DMaxlike.particlediameter' );

		$html .= $params->insertTextField( "numRef", $fieldSize,'','relion2DMaxlike.numberofreferences' );
		$html .= $params->insertTextField( "maxIter", $fieldSize,'','relion2DMaxlike.maxnumberofiterations' );
		$html .= $params->insertTextField( "angStep", $fieldSize,'(degrees)','relion2DMaxlike.angleinc' );
		$html .= $params->insertTextField( "tau", $fieldSize,'','appion.tau2fudge' );
		$html .= $params->insertCheckboxField("flat",'','relion2DMaxlike.flattensolvent');
		$html .= $params->insertCheckboxField("zero_mask",'','relion2DMaxlike.zeromasking');
		$html .= $params->insertCheckboxField("correctnorm",'','relion2DMaxlike.correctnorm');

		$html .=  "	<hr />\n";
		$html .=  "Time estimate: ";
		$html .=  "<INPUT TYPE='text' NAME='timeestimate' SIZE='16' disabled'>\n";
		$html .=  "<br/>\n";
		
		// When loading this page the first time, use the switchDefaults javascript function to set
		// form parameters based on the currently selected stack.
		if (!$_POST['process']) {
			$html .= "<script>switchDefaults(document.viewerform.stack.options[document.viewerform.stack.selectedIndex].value);</script>\n";
		}

		return $html;
	}

	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 5;

		$html .= "<H4>MPI Configuration</H4><hr />";

		$html .= $params->insertTextField( "mpinodes", $fieldSize, '', 'relion2DMaxlike.mpinodes' );
		$html .= $params->insertTextField( "mpiprocs", $fieldSize, '', 'relion2DMaxlike.mpiprocessors' );
		$html .= $params->insertTextField( "mpithreads", $fieldSize, '', 'relion2DMaxlike.mpithreads' );
		$html .= $params->insertTextField( "mpimem", $fieldSize, '', 'relion2DMaxlike.memoryperthread' );

		$html .= "<br />";
		$html .= $params->insertCheckboxField("nompi");

		$html .= "<br />";
		$html .= $params->insertCheckboxField("commit");

		return $html;
	}

	// Override the buildCommand function to adapt to the old python command
	// that uses "-" in params and parse the stack id.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );

		$params = $this->getFormParams();

		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		$command = $this->removeCommandFlag( $command, "stack" );
		$command = $this->addCommandFlag( $command, "stack", "stack", $stackid );

		// Set the clip diameter
		$command = $this->removeCommandFlag( $command, "clip" );
		$clip = $params->getParamValue( "clip" );
		$bin  = $params->getParamValue( "bin" );
		if ( $clip == $boxsz ) {
			// no clipping needed
			$clip = '';
		} else {
			// clipping requested
			$clip = floor($clip/($bin*2.0))*2;
			$command.= " --clip=$clip ";
		}

		$flat  = ($params->getParamValue('flat') == 'on' ) ? true : false;
		if (!$flat) {
			$command.= " --flat ";
		}

		// If the commit box is checked, add --commit, otherwise --no-commit
		$commit  = ($params->getParamValue('commit') == 'on' ) ? true : false;
		if (!$commit) {
			$command.= " --no-commit ";
		}

		$nompi  = ($params->getParamValue('nompi') == 'on' ) ? true : false;
		if ($nompi) {
			$command = $this->removeCommandFlag( $command, "mpithreads" );
			$command = $this->removeCommandFlag( $command, "mpimem" );
			$command = $this->removeCommandFlag( $command, "mpiprocs" );
			$command = $this->removeCommandFlag( $command, "mpinodes" );
#			$command.= " --nompi ";
		}

		return $command;
	}

	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );

		$params = $this->getFormParams();
		$nompi  = ($params->getParamValue('nompi') == 'on' ) ? true : false;
		if (!$nompi) {
			$phostinfo = $this->getProcessingHostInfo();
			$maxmem = $phostinfo['memorymax'];
			//$numnodes = $PROCESSING_HOSTS[0]['
			$mpithreads = $params->getParamValue('mpithreads');
			$mpimem = $params->getParamValue('mpimem');
			$mpiprocs = $params->getParamValue('mpiprocs');
			if ($mpiprocs*$mpithreads*$mpimem > $maxmem) {
				$msg .= "<B>Error:</B> Total MPI threads per node * MPI memory/thread is greater than max memory per node. "
					."<br>( $mpiprocs procs/node * $mpithreads threads/proc * $mpimem Gb/thread = "
					.$mpiprocs*$mpithreads*$mpimem." Gb > $maxmem Gb )";
				return $msg;
			}
		}

		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		$clip = $params->getParamValue('clip');
		if ($clip > $boxsz) {
			// Clip size too big
			$msg .= "<B>Error:</B> Clipping diameter ($clip pixels)"
			." must be less than or equal to the stack boxsize ($boxsz pixels)";
		}
		return $msg;
	}
}
?>
