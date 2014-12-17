<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$imageinfo=$_SESSION['imageinfo'];

class Protomo2CoarseAlignSummary extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $tiltseries='' )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		$tiltseries=$_SESSION['tiltseries'];
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Coarse Alignment Summary' );
		$this->setHeading( 'Protomo Coarse Alignment Summary' );
		$this->setExeFile( '' );
		$this->setGuideURL( "http://www.electrontomography.org/?page_id=317" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
	}
	
	// Display plots and gifs
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		global $outdir;
		global $runname;
		
		$corrpeak_files = glob("$outdir/$runname/gifs/correlations/c*.gif");
		$initial_tilt_files = glob("$outdir/$runname/gifs/tiltseries/i*.gif");
		$tilt_files = glob("$outdir/$runname/gifs/tiltseries/c*.gif");
		$rec_files = glob("$outdir/$runname/gifs/reconstructions/c*.gif");
		//print $outdir.'/'.$runname;
		//foreach(array_keys($corrpeak_files) as $paramName)
		//	echo $paramName . "<br>";
		//	echo $corrpeak_files["$paramName"] . "<br>";
		
		// Display Coarse Alignment Summary
		for ($i = 0; $i < max(count($corrpeak_files),count($rec_files)); $i++)
		{
			$ite=$i+1;
			$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_files[$i];
			$initial_tilt_gif = "loadimg.php?rawgif=1&filename=".$initial_tilt_files[$i];
			$tilt_gif = "loadimg.php?rawgif=1&filename=".$tilt_files[$i];
			$rec_gif = "loadimg.php?rawgif=1&filename=".$rec_files[$i];
			
			$html .= "
		<br />
		<center><H4>Tilt Series Correlation Peaks</H4></center>
		<br />";
			if (isset($corrpeak_files[$i])) {
				$html .= '<center><img src="'.$corrpeak_gif.'" alt="correlations" />'."<br /></center>";
				$html .= '<center>'.docpop('corrimageinfo_coarse', 'Image Info').'<br /><br /><hr /></center>';
			} else {
				$html .= "<center><b>Depiction Correlation Peak Gif for Coarse Alignment either failed to generate or is still processing</b></center>";
			}
			
			$html.='<br /><script type="text/javascript">
			function toggleMe(a){
			var e=document.getElementById(a);
			if(!e)return true;
			if(e.style.display=="none"){
			e.style.display="block"
			}
			else{
			e.style.display="none"
			}
			return true;
			}
			</script>
			
			<center><input type="button" style="width:150px;height:30px;" onclick="return toggleMe(\'para1\')" value="View Initial Tilt Series"></center><br>
			<div id="para1" style="display:none">';
			$html .= "
		<br />
		<center><H4>Initial Tilt Series Before Coarse Alignment</H4></center>
		<br />";
			if (isset($initial_tilt_files[$i])) {
				$html .= '<center><img src="'.$initial_tilt_gif.'" alt="tiltseries" />'."<br /></center>";
				$html .= '<center>'.docpop('initialtiltimageinfo_coarse', 'Image Info').'<br /><br /></center>';
			} else {
				$html .= "<center><b>Depiction Tilt Series Gif for unaligned tilt series either failed to generate or is still processing</b></center>";
			}
			$html .= '</div>';
			
			$html .= "
		<hr /><center><H4>Tilt Series After Coarse Alignment</H4></center>
		<br />";
			if (isset($tilt_files[$i])) {
				$html .= '<center><img src="'.$tilt_gif.'" alt="tiltseries" />'."<br /></center>";
				$html .= '<center>'.docpop('tiltimageinfo_coarse', 'Image Info').'<br /><br /><hr /></center>';
			} else {
				$html .= "<center><b>Depiction Tilt Series Gif for Coarse Alignment either failed to generate or is still processing</b></center>";
			}
			$html .= "
		<br />
		<center><H4>Tilt Series Reconstruction After Coarse Alignment</H4></center>
		<br />";
			if (isset($rec_files[$i])) {
				$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" />'."<br /></center>";
				$html .= '<center>'.docpop('reconimageinfo_coarse', 'Image Info').'<br /><br /><hr /></center>';
			} else {
				$html .= "<center><b>Depiction Reconstruction Gif for Coarse Alignment either failed to generate or is still processing</b></center>";
			}
		}
		
		// Only display link to next step in tomo processing if Coarse Alignment is complete
		if (count($rec_files) < 1)
		{
			$html .= "<br></br>
			<b><center>[Refresh this page after Coarse Alignment completes]</center><br></b>";
		} else {
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center>[Click here to continue onto <font size='4'>Refinement</font> if the Coarse Alignment results are satisfactory] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Coarse Alignment</font>]</center></b></a>";
		}
		
		return $html;
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $tiltseries;
		global $sessionname;
		global $runname;
		global $outdir;
		global $imageinfo;
		
		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $outdir;
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['erase_coarse'] = 1;
		$_SESSION['restart_cycle'] = '';
		
		return $html;
	}
}
?>
