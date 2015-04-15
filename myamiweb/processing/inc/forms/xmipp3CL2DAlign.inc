<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

class Xmipp3CL2DAlign extends BasicLayoutForm
{
	protected $stackIds;
	
	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='',$stackId='', $clip='', $bin='1', $numpart='3000', 
		$lowpass='10', $highpass='2000', $num_ref='20', $max_iter='15', $img2imgdist='correlation', 
		$img2clusterdist='minimum', $commit='on') 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('xmipp3CL2D'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display
		
		$this->setJobType( 'partalign' ); //Job type stored in database
		$this->setOutputDirectory( 'align' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'cl2d' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'XMIPP 3 CL2D Launcher' ); // Shows up in the browser tab
		$this->setHeading( 'Xmipp 3 Clustering 2D Alignment' ); // shows at the top of the processing page
		$this->setExeFile( 'runXmipp3CL2D.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Xmipp_3_Clustering_2D_Alignment" );
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
		// remove commas from number
		$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
		$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
		$javascript .= "	document.viewerform.clip.value = stackArray[2];\n";
		// set max last ring radius
		$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
		$javascript .= "	if (bestbin < 1) {\n";
		$javascript .= "		var bestbin = 1 ;}\n";
		$javascript .= "	document.viewerform.bin.value = bestbin;\n";
		// set particle & mask radius and lp
		$javascript .= "}\n";
		$javascript .= "
			function enablefastmode() {
				if (document.viewerform.fast.checked){
					document.viewerform.fastmode.disabled=false;
				} else {
					document.viewerform.fastmode.disabled=true;
				}
	
			}
			\n";
		$javascript .= "</script>\n";
		
		$this->addJavaScript( $javascript );
		
		//------ Set Parameters specific to the program that requires this new form -----//
		
		$particle = new particledata();
		$this->stackIds = $particle->getStackIds($expId);
	
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		// Add each of the parameters here. 
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "stack", $stackId, "Select a stack of particles to use" );
		$params->addParam( "clip", $clip, "Unbinned clip diameter" );
		$params->addParam( "bin", $bin, "Particle binning" );
		$params->addParam( "numpart", $numpart, "Number of particles" );
		$params->addParam( "lowpass", $lowpass, "Low Pass Filter Radius" );
		$params->addParam( "highpass", $highpass, "High Pass Filter Radius" );
		$params->addParam( "num_ref", $num_ref, "Number of references" );
		$params->addParam( "max-iter", $max_iter, "Maximum number of iterations" );
		$params->addParam( "img2imgdist", $img2imgdist, "Image to Image Distance" );
		$params->addParam( "img2clusterdist", $img2clusterdist, "Image to Cluster Distance" );
		$params->addParam( "commit", $commit, "Commit to Database" );
		
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

		$html.= $params->insertTextField( "lowpass", $fieldSize, "(&Aring;ngstroms)",'appion.lpstackval' );
		$html.= $params->insertTextField( "highpass", $fieldSize, "(&Aring;ngstroms)", 'appion.hpstackval' );

		$html .= "
	    <br />
	    <H4>Job Parameters</H4>
	    <hr />";

		$html.= $params->insertTextField( "num_ref", $fieldSize,'','appion.numrefcl2d' );
		$html.= $params->insertTextField( "max-iter", $fieldSize,'','appion.xmippmaxiter' );	

		$html.= "<I>Image to Image Distance:</I><br />\n";
		$html.= $params->insertRadioField("img2imgdist", "correntropy", "Correntropy", '', 'appion.image2imagedistance');	
		$html.= $params->insertRadioField("img2imgdist", "correlation", "Correlation", '', 'appion.image2imagedistance');	
		
		$html.= "<I>Image to Cluster Distance:</I><br />\n";
		$html.= $params->insertRadioField("img2clusterdist", "minimum", "Minimum", '', 'appion.image2clusterdistance');	
		$html.= $params->insertRadioField("img2clusterdist", "intracluster", "Intracluster", '', 'appion.image2clusterdistance');
		
		// When loading this page the first time, use the switchDefaults javascript function to set 
		// form parameters based on the currently selected stack.
		if (!$_POST['process']) {
			$html.= "<script>switchDefaults(document.viewerform.stack.options[document.viewerform.stack.selectedIndex].value);</script>\n";
		}
		
		return $html;
	}	
	
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		if (!$this->stackIds) {
			$html =  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	= "switchDefaults(this.value)";
			$particle 	= new particledata();
			$options 	= $particle->getStackOptions($this->stackIds);
			$html 		= $params->insertStackedSelectField( "stack", $options,'', '', $onchange );
		}
		
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
		
		// num_ref should be num-ref, but dashes don't work 
		// well in the php/javascript world, so change it here.
		$command = $this->removeCommandFlag( $command, "num_ref" );
		$num_ref = $params->getParamValue( "num_ref" );
		$command.= " --num-ref=".$num_ref." ";
		
		// same with numpart
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
		
		// set flag for image to image dist
		// if it is set to correlation, --correlation should be present,
		// otherwise no flag.
		$command = $this->removeCommandFlag( $command, "img2imgdist" );
		$img2imgdist  = $params->getParamValue( "img2imgdist" );
		if ($img2imgdist == "correlation") {
			$command.= " --correlation ";
		}
			
		// set flag for image to cluster dist
		// if it is set to minimum, --classical_multiref should be
		// present, otherwise no flag.
		$command = $this->removeCommandFlag( $command, "img2clusterdist" );
		$img2clusterdist  = $params->getParamValue( "img2clusterdist" );
		if ($img2clusterdist == "minimum") {
			$command.= " --classical_multiref ";
		}
		
		// If the commit box is checked, add --commit, otherwise --no-commit
		$commit  = ($params->getParamValue('commit') == 'on' ) ? true : false;
		if (!$commit) {
			$command.= " --no-commit ";
		}
		$command.= " --nproc=".$postArray['nodes']*$postArray['ppn']." ";
		return $command;		
	}
	
	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$params = $this->getFormParams();
		
		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		
		$clip = $params->getParamValue('clip');
		
		if ($clip > $boxsz) {
			// Clip size too big
			$msg .= "<B>Error:</B> Clipping diameter ($clip pixels)"
			." must be less than  or equal to the stack boxsize ($boxsz pixels)";
		}
		
		return $msg;
	}	
}
?>
