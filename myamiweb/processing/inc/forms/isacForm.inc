<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

class IsacForm extends BasicLayoutForm
{
	protected $stackIds;
	protected $alignStackIds;
	
	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='', $stackId='', $alignStackId='', $clip='', $bin='1', $numpart='3000', 
		$lp='10', $hp='2000', $generations='2', $thld_grp='10', $img_per_grp='100', 
		$stab_ali='5', $ir='', $ou='', $rs='', $ts='', $xr='', $yr='', $maxit='', $FL='',
		$FH='', $FF='', $init_iter='', $main_iter='', $iter_reali='', $match_first='', $max_round='', 
		$match_second='', $indep_run='', $use_align_stack="", $thld_err="" ) 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('isac'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display
		
		$this->setJobType( 'sparxisac' ); //Job type stored in database
		$this->setOutputDirectory( 'align' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'ISAC' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'ISAC Launcher' ); // Shows up in the browser tab
		$this->setHeading( 'Iterative Stable Alignment and Clustering (ISAC)' ); // shows at the top of the processing page
		$this->setExeFile( 'runJob.py' ); // added to the command string
		$this->setGuideURL( "http://http://ami.scripps.edu/redmine/projects/appion/wiki/ISAC_Iterative_Stable_Alignment_and_Clustering" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( True ); // Shows the processing host params to set processors and memory
		$this->setShowRemoteOutDir( True ); // Shows the remote out dir field in cluster params (since using apRemoteJob.py which expects it)
		$this->setEnableLocalHost( True ); // ISAC needs to know the local helper host to rsync the results back to the local rundir
		
		//------ Add JavaScript functions needed for this form -------------------------//
		
		$javascript = "<script src='../js/viewer.js'></script>\n";
		// javascript to switch the defaults based on the stack
		$javascript .= "<script>\n";
		$javascript .= "function switchDefaults(stackval) {\n";
		$javascript .= "	var stackArray = stackval.split('|--|');\n";
		// remove commas from number
		$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
		$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
		$javascript .= "	document.viewerform.clip.value = stackArray[2];\n";
		//$javascript .= "	document.viewerform.ou.value = Math.floor(stackArray[2]/2) - 2;\n";
		// set max last ring radius
		$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
		$javascript .= "	if (bestbin < 1) {\n";
		$javascript .= "		var bestbin = 1 ;}\n";
		$javascript .= "	document.viewerform.bin.value = bestbin;\n";
		// set particle & mask radius and lp
		$javascript .= "}\n";
		$javascript .= "
			function useAlignedStack() {
				if (document.viewerform.use_align_stack.checked){
					document.viewerform.stack.disabled=true;
					document.viewerform.alignstack.disabled=false;
					switchDefaults(document.viewerform.alignstack.value)
				} else {
					document.viewerform.stack.disabled=false;
					document.viewerform.alignstack.disabled=true;
					switchDefaults(document.viewerform.stack.value)
				}
	
			}
			\n";
		$javascript .= "</script>\n";
		
		$this->addJavaScript( $javascript );
		
		//------ Set Parameters specific to the program that requires this new form -----//
		
		$particle 				= new particledata();
		$this->stackIds 		= $particle->getStackIds($expId);
		$this->alignStackIds 	= $particle->getAlignStackIds($expId, False);
	
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		// Add each of the parameters here. 
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "stack", $stackId, "Select a stack of particles to use" );
		$params->addParam( "alignstack", $alignStackId, "Select an aligned stack of particles to use" );
		$params->addParam( "clip", $clip, "Unbinned clip diameter" );
		$params->addParam( "bin", $bin, "Particle binning" );
		$params->addParam( "numpart", $numpart, "Number of particles" );
		$params->addParam( "lp", $lp, "Low Pass Filter Radius" );
		$params->addParam( "hp", $hp, "High Pass Filter Radius" );

		// Isac params that are most often used
		$params->addParam( "generations", $generations, "Generations" );
		$params->addParam( "thld_grp", $thld_grp, "Minimum class size" );
		$params->addParam( "img_per_grp", $img_per_grp, "Maximum class size" );
		$params->addParam( "stab_ali", $stab_ali, "Stability alignments" );
		
		// Advanced Isac Params
		$params->addParam( "ir", $ir, "Inner radius" );
		$params->addParam( "ou", $ou, "Outer radius" );
		$params->addParam( "rs", $rs, "Ring step" );
		$params->addParam( "ts", $ts, "Translational search step" );
		$params->addParam( "xr", $xr, "Translational search x range" );
		$params->addParam( "yr", $yr, "Translational search y range" );
		$params->addParam( "maxit", $maxit, "Iterations" );
		$params->addParam( "FL", $FL, "Lowest stopband frequency" );
		$params->addParam( "FH", $FH, "Highest stopband frequency" );
		$params->addParam( "FF", $FF, "Tangent filter falloff" );
		$params->addParam( "init_iter", $init_iter, "Initial iterations" );
		$params->addParam( "main_iter", $main_iter, "Main iterations" );
		$params->addParam( "iter_reali", $iter_reali, "iter_reali" );
		$params->addParam( "match_first", $match_first, "First phase iterations" );
		$params->addParam( "max_round", $max_round, "First phase rounds" );
		$params->addParam( "match_second", $match_second, "Second phase iterations" );
		$params->addParam( "indep_run", $indep_run, "m-way matching level" );
		$params->addParam( "use_align_stack", $use_align_stack, "Use an Aligned Stack" );
		$params->addParam( "thld_err", $thld_err, "Threshold of pixel error" );
		
		// Validations
		$params->addValidation( "numpart", "minval=4" );
	}
		
	// Generate a form for the parameters that are specific to this program 
	// This overrides the generateAdditionalFormRight() 
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html .= "
	    <br />
	    <H4>Limiting numbers</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "clip", $fieldSize, "(pixels)", 'appion.clipdiam' );
		$html.= $params->insertTextField( "bin", $fieldSize, '', 'appion.partbin' );
		$html.= $params->insertTextField( "numpart", $fieldSize );
				
		$html .= "
	    <br />
	    <H4>Filters</H4>
	    <hr />";

		$html.= $params->insertTextField( "lp", $fieldSize, "(&Aring;ngstroms)",'appion.lpstackval' );
		$html.= $params->insertTextField( "hp", $fieldSize, "(&Aring;ngstroms)", 'appion.hpstackval' );

		$html .= "
	    <br />
	    <H4>ISAC Parameters</H4>
	    <hr />";

		$html.= $params->insertTextField( "generations", $fieldSize, '', 'isac.generations' );
		$html.= $params->insertTextField( "thld_grp", $fieldSize, '', 'isac.thld_grp' );
		$html.= $params->insertTextField( "img_per_grp", $fieldSize, '', 'isac.img_per_grp' );
		$html.= $params->insertTextField( "stab_ali", $fieldSize, '', 'isac.stab_ali' );
		$html.= $params->insertTextField( "ir", $fieldSize, '', 'isac.ir' );
		$html.= $params->insertTextField( "ou", $fieldSize, '', 'isac.ou' );
		
		$html .= "
	    <br />
	    <H4>Advanced ISAC Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "rs", $fieldSize, '', 'isac.rs' );
		$html.= $params->insertTextField( "ts", $fieldSize, '', 'isac.ts' );
		$html.= $params->insertTextField( "xr", $fieldSize, '', 'isac.xr' );
		$html.= $params->insertTextField( "yr", $fieldSize, '', 'isac.yr' );
		$html.= $params->insertTextField( "maxit", $fieldSize, '', 'isac.maxit' );
		$html.= $params->insertTextField( "FL", $fieldSize, '', 'isac.FL' );
		$html.= $params->insertTextField( "FH", $fieldSize, '', 'isac.FH' );
		$html.= $params->insertTextField( "FF", $fieldSize, '', 'isac.FF' );
		$html.= $params->insertTextField( "init_iter", $fieldSize, '', 'isac.init_iter' );
		$html.= $params->insertTextField( "main_iter", $fieldSize, '', 'isac.main_iter' );
		$html.= $params->insertTextField( "iter_reali", $fieldSize, '', 'isac.iter_reali' );
		$html.= $params->insertTextField( "match_first", $fieldSize, '', 'isac.match_first' );
		$html.= $params->insertTextField( "max_round", $fieldSize, '', 'isac.max_round' );
		$html.= $params->insertTextField( "match_second", $fieldSize, '', 'isac.match_second' );
		$html.= $params->insertTextField( "indep_run", $fieldSize, '', 'isac.indep_run' );
		$html.= $params->insertTextField( "thld_err", $fieldSize, '', 'isac.thld_err' );
		
		// When loading this page the first time, use the switchDefaults javascript function to set 
		// form parameters based on the currently selected stack.
		if (!$_POST['process']) {
			// TODO: this checkbox is being set to on after switching to off and then reloading page...
			if ( $params->getParamValue( "use_align_stack" ) == "on" ) {
				$html.= "<script>document.viewerform.stack.disabled=true;switchDefaults(document.viewerform.alignstack.options[document.viewerform.alignstack.selectedIndex].value);</script>\n";
			} else {
				$html.= "<script>document.viewerform.alignstack.disabled=true;switchDefaults(document.viewerform.stack.options[document.viewerform.stack.selectedIndex].value);</script>\n";
			}
		}
		
		return $html;
	}	
	
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$particle 	= new particledata();
		
		$html .= "
	    <br />
	    <H4>Stack Selection</H4>
	    <hr />";
		
		
		if (!$this->stackIds) {
			$html .=  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	= "switchDefaults(this.value)";
			$options 	= $particle->getStackOptions($this->stackIds);
			$html 		.= $params->insertStackedSelectField( "stack", $options,'', '', $onchange );
		}
		
		$html .= "<br />";
		
		$html .= $params->insertCheckboxField("use_align_stack", '', 'isac.use_align_stack', "useAlignedStack()" );
		//$html .= "<br />";
		
		if (!$this->alignStackIds) {
			$html .=  "<font color='red'><B>No Aligned Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	  = "switchDefaults(this.value)";
			$alignoptions = $particle->getAlignedStackOptions($this->alignStackIds);
			$html 		  .= $params->insertStackedSelectField( "alignstack", $alignoptions,'', 'isac.alignstack', $onchange );
		}
		
		return $html;
	}
	
	// Override the buildCommand function to adapt to the old python command
	// that uses "-" in params and parse the stack id.
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		$params = $this->getFormParams();
		
		// Determine if we should use the stack or alignedstack id
		$command = $this->removeCommandFlag( $command, "use_align_stack" );
		$command = $this->removeCommandFlag( $command, "stack" );
		$command = $this->removeCommandFlag( $command, "alignstack" );
		$use_align_stack = $params->getParamValue( "use_align_stack" );

		if ($use_align_stack == 'on') {
			$alignstack = $params->getParamValue( "alignstack" );
			list($alignstackid, $alignapix, $alignboxsz, $aligntotpart) = preg_split('%\|--\|%',$alignstack);
			$command = $this->addCommandFlag( $command, "alignstack", "alignstack", $alignstackid );
		} else {
			$stack = $params->getParamValue( "stack" );
			list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
			$command = $this->addCommandFlag( $command, "stack", "stack", $stackid );			
		}
		
		// can't use dashes - in keys, so add the dash here
		$command = $this->removeCommandFlag( $command, "numpart" );
		$numpart = $params->getParamValue( "numpart" );
		$command.= " --num-part=".$numpart." ";
		
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
		
		return $command;		
	}
	
	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$params = $this->getFormParams();
		
		// Extract the stack id from the stack string
		$use_align_stack = $params->getParamValue( "use_align_stack" );
		if ($use_align_stack == 'on') {
			$stack = $params->getParamValue( "alignstack" );
		} else {
			$stack = $params->getParamValue( "stack" );
		} 
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		
		$clip = $params->getParamValue('clip');
		
		if ($clip > $boxsz) {
			// Clip size too big
			$msg .= "<B>Error:</B> Clipping diameter ($clip pixels)"
			." must be less than  or equal to the stack boxsize ($boxsz pixels)";
		}
		
		return $msg;
	}	
	
	// Define this function to create a list of files that need to be copied
	// to the remote cluster before running. This function will be called by the 
	// basicForm class when runAppionLoop.php calls copyFilesToCluster().
	public function setFilesToCopy()
	{
		$params = $this->getFormParams();
		
		// TODO: stack or align stack?
		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		
		// Get the stack file path
		$particle  = new particledata();
		$stackdata = $particle->getStackParams($stackid);
		$stackfile = $stackdata['path']."/".$stackdata['name'];
		
		// Get the stack file path and name
		$this->filesToCopy[] = $stackfile;
	}
	
	public function copyFilesToCluster( $host, $directory )
	{
		// This is a bit different from the basicForm class, because we need to copy
		// the stack from its current location to the cluster. However it looks like
		// apSparxIsac.py is looking up the stack location in the DB so not sure where 
		// we should be copying to....
	}
}
?>
