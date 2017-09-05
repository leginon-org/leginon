<?php

/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

/* Boxsize rules:
* (1) no prime factor greater than 11
* (2) if greater than 4^x, must be multiple of 2^x,
* (3) surely no one will make a stack bigger than 5000 pixels
*/

$goodboxes = array(
	4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64, 72, 80, 96,
	112, 120, 128, 144, 160, 176, 192, 200, 224, 240, 256, 288,
	320, 336, 352, 384, 400, 432, 448, 480, 512, 560, 576, 640,
	672, 704, 720, 768, 800, 864, 896, 960, 1024, 1120, 1152,
	1280, 1344, 1408, 1440, 1536, 1568, 1600, 1728, 1760, 1792,
	1920, 2016, 2048, 2112, 2240, 2304, 2400, 2464, 2560, 2592,
	2688, 2816, 2880, 3072, 3136, 3168, 3200, 3360, 3456, 3520,
	3584, 3840, 3872, 4000, 4032, 4096, 4224, 4480, 4608, 4800,
	4928, 5120,
);

class QuickStackForm extends BasicLayoutForm
{
	protected $stackIds;

	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='', $selectid='', $initboxsize='', $finalboxsize='',
		$lowpass='10', $highpass='1000', $commit='on', $invert='on', $overridebox='', $mode='both')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('appion'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display

		$this->setJobType( 'makestack' ); //Job type stored in database
		$this->setOutputDirectory( 'stacks' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'qstack' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Quick Stack Launcher' ); // Shows up in the browser tab
		$this->setHeading( 'Quick Stack' ); // shows at the top of the processing page
		$this->setExeFile( 'quickStack.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Quick_Stack" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False ); // Shows the processing host params to set processors and memory

		//------ Add JavaScript functions needed for this form -------------------------//

		$javascript = "<script src='../js/viewer.js'></script>\n";
		// javascript to switch the defaults based on the stack
		$javascript .= "<script>\n";
		$javascript .= "function binningCheck() {\n";
		$javascript .= "	document.viewerform.init-boxsize.value = stackArray[3];\n";
		$javascript .= "	document.viewerform.final-boxsize.value = stackArray[2];\n";
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

		$this->addJavaScript( $javascript );

		//------ Set Parameters specific to the program that requires this new form -----//

		$particle = new particledata();
		$this->selectionIds = $particle->getParticleRunIds($expId);

		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "quickStack" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")

		$req = "<font color='red'><b>**</b></font>";

		$params->addParam( "selectid", $selectid, "Select a Particle Run", "onChange='binningCheck()'" );
		$params->addParam( "init-boxsize", $initboxsize, "$req Initial Micrograph Boxsize", "onChange='binningCheck()'" );
		$params->addParam( "final-boxsize", $finalboxsize, "$req Final Reduced Particle Boxsize", "onChange='binningCheck()'" );
		//$params->addParam( "lowpass", $lowpass, "Low Pass Filter Radius" );
		//$params->addParam( "highpass", $highpass, "High Pass Filter Radius" );
		$params->addParam( "commit", $commit, "Commit to Database" );
		$params->addParam( "invert", $invert, "Invert image density" );
		$params->addParam( "mode", $mode, "Type of stacks to produce" );

		$params->addParam( "overridebox", $overridebox, "force override suggested boxsizes" );

		//$params->addParam( "correctnorm", $correctnorm, "Perform normalization error correction");
		// Validations
		$params->addValidation( "init-boxsize", "minval=8" );
		$params->addValidation( "final-boxsize", "minval=4" );
		//$params->addValidation( "description", "req" );
		$params->addValidation( "selectid", "num" );
		$params->addValidation( "mode", "req" );

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
		$req = "<font color='red'><B>**</b></font>";

		$html .= "<H4>Particle Selection</H4>\n\n";

		if (!$this->selectionIds) {
			$html .=  "<font color='red'><B>No Particles for this Session</B></FONT>\n";
		} else {
			$particle = new particledata();
			$html .= $req." ";
			$html .= docpop('stackparticles','Particles:');
			$html .= "<select name='selectid' onchange='fromstackToNone()'>\n";
			//$html .= "<option value='0'>None</option>\n";
			foreach ($this->selectionIds as $partrun){
				$partrunid=$partrun['DEF_id'];
				$runname=$partrun['name'];
				$partstats=$particle->getStats($partrunid);
				$numPart = $partstats['totparticles'];
				if ($numPart == 0)
					continue;
				$totparts=commafy($numPart);
				$html .= "<option value='$partrunid'";
				// select previously set part on resubmit
				if ($partrunval==$partrunid) {
					$html .= " selected";
				} elseif ($partrunval==-1) {
					$html .= " selected";
					$partrunval=$partrunid;
				}
				$html .=">$runname ($totparts parts)</option>\n";
			}
			$html .= "</select>\n";
		}

		$html .= "<br /><hr/><H4>Particle box sizes</H4>";

		$html .= $params->insertTextField( "init-boxsize", $fieldSize, "(pixels)", 'quickStack.initboxsize' );
		$html .= $params->insertTextField( "final-boxsize", $fieldSize, "(pixels)", 'quickStack.finalboxsize' );
		$html .= $params->insertCheckboxField("overridebox");

		$html .= "<hr/><h4>Density modifications:</h4>\n";

		$html.= $params->insertRadioField("invert", "", "Stain - do NOT change particle density (particles are already white)","");
		$html.= $params->insertRadioField("invert", "on", "Vitreous ice - invert the particle density","");

		$html .= "<hr/><h4>Stack format:</h4>\n";

		$html.= $params->insertRadioField("mode", "relion", "Relion only &ndash; MRC stacks, star file with CTF info, faster, no database", "");
		$html.= $params->insertRadioField("mode", "appion", "Appion only &ndash; IMAGIC stack file, no CTF, upload data to database", "");
		$html.= $params->insertRadioField("mode", "both", "Both &ndash; create both MRC and IMAGIC stack, uses more file space","");

		/*
		$html .= "
		<br />
		<H4>Normalization</H4>
		<hr />";
		$html .= $params->insertCheckboxField("correctnorm",'','quickStack.correctnorm');
		*/

		return $html;
	}

	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 5;

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
		$selectid = $params->getParamValue( "selectid" );
		//$command = $this->removeCommandFlag( $command, "stack" );
		//$command = $this->addCommandFlag( $command, "stack", "stack", $stackid );
		$command = $this->removeCommandFlag( $command, "override" );


		// Set the clip diameter
		$bin  = $params->getParamValue( "bin" );

		// If the commit box is checked, add --commit, otherwise --no-commit
		$commit  = ($params->getParamValue('commit') == 'on' ) ? true : false;
		if (!$commit) {
			$command.= " --no-commit ";
		}

		return $command;
	}

	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );

		$params = $this->getFormParams();

		$initboxsize = $params->getParamValue( "init-boxsize" );
		$finalboxsize = $params->getParamValue( "final-boxsize" );
		global $goodboxes;
		$overridebox = $params->getParamValue( "overridebox" );
		if ($overridebox != 'on') {
			foreach ($goodboxes as $box) {
				if ($box == $initboxsize)
					break;
				elseif ($box > $initboxsize) {
					$bigbox = $box;
					$msg = "<b>ERROR:</b> Bad prime number in initial boxsize, "
						."try using $smallbox or $bigbox instead or check 'override box size' to force";
					return $msg;
				}
				$smallbox = $box;
			}
			foreach ($goodboxes as $box) {
				if ($box == $finalboxsize)
					break;
				elseif ($box > $finalboxsize) {
					$bigbox = $box;
					$msg = "<b>ERROR:</b> Bad prime number in final boxsize, "
						."try using $smallbox or $bigbox instead or check 'override box size' to force";
					return $msg;
				}
				$smallbox = $box;
			}
		}
		return $msg;
	}
}
?>
