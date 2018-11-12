<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
ini_set('display_errors', '0');     # don't show any errors...
error_reporting(E_ALL | E_STRICT);

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

$page = $_SERVER['REQUEST_URI'];
header("Refresh: 300; URL=$page");

session_start();
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$imageinfo=$_SESSION['imageinfo'];
$refine=$_GET['refine'];

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
		$this->setGuideURL( "https://github.com/nysbc/appion-protomo#example" );
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
		global $refine;
		$tilts = glob("$outdir/tiltseries*/.tiltseries*");
		$qalist=array();
		foreach(array_keys($tilts) as $paramName)
			$qalist[]=pathinfo($tilts["$paramName"], PATHINFO_EXTENSION);
		
		
		
		if (isset($_GET['refine']))
		{
				// Table of all of the CCMS plots for easy identification
				$html .= "
			<hr />
			<center><H4><b>CCMS Plot for Each Tilt-Series ".docpop('quality_assessment_batch', '(Info)')."</b></H4></center>
			<hr />";
				
				$i = 0;
				$j = -1;
				$numcolumns=3;
				$html .= '<table id="" class="display" cellspacing="0" border="1" width="100%">';
				$html .= "<tr>";
				if (count($qalist) > 0)
				{
				do {
					foreach ($qalist as $tilt)
					{
						$ite=$i+1;
						if ($ite <= count($qalist) AND $ite > 0) {
							$html .= '<th><a href="protomo2BatchTiltSummary.php?expId='.$_GET['expId'].'&rundir='.$outdir.'&tiltseries='.$qalist[$i].'" target="_blank">Tilt-Series #'.intval($qalist[$i]).'</a></th>';
						}
						if ($ite % $numcolumns == 0 OR $ite < 1) {
							$html .= "</tr><tr>";
							$j++;
							break;
						}
						$i++;
					}
					$i = 0 + $numcolumns*$j;
					foreach ($qalist as $tilt)
					{
						$ite=$i+1;
						if ($ite <= count($qalist) AND $ite > 0) {
							$ccms_gif = "loadimg.php?rawgif=1&filename=".$outdir.'/tiltseries'.$qalist[$i].'/media/quality_assessment/series'.$qalist[$i].'_quality_assessment.gif';
							$html .= '<td><center><a href="protomo2BatchTiltSummary.php?expId='.$_GET['expId'].'&rundir='.$outdir.'&tiltseries='.$qalist[$i].'" target="_blank"><img src="'.$ccms_gif.'"width="350" /></a></center></td>';
						}
						if ($ite % $numcolumns == 0 OR $ite < 1) {
							$html .= "</tr><tr>";
							$i++;
							break;
						}
						$i++;
					}
				} while ($i < count($qalist));
				}
				$html .= '</tr><tr></table><br>';
				
				$html .= "<br>
					<b><center>[If you wish to re-do an alignment with different parameters, remove the corresponding directory:</center></b>";
				$html .= "
					<b><center>".rtrim($outdir,'/')."/tiltseriesXXXX</center></b>";
				$html .= "
					<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchForm'><b><center><font size='5'>←</font> Then click here to go back]</center></b></a>";
		}else{
				// Table of all of the correlation peaks for easy identification
				$html .= "
			<hr />
			<center><H4><b>Coarse Alignment Correlation Peaks for Each Tilt-Series ".docpop('corrimageinfo_coarse', '(Info)')."</b></H4></center>
			<hr />";
				
				$i = 0;
				$j = -1;
				$numcolumns=5;
				$html .= '<table id="" class="display" cellspacing="0" border="1" width="100%">';
				$html .= "<tr>";
				if (count($qalist) > 0)
				{
				do {
					foreach ($qalist as $tilt)
					{
						$ite=$i+1;
						if ($ite <= count($qalist) AND $ite > 0) {
							$html .= '<th><a href="protomo2BatchCoarseSummary.php?rundir='.$outdir.'&tiltseries='.$qalist[$i].'" target="_blank">Tilt-Series #'.intval($qalist[$i]).'</a></th>';
						}
						if ($ite % $numcolumns == 0 OR $ite < 1) {
							$html .= "</tr><tr>";
							$j++;
							break;
						}
						$i++;
					}
					$i = 0 + $numcolumns*$j;
					foreach ($qalist as $tilt)
					{
						$ite=$i+1;
						if ($ite <= count($qalist) AND $ite > 0) {
							$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$outdir.'/tiltseries'.$qalist[$i].'/media/correlations/coarse_series'.$qalist[$i].'00_cor.gif';
							$html .= '<td><center><a href="protomo2BatchCoarseSummary.php?rundir='.$outdir.'&tiltseries='.$qalist[$i].'" target="_blank"><img src="'.$corrpeak_gif.'"/></a></center></td>';
						}
						if ($ite % $numcolumns == 0 OR $ite < 1) {
							$html .= "</tr><tr>";
							$i++;
							break;
						}
						$i++;
					}
				} while ($i < count($qalist));
				}
				$html .= '</tr><tr></table><br>';
				
				$html .= "<br></br>
					<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchSummary&refine=1'><b><center>[Click here to continue on to view <font size='4'>Refinement Results</font> if the Coarse Alignment results are satisfactory] <font size='5'>→</font></center></b></a>";
				$html .= "<br>
					<b><center>[If you with wish to re-do an alignment with different parameters, remove the corresponding directory:</center></b>";
				$html .= "
					<b><center>".rtrim($outdir,'/')."/tiltseriesXXXX</center></b>";
				$html .= "
					<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchForm'><b><center><font size='5'>←</font> Then click here to go back]</center></b></a>";
		}
		return $html;
	}	
	
	// Use form footer to set $_SESSION variables
	public function generateFormFooter( $postArray )
	{
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
