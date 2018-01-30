<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */


require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

class rubinsteinParticlePolisher extends BasicLayoutForm
{
	protected $stackIds;
	protected $unalignedDDStackIds;
	
	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='',$stackId='',  $ddstackId='', $expweight=true, $localavg=true,$localavgsigma='500', $smooth='1.0', $exaggerate='10',$framefirstali='0', $framefirstave='0', $rmax1='500',$rmax2='20',$bfactor='2000',$commit='on')

	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('rpp'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display
		
		$this->setJobType( 'particlepolishing' ); //Job type stored in database
		$this->setOutputDirectory( 'rpp' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'rpp' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Rubinstein Particle Polishing' ); // Shows up in the browser tab
		$this->setHeading( 'Rubinstein Particle Polishing' ); // shows at the top of the processing page
		$this->setExeFile( 'polishStack.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/rubinstein_Particle_Polishing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster(False ); // Shows the processing host params to set processors and memory
		
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

		$this->unalignedDDStackIds = $particle->getDDStackRunIdsUnAligned($expId);
	
		$params = $this->getFormParams();
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		// Add each of the parameters here. 
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "stack", $stackId, "Select a particle stack" );

		$params->addParam( "commit", $commit, "Commit to Database" );
		$params->addParam( "micrographs_per_job", $micrographs_per_job, "Micrographs per job");
		$params->addParam( "particleradius", $particleradius, "Particle radius");
		$params->addParam( "expweight", $expweight, "Exposure Weighting (Recommended)");
		$params->addParam( "localavg", $localavg, "Local averaging (Recommended)");
		
		$params->addParam( "ddstackid", $ddstackid, "Select an unaligned framestack");
		
		$params->addParam( "localavgsigma", $localavgsigma, "Local averaging weight standard deviation, default = 500");
		$params->addParam( "framefirstali", $framefirstali, "First frame to be used in alignment, default =0");
		$params->addParam( "framelastali", $frameliastali, "Last frame to be used in alignment, default = use all");
		$params->addParam( "framefirstave", $framefirstave, "First frame to be used in average of frames, default = 0");
		$params->addParam( "framelastave", $framelastave, "Last frame to be used in average of frames, default = use all");
		$params->addParam( "smooth", $smooth, "Specify the amount of smoothing, default = 1.0");
		$params->addParam( "exaggerate", $exaggerate, "Factor by which particle trajectories should be exaggerated, default = 10");
		$params->addParam( "expperframe", $expperframe, "Exposure per frame in electrons per Angstrom squared. Default = dose/numframes");
		$params->addParam( "rmax1", $rmax1, "Low resolution cutoff (Angstroms), default = 500");
		$params->addParam( "rmax2", $rmax2, "High resolution cutoff (Angstroms), default = 20");
		$params->addParam( "bfactor", $bfactor, "B-factor (in A**2) used for all alignment, default = 2000");
		$params->addParam( "total_dose", $total_dose, "Total dose for all frames, if value not saved in database");
	//	$params->addParam( "output_filetype", $output_filetype, "Output filetype");
		$params->addParam( "invertoutput", $invertoutput, "Invert output from movie densities");
		
		
		// Validations

		

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
            <H4>Required Parameters</H4>
            <hr />";

                $html.= $params->insertTextField( "particleradius", $fieldSize, "(angstroms)", 'appion.particleradius' );
                $html.= $params->insertTextField( "micrographs_per_job", $fieldSize, "", 'appion.micrographs_per_job' );
				$html.="<br>";
                $html.= $params->insertCheckBoxField( "expweight");
                $html.= $params->insertCheckBoxField( "localavg" );
                $html.="<br>";
				


		$html .= "
            <br />
            <H4>Optional Parameters</H4>
            <hr />";
		
                $html.= $params->insertTextField( "localavgsigma", $fieldSize, "", 'appion.localavgsigma' );
                $html.= $params->insertTextField( "framefirstali", $fieldSize, "", 'appion.framefirstali' );
                $html.= $params->insertTextField( "framelastali", $fieldSize, "", 'appion.framelastali' );
                $html.= $params->insertTextField( "framefirstave", $fieldSize, "", 'appion.framefirstave' );
                $html.= $params->insertTextField( "framelastave", $fieldSize, "", 'appion.framelastave' );
                $html.= $params->insertTextField( "smooth", $fieldSize, "", 'appion.smooth' );
                $html.= $params->insertTextField( "exaggerate", $fieldSize, "", 'appion.exaggerate' );

                
                $html.= $params->insertTextField( "expperframe", $fieldSize, "", 'appion.expperframe' );
                
                $html.= $params->insertTextField( "rmax1", $fieldSize, "", 'appion.rmax1' );
                $html.= $params->insertTextField( "rmax2", $fieldSize, "", 'appion.rmax2' );
                $html.= $params->insertTextField( "bfactor", $fieldSize, "", 'appion.bfactor' );
                $html.= $params->insertTextField( "total_dose", $fieldSize, "", 'appion.total_dose' );
       //         $html.= $params->insertTextField( "output_filetype", $fieldSize, "", 'appion.output_filetype' );
                $html.="<br>";
                $html.= $params->insertCheckBoxField( "invertoutput");

                $html .= "<br><hr>";
	
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
			$html .=  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	= "switchDefaults(this.value)";
			$particle 	= new particledata();
			$options 	= $particle->getStackOptions($this->stackIds);
			$html 		= $params->insertStackedSelectField( "stack", $options,'', '', $onchange );
			
			
		}
		$html .= "<br />";
		

		if(!$this->unalignedDDStackIds) {
			$html = "<font color='red'><B>No unaligned ddstacks for this session</B></FONT>\n";
		} else{
			$onchange = "switchDefaults(this.value)";
			$particle = new particledata();

			for($i=0;$i<count($this->unalignedDDStackIds);$i++)
			{

				
				$ddoptions[$this->unalignedDDStackIds[$i]['stackid']] = $this->unalignedDDStackIds[$i]['runname'];
			//	echo $ddoptions[$i];
			}


			$html .= $params->insertStackedSelectField("ddstackid",$ddoptions,'','',$onchange);
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
	
		// If the commit box is checked, add --commit, otherwise --no-commit
		$commit  = ($params->getParamValue('commit') == 'on' ) ? true : false;
		if (!$commit) {
			$command.= " --no-commit ";
		}
		//$command.= " --nproc=".$postArray['nodes']*$postArray['ppn']." ";
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
/*
		$clip = $params->getParamValue('clip');
		
		if ($clip > $boxsz) {
			// Clip size too big
			$msg .= "<B>Error:</B> Clipping diameter ($clip pixels)"
			." must be less than  or equal to the stack boxsize ($boxsz pixels)";
		}
*/

		$localavgsigma = $params->getParamValue('localavgsigma');
		$localavg = $params->getParamValue('localavg');
		$particleradius = $params->getParamValue('particleradius');
		$ddstackid = $params->getParamValue( "ddstackid" );
		$stackid = $params->getParamValue( "stackid" );
		$micrographs_per_job = $params->getParamValue('micrographs_per_job');

		if ($_POST['process'] != 'Just Show Command')
			$msg .="<B>Error: </B> This needs to be run from head node with job scheduler with pasted command.<br>";

		if($particleradius==='')
		{
		$msg .="<B>Error: </B> Select particle radius in angstroms<br>";
		}

		if ($stackid==='')
			$msg .="<B>Error: </B> Need particle stack to run<br>";

		if ($ddstackid==='')
			$msg .="<B>Error: </B> Need unaligned ddstack to run<br>";

		if($micrographs_per_job==='')
		{
			$msg.="<B>Error: </B> Select the number of micrographs per job<br>";
		}
		
		if((!empty($localavgsigma))&&(empty($localavg)))
		
		{

			
			$msg .="<B>Error: </B> Cannot select local averaging weight without local averaging selected<br>";
		}	

		//Default value for Local average sigma is 500
		if(($localavg===true)&&(empty($localavgsigma)))
		{
		$localavgsigma = 500;
		}


		return $msg;
	}	
}
?>
