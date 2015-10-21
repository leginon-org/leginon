<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
ini_set('display_errors', '0');     # don't show any errors...
error_reporting(E_ALL | E_STRICT);

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$imageinfo=$_SESSION['imageinfo'];

class Protomo2BatchSummary extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Batch Summary' );
		$this->setHeading( 'Protomo Batch Summary' );
		$this->setExeFile( '' );
		$this->setGuideURL( "http://www.electrontomography.org/?page_id=317" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
	}
	
	// Display CCMS plots
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		global $outdir;
		global $runname;
		$rundir=$outdir.'/'.$runname;
		$tilts = glob("$rundir/.t*");
		$qalist=array();
		foreach(array_keys($tilts) as $paramName)
			//echo $paramName . "<br>";
			//echo $tiltseries["$paramName"]. "<br>";
			//$ext = pathinfo($tiltseries["$paramName"], PATHINFO_EXTENSION);
			$qalist[]=pathinfo($tilts["$paramName"], PATHINFO_EXTENSION);
		$tiltlist=array();
		foreach(array_keys($qalist) as $paramName)
			$tiltlist[]=$rundir.'/tiltseries'.$paramName.'/media/quality_assessment/series'.$paramName.'_quality_assessment.gif';
		
		// Table of all of the CCMS plots for easy identification
		$html .= "
	<hr />
	<center><H4><b>CCMS Plot for Each Tilt-Series ".docpop('quality_assessment', '(Info)')."</b></H4></center>
	<hr />";
		
		$i = 0;
		$html .= '<table id="" class="display" cellspacing="0" border="1" width="100%">';
		$html .= "<tr>";
		if (count($qalist) > 0)
		{
		do {
			foreach ($qalist as $tilt)
			{
				$ite=$i+1;
				if ($ite <= count($qalist) AND $ite > 0) {
					$ccms_gif = "loadimg.php?rawgif=1&filename=".$rundir.'/tiltseries'.$qalist[$i].'/media/quality_assessment/series'.$qalist[$i].'_quality_assessment.gif';
					$html .= '<td><center><a href="protomo2BatchTiltSummary.php?rundir='.$rundir.'&tiltseries='.$qalist[$i].'" target="_blank"><img src="'.$ccms_gif.'"width="400" /></a></center></td>';
				}
				if ($ite % 3 == 0 OR $ite < 1) {
					$html .= "</tr><tr>";
					$i++;
					break;
				}
				$i++;
			}
		} while ($i < count($qalist));
		}
		$html .= '</tr><tr></table><br>';
		
		return $html;
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $sessionname;
		global $runname;
		global $outdir;
		global $imageinfo;

		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $outdir;
		$_SESSION['imageinfo'] = $imageinfo;

		return $html;
	}
}
?>
