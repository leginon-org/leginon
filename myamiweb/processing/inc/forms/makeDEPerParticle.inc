<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
// This class displays a form used to create a command similar to the following:
// uploadExternalRefine.py --rundir=/ami/data17/appion/11jan11a/recon/external_package_test 
// --runname=external_package_test --description="testing out external upload on 11jan11 data, emanrecon11, first iteration" 
// --projectid=224 --no-commit --expId=8397 --uploadIterations=1,2,3,4,5 --stackid=127 
// --modelid=19 --mass=3800 --apix=2.74 --box=160 --numberOfReferences=1 --numiter=1 --timestamp=11jul18z 
// --symid=25

require_once "basicLoopForm.inc";
//require_once "basicLayoutForm.inc";
require_once "DEAlignTable.inc";
require_once "inc/particledata.inc";

class makeDEPerParticle extends BasicLayoutForm
{
	protected $stackIds;
        protected $unalignedDDStackIds;
	
	// This is the constructor function. It is called as soon as this class is 
	// instantiated with a line like: $form = new CoolFeatureForm($expId, $extraHTML).
	// The first 2 parameters are needed for the BasicLayoutForm class that this class extends from.  
	// The rest of the parameters are specific to this form.
	
	function __construct( $expId, $extraHTML='', $stackId='', $alignment_correct='1', $alignment_quanta='3', $radiationdamage_compensate='1', $border='70',
	$hackcopy='', $usequeue='on', $queue_style='', $queue_scratch='', $njobs='4', $queue_ppn='2', $queue_name='', $queue_memory='4', $handlefiles='copy',
	$bad_cols='', $bad_rows='', $darkreference_transform='', $gainreference_transform='', $output_transform='', $wrapper='', $alignlabel='a' ) 
	{
		// You must first call the parent class(BasicLayoutForm) constructor. 
		// Pass it the $expId and $extraHTML variables. Errors and test results are passed through $extraHTML.
		
		parent::__construct($expId, $extraHTML);


		// Wrapper is currently defaulted from config.php without knowing what cluster
		// the job is going to be submitted to.  This is not the best to do.		
		// getAppionWrapper function comes from processing/inc/processing.inc
		$wrapper = ($wrapper) ? $wrapper: getAppionWrapper();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		// Set the publications to be references on the web pages
		$pubList = array('de_frame','appion');
		$this->setPublications( $pubList );
		// Job Type should be unique to Appion. Used in the database to determine the type of job being run.
		$this->setJobType( 'dealignparticles' ); 
		// The name of the folder that all runs of this job type will be stored in.
		$this->setOutputDirectory( 'framealignment' );  
		// A portion of the run name that will be common (by default) to all runs of this job type. A unique number is appended to individual run names.
		$this->setBaseRunName( 'perparticle' ); 
		// The title on the web page for this feature.
		$this->setTitle( 'Launcher for per particle DE aligner' ); 
		// The Heading on the web page for this feature.		
		$this->setHeading( 'Create Aligned and Dose Compensated Frame Sums' ); 
		// The name of the python executable file that this GUI corresponds to. It should be based on the AppionLoop class and located in the myami/appion/bin folder.
		$this->setExeFile( 'makeDEAlignedSum.py' );
		// A URL corresponding to a wiki page in the Appion User Guide with information on running this feature.  
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		// True to activate "test single image" field of Appion Loop parameters.
		$this->setTestable( True ); 
		// The output directory will be created in the Appion run directory rather than Leginon.
		$this->setUseLegOutDir( False );
		// Flag to hide the description field of the run parameters. True enables the description field.
		$this->setShowDesc( True ); 
		// Flag to use the cluster parameter form rather than the run parameter form.
		// Reconstructions and remote jobs use the cluster parameters, generic single processor jobs use run parameters.
		// Set to True to use Cluster Parameters
		$this->setUseCluster( False );

                //------ Add JavaScript functions needed for this form -------------------------//

                $javascript = "<script src='../js/viewer.js'></script>\n";
                // javascript to switch the defaults based on the stack
                $javascript .= "<script>\n";
               $javascript .= "function switchDefaults(stackval) {\n";
                $javascript .= "        var stackArray = stackval.split('|--|');\n";
                // remove commas from number
                $javascript .= "        stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
                $javascript .= "        document.viewerform.numpart.value = stackArray[3];\n";
                $javascript .= "        document.viewerform.clip.value = stackArray[2];\n";
                // set max last ring radius
                $javascript .= "        var bestbin = Math.floor(stackArray[2]/64);\n";
                $javascript .= "        if (bestbin < 1) {\n";
                $javascript .= "                var bestbin = 1 ;}\n";
                $javascript .= "        document.viewerform.bin.value = bestbin;\n";
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

	
		$particle = new particledata();
		$this->stackIds = $particle->getStackIds($expId);

                $this->unalignedDDStackIds = $particle->getDDStackRunIdsUnAligned($expId);


		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$this->DEAlignTable = new DEAlignTable($expId, $extraHTML, $alignment_correct, $alignment_quanta, $radiationdamage_compensate, $border,
	$hackcopy, $usequeue, $queue_style, $queue_scratch, $njobs, $queue_ppn, $queue_name, $queue_memory, $handlefiles,
	$bad_cols, $bad_rows, $darkreference_transform, $gainreference_transform, $output_transform, $wrapper, $alignlabel ); 
		$params = $this->DEAlignTable->getFormParams();
	//	$params = $this->getFormParams();
	//	var_dump($params);
		$params->setHelpSection( "makeDEAlignedSum" );
		$params->addParam( "stack", $stackId, "Select a particle stack" );


	}
	
	// Generate a form for the parameters that are specific to this program 
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft() 
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormRight($displayAdvanced=False)
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$html .= $this->DEAlignTable->generateForm($enable=true);
	
		// When loading this page the first time, use the switchDefaults javascript function to set 
                // form parameters based on the currently selected stack.
                if (!$_POST['process']) {
                        $html.= "<script>switchDefaults(document.viewerform.stack.options[document.viewerform.stack.selectedIndex].value);</script>\n";
                }

		$html.="this is another test";
	
		return $html;
	}	

	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
              $params = $this->DEAlignTable->getFormParams();
		if (!$this->stackIds) {
			$html .=  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	= "switchDefaults(this.value)";
			$particle 	= new particledata();
			$options 	= $particle->getStackOptions($this->stackIds);
	                $html           = $params->insertStackedSelectField( "stack", $options,'', '', $onchange );
	
		}
		$html .= "<br />";

		return $html;
	}

	// Override the validate function so that we can verify parameters from this subform
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$msg .= $this->DEAlignTable->validate( $postArray );	


		 $params = $this->getFormParams();
                // Extract the stack id from the stack string
		return $msg;
	}

	public function buildCommand($postArray) {
		// multi-thread findem by template

		$command .= parent::buildCommand($postArray);

		$command .= $this->DEAlignTable->buildCommand( $postArray);

              $params = $this->DEAlignTable->getFormParams();

                // Extract the stack id from the stack string
                $tempstack = $params->getParamValue( "stack" );
				//echo 'stack var is '.var_dump($tempstack)."<br><br>";
				//echo 'params var is '.var_dump($params)."<br><br>";

                list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$tempstack);

				$command = $this->DEAlignTable->removeCommandFlag( $command, "stack" );
                $command = $this->DEAlignTable->addCommandFlag( $command, "stackid","stackid", $stackid );
				
					

		return $command;
	}
		
}

?>
