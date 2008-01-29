<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see	http://ami.scripps.edu/software/leginon-license
 */

require_once "config_processing.php";
require_once "inc/mysql.inc";

define(PARTICLE_DB_HOST, $PARTICLE_DB_HOST);
define(PARTICLE_DB_USER, $PARTICLE_DB_USER);
define(PARTICLE_DB_PASS, $PARTICLE_DB_PASS);
define(PARTICLE_DB, $PARTICLE_DB);

class particledata {

	var $crlf="\n";
	var $baseurl=PROCESSING_BASE_URL;

	function particledata () {
		$this->mysql = new mysql(
					PARTICLE_DB_HOST,
					PARTICLE_DB_USER,
					PARTICLE_DB_PASS,
					PARTICLE_DB);
	}

	function displayParameters ($title,$params,$exclude_fields) {
		//standard parameter table display

		//Array of $params keys that are shown as a link to another report
		$links=array(
			'stackId'=>'stackreport.php?sId='
			,'particleSelection'=>'particlerunreport.php?rId='
		);

		echo "<h4>".$title."</h4>";
		echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
		$selection_fields = array_keys($params);
		foreach($selection_fields as $key) {
			$exclude = false;
			foreach($exclude_fields as $bad) {
				if ($key == $bad) {
					$exclude = true;
					break;
				}
			}
			//Display only non-excluded fields
			if (!$exclude) {
				// Clean up referenced key for display
				$displaykeyarray = explode('Data|',$key);
				if (count($displaykeyarray)>1) {
					$displaykey = array_pop($displaykeyarray);
					$refkey = array_pop($displaykeyarray);
				} else {
					$displaykeyarray = explode('DEF_',$key);
					$displaykey = array_pop($displaykeyarray);
					$refkey = $displaykey;
				}
				// Display only non-null params
				if (gettype($params[$key])!='NULL') {
					echo "<tr>\n";
					echo "</td>";
					echo "<td><span class='datafield0'>$displaykey</span></td>";
					echo "<td>";
					$type='text';
					foreach(array_keys($links) as $linkkey) {
						if ($linkkey ==$refkey) {
							$type='link';
							$link = $links[$linkkey];
						}
					}
					if ($type!='link') {
						//plain display
						echo $params[$key];
					} else {
						//Specify different values for the displayed data and link if available
						if (!is_array($params[$key])) {
							$datadisplay = $params[$key];
							$datalink = $datadisplay;
						} else {
							$datadisplay = $params[$key]['display'];
							$datalink = $params[$key]['link'];
						}
						$link = $link.$datalink;
						echo "<a target='params' href='".$link."'>".$datadisplay."</a>";
					}
					echo "</td></tr>\n";
				}
			}

		}
		echo "</table>\n";
	}
		
	function getTemplatesFromProject ($projectId) {
		$q="SELECT temp.*, path.path "
			."FROM `ApTemplateImageData` AS temp "
			."LEFT JOIN ApPathData AS path ON "
			."(temp.`REF|ApPathData|path`=path.`DEF_id`) "
			."WHERE `project|projects|project`='$projectId' "
		        ."AND (temp.`hidden` IS NULL OR temp.`hidden` = 0) "
			."ORDER BY temp.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getTemplatesFromId ($templateId) {
		$q = "SELECT t.*, p.path "
				."FROM `ApTemplateImageData` AS t "
				."LEFT JOIN ApPathData AS p ON "
				."(t.`REF|ApPathData|path`=p.`DEF_id`) "
				."WHERE t.`DEF_id` = '$templateId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRecentTemplateRunFromId ($templateId) {
		$q = "SELECT trun.* "
				."FROM `ApTemplateRunData` AS trun "
				."LEFT JOIN ApTemplateImageData AS timg ON "
				."(trun.`REF|ApTemplateImageData|template` = timg.`DEF_id`) "
				."WHERE timg.`DEF_id` = '$templateId' "
				."ORDER BY trun.`DEF_id` DESC "
				."LIMIT 1 ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getParticlesFromImageId ($runId, $imageId){
		$q = "select p.DEF_id as id, "
			."p.xcoord, p.ycoord, p.correlation "
			."from ApParticleData p "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' "
			."and p.`REF|leginondata|AcquisitionImageData|image` = '$imageId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getLastAssessmentRun ($sessionId){
		$q = "select max(DEF_id) as runId "
			." from ApAssessmentRunData where `REF|leginondata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId]; 
	}

	function getAssessmentRunIds ($sessionId) {
		$q = "select * "
			."from ApAssessmentRun where `REF|leginondata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getKeepStatus ($imageId,$runId){
		// returns a boolean value, 0 if rejected, 1 if keeping,
		// null if no status in database
		$q = "select * "
			."from dbappiondata.ApAssessmentData "
			."where `REF|leginondata|AcquisitionImageData|image` = '$imageId' "
			."and `REF|ApAssessmentRunData|assessmentrun` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);
		if ($r) {
			if ($r['selectionkeep']==0) $keep='no';
			elseif ($r['selectionkeep']==1) $keep='yes';
		}
		return $keep;
		//		return $r['selectionkeep'];
	}

	function updateKeepStatus ($imageId,$runId,$value){
		// update image status : 0 if rejected, 1 if keeping,

		$exists=($this->getKeepStatus($imageId,$runId)) ? true : false;
		if ($exists) {
			$data = array('selectionkeep'=>$value);
			$where = array('REF|leginondata|AcquisitionImageData|image'=>$imageId);
			$where['REF|ApAssessmentRunData|assessmentrun']=$runId;
			$this->mysql->SQLUpdate('ApAssessmentData',$data,$where);			 
		}
		else {
			$data['selectionkeep']=$value;
			$data['REF|leginondata|AcquisitionImageData|image']=$imageId;
			$data['REF|ApAssessmentRunData|assessmentrun']=$runId;
			$this->mysql->SQLInsert('ApAssessmentData',$data);
		}
	}

	function getAssessmentDataForRun ($runId){
		$q = "select i.filename, a.selectionkeep as keep "
			."from ApAssessmentData a "
			."left join dbemdata.AcquisitionImageData i "
			."on (a.`REF|leginondata|AcquisitionImageData|image` = i.`DEF_id`) "
			."where a.`REF|ApAssessmentRunData|assessmentrun` = '$runId' ";
		//echo "$q";
		$r=$this->mysql->getSQLResult($q);
		return $r;	
	}

	function getSelectionParams ($runId) {
		$q = "select * from ApSelectionRunData "
			." where `DEF_id` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);
		
		//print_r ($r);
		//echo $r['REF|ApSelectionParamsData|params'];
		$q = "select s.*, r.name, r.`REF|leginondata|SessionData|session` ";

		if ($r['REF|ApSelectionParamsData|params']) {
			$selectionparamid=$r['REF|ApSelectionParamsData|params'];
			$q .= "from ApSelectionParamsData s "
				 ."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApSelectionParamsData|params`) ";
		}
		elseif ($r['REF|ApDogParamsData|dogparams']) {
			$dogparamid=$r['REF|ApDogParamsData|dogparams'];
			$q .= "from ApDogParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApDogParamsData|dogparams`) ";
		}
		elseif ($r['REF|ApManualParamsData|manparams']) {
			$manparamid=$r['REF|ApManualParamsData|manparams'];
			$q .= "from ApManualParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApManualParamsData|manparams`) ";
		}
		elseif ($r['REF|ApTiltAlignParamsData|tiltparams']) {
			$manparamid=$r['REF|ApTiltAlignParamsData|tiltparams'];
			$q .= "from ApTiltAlignParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApTiltAlignParamsData|tiltparams`) ";
		}
		
			$q .= "where r.`DEF_id` = '$runId' ";
		//echo $q;
		$r=$this->mysql->getSQLResult($q);
		//print_r ($r);
		return $r;
	}

	function getMaxTiltAngle ($sessionId) {
		$q = "SELECT MAX(ABS(s.`SUBD|stage position|a`))*180.0/PI() AS angle "
			."FROM dbemdata.`AcquisitionImageData` AS im "
			."LEFT JOIN dbemdata.`ScopeEMData` AS s "
			."ON s.`DEF_id` = im.`REF|ScopeEMData|scope` "
			."WHERE im.`REF|SessionData|session` = '$sessionId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['angle'];
	}

	function getTemplateRunParams ($runId) {
		$q="SELECT i.DEF_id as id, p.path, i.templatename as tname, i.apix, i.description, "
			."t.range_start, t.range_end, t.range_incr, "
			."r.name "
			."from ApTemplateRunData AS t "
			."left join ApTemplateImageData i on (t.`REF|ApTemplateImageData|template`=i.`DEF_id`) "
			."LEFT JOIN ApPathData AS p ON (i.`REF|ApPathData|path`=p.`DEF_id`) "
			."left join ApSelectionRunData r on (t.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			."where t.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
		
	function getParticles ($runId) {
		$q="select p.DEF_id, p.xcoord, p.ycoord, p.correlation "
			."from ApParticleData p "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' "; 
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function hasParticleData ($sessionId) {
		$r= ($this->getLastParticleRun($sessionId)) ? true : false;
		return $r;
	}

	function getStats ($runId, $inspect=False, $selexval=False){
		$q="select count(p.`DEF_id`) as `totparticles`, "
			."count(distinct p.`REF|leginondata|AcquisitionImageData|image`) as num, "
			."min(p.correlation) as `min`, "
			."max(p.correlation) as `max`, "
			."avg(p.correlation) as `avg`, "
			."stddev(p.correlation) as `stddev` "
						."from ApParticleData p ";
		// use the latest inspection value. This should be changed later 
		if ($inspect) {
						$q.= "left join ApAssessmentData ad "
				."on (ad.`REF|leginondata|AcquisitionImageData|image` = p.`REF|leginondata|AcquisitionImageData|image`) ";
		}
		$q.="WHERE ";
		if ($inspect) {
			$q.= "ad.`DEF_id`=(select max(ad2.`DEF_id`) from ApAssessmentData ad2 where ad2.`REF|leginondata|AcquisitionImageData|image` = ad.`REF|leginondata|AcquisitionImageData|image`) "
				."and ad.selectionkeep=1 AND ";
		}
		if ($selexval) $q.="p.`correlation`>='$selexval' AND ";
		$q.="p.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
			
	}

	function getNumImgs ($runId){
		$q="SELECT count(distinct `REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` "
			. "WHERE `REF|ApSelectionRunData|selectionrun`='$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getNumImgsFromSessionId ($sessionId){
		$q="SELECT count(distinct `REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` p "
			. "left join `ApSelectionRunData` r on (p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			. "WHERE r.`REF|leginondata|SessionData|session`='$sessionId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getNumAssessedImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "select count(DEF_id) as num "
			."from `ApAssessmentData` where "
			."`selectionkeep` IS NOT NULL "
			."and `REF|ApAssessmentRunData|assessmentrun` = '$rid'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getLastParticleRun ($sessionId) {
		$q = "select DEF_id as runId "
			."from `ApSelectionRunData` "
			."where `REF|leginondata|SessionData|session` = '$sessionId' "
			."order by DEF_id desc limit 1";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}

	function getParticleRunData ($partRunId) {
		$q = "SELECT r.*, p.path "
			."FROM `ApSelectionRunData` AS r "
			."LEFT JOIN ApPathData AS p ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$partRunId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticleRunIds ($sessionId) {
		$q = "SELECT r.*, p.path "
			."FROM `ApSelectionRunData` AS r "
			."LEFT JOIN ApPathData AS p "
			."ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`REF|leginondata|SessionData|session` = '$sessionId' "
			."ORDER BY r.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	#--------- MAKE STACK FUNCTIONS---------------#

	function getStackIds ($sessionId) {
		// this function is really slow
		$q = "SELECT r.`REF|ApStackData|stack` as stackid "
		."FROM ApRunsInStackData as r "
		."LEFT JOIN ApStackRunData as s ON "
		."(r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
		."WHERE s.`REF|leginondata|SessionData|session` = '$sessionId' "
		."ORDER BY stackid DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackIdsOld ($sessionId) {
		$q = "select spar.stackid "
		."from ("
		."select `REF|ApParticleData|particle` as pid, `REF|ApStackRunData|stackRun` as stackid "
		."from ApStackParticlesData group by `REF|ApStackRunData|stackRun`) spar "
		."left join ApParticleData p on (p.`DEF_id` = spar.pid) "
		."left join ApSelectionRunData r on	(p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id` ) "
		."where r.`REF|leginondata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackParams ($stackId) {
		$q = "SELECT sd.*, pd.`path` "
			."FROM ApStackData as sd "
			."LEFT JOIN ApPathData AS pd ON "
			."(sd.`REF|ApPathData|path` = pd.`DEF_id`) "
			."WHERE sd.`DEF_id` = '$stackId'";
		list($stack_primary_array) = $this->mysql->getSQLResult($q);
		// Get runs in stack
		$q = "SELECT r.`REF|ApStackRunData|stackRun` as runid "
			."FROM ApRunsInStackData as r "
			."WHERE r.`REF|ApStackData|stack` = '$stackId'";
		$stackrunIds = $this->mysql->getSQLResult($q);
		// Parameters of original stack of the runs in stack
		foreach ($stackrunIds as $runid) {
			$stackrunId = $runid[runid];	
			$rstack = $this->getOriginalStackFromStackRun($stackrunId);
			$childstackId = $rstack['stackId'];
			//Get Parameters
			$q = "SELECT sd.`DEF_id` as stackId, s.`DEF_id` as runid, s.*, p.*"
				."FROM ApRunsInStackData as r "
				."LEFT JOIN ApStackRunData as s "
				."ON (r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
				."LEFT JOIN ApStackData as sd "
				."ON (r.`REF|ApStackData|stack`=sd.`DEF_id`) "
				."LEFT JOIN ApPathData AS pd ON "
				."(sd.`REF|ApPathData|path` = pd.`DEF_id`) "
				."LEFT JOIN `ApStackParamsData` p "
				."ON (p.`DEF_id` = s.`REF|ApStackParamsData|stackParams`) "
				."WHERE r.`REF|ApStackData|stack` = '$childstackId'";
			list($r) = $this->mysql->getSQLResult($q);
			$params[]=$r;
		}
		//handle multiple runs in stack
		if (count($stackrunIds) > 1) {
			$patharray = explode('/',$stack_primary_array[path]);
			$runname = $patharray[count($patharray)-1];
		} else {
			$runname=$params[0]['stackRunName'];
		}

		$runarray = array();
		$runarray['shownstackname'] = $runname;
		$runarray['count'] = count($stackrunIds);
		//use first run parameters for basic stack info
		$runarray['boxSize']=$params[0]['boxSize'];
		$runarray['bin']=$params[0]['bin'];
		$runarray = array_merge($runarray,$stack_primary_array);	
		$r = array_merge($params,$runarray);
		return $r;
	}

	function getOriginalStackFromStackRun($stackrunId) {
	//get the original stack when a stackrun is also used in combined stacks
		$q = "SELECT rs.`REF|ApStackData|stack` as stackId from `ApRunsInStackData` rs"
			. " WHERE"
			. " rs.`REF|ApStackRunData|stackRun`=".$stackrunId." "
			. " AND"
			. " rs.`REF|ApStackData|stack` NOT IN"
			. " (SELECT `REF|ApStackData|stack` as stack FROM "
			. " (SELECT count(*) as count ,`REF|ApStackData|stack`"
			. " FROM `ApRunsInStackData`"
			. " WHERE 1"
			. " GROUP BY `REF|ApStackData|stack`) runs"
			. " where runs.`count` > 1)";
		list($rstack) = $this->mysql->getSQLResult($q);
		return $rstack;
	}

	function getStackSelectionRun ($stackId) {
		$q = "SELECT pr . `DEF_id` selectionid , "
		." pr . `name` "
		." FROM ( SELECT * FROM `ApStackParticlesData` "
		." WHERE `REF|ApStackData|stack` = ".$stackId." "
		." group by `REF|ApStackRunData|stackRun` ) sp1 "
		." LEFT JOIN `ApParticleData` p "
		." ON p . `DEF_id` = sp1 . `REF|ApParticleData|particle` "
		." LEFT JOIN `ApSelectionRunData` pr "
		." ON pr . `DEF_id` = p . `REF|ApSelectionRunData|selectionrun` "
		." ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNumStackParticles ($stackId) {
		$q= "SELECT count(DEF_id) as num "
			."FROM `ApStackParticlesData` "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}		

	//////// fix me ////////
	function getStackIdFromReconId ($reconId) {
		$q= "SELECT * "
			."FROM `ApRefinementRunData` "
			."WHERE `DEF_id` = '$reconId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['REF|ApStackData|stack'];
	}		

	function getStackPixelSizeFromStackId ($stackId) {
		//get the first image of the stack assume using defocpair if not specified
		$q="SELECT "
			." IF( ( pimage . `defocpair` IS NULL OR pimage . `defocpair` = 1 ) , "
			." sbimage . image , pimage . image ) as image , "
			." pimage.image as pimage, "
			." pimage.`stackbin` "
			." FROM "
			." ( SELECT "
			." p . `REF|leginondata|AcquisitionImageData|image` as image , pa . `defocpair` ,"
			." pa.`bin` as stackbin "
			." FROM `ApStackParticlesData` sp "
			." LEFT JOIN `ApStackRunData` r ON "
			." ( sp . `REF|ApStackRunData|stackRun` = r . `DEF_id` ) "
			." LEFT JOIN `ApStackParamsData` pa ON "
			." ( pa . `DEF_id` = r . `REF|ApStackParamsData|stackParams` ) "
			." LEFT JOIN `ApParticleData` p ON "
			." sp . `REF|ApParticleData|particle` = p . `DEF_id` "
			." WHERE sp . `REF|ApStackData|stack` = ".$stackId." "
			." limit 1 ) pimage , "
			." ( SELECT "
			." sb . `REF|leginondata|AcquisitionImageData|image2` as image "
			." FROM `ApStackParticlesData` sp "
			." LEFT JOIN `ApStackRunData` r ON "
			." ( sp . `REF|ApStackRunData|stackRun` = r . `DEF_id` ) "
			." LEFT JOIN `ApStackParamsData` pa ON "
			." ( pa . `DEF_id` = r . `REF|ApStackParamsData|stackParams` ) "
			." LEFT JOIN `ApParticleData` p ON "
			." sp . `REF|ApParticleData|particle` = p . `DEF_id` "
			." LEFT JOIN `ApImageTransformationData` sb ON "
			." (sb . `REF|leginondata|AcquisitionImageData|image1` "
			." = p . `REF|leginondata|AcquisitionImageData|image`) "
			." WHERE sp . `REF|ApStackData|stack`= ".$stackId." "
			." limit 1 ) sbimage ";
			list($r1)= $this->mysql->getSQLResult($q);
		//if no sibling image when defocpair param is not specified, use the original image
		$imgId = ($r1['image']) ? $r1['image'] : $r1['pimage'];
		
		// get image bin and the most recent pixel calibration
		$q="SELECT pd.`SUBD|binning|x` as imgbin, "
			."pc.`pixelsize` as ccdpixelsize "
			."FROM dbemdata.`AcquisitionImageData` a "
			."left join dbemdata.`PresetData` pd "
			."on (a.`REF|PresetData|preset`=pd.`DEF_id`) "
			.", dbemdata.PixelSizeCalibrationData pc "
			."WHERE a.`DEF_id`='$imgId' "
			."AND pc.`REF|InstrumentData|tem`= pd.`REF|InstrumentData|tem` "
			."AND pc.`magnification`= pd.`magnification` "
			."AND "
			."pc.`REF|InstrumentData|ccdcamera`= pd.`REF|InstrumentData|ccdcamera` "
			."AND "
			."pc.`DEF_timestamp`<	a.`DEF_timestamp` "
			."ORDER BY pc.`DEF_timestamp` DESC ";

		list($r2)=$this->mysql->getSQLResult($q);
		if (!is_null($r1['stackbin']) ) {
			settype($r1['stackbin'],"integer");
			$stackbin = $r1['stackbin'];
		} else {
			$stackbin = 1;
		}
		$stackpixelsize = $r2['ccdpixelsize']*$r2['imgbin']*$stackbin;
		return $stackpixelsize;
	}

	function displayParticleStats ($particleruns, $display_keys, $inspect=False, $selexval=False) {
		if (!is_array($particleruns))
			return ;
		$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html .= "<tr> <td> </td>";
		foreach($display_keys as $key) {
			$html .= "<td> <span class='datafield0'>".$key."</span> </td> ";
		}
		$html .= "</tr>";

		foreach ($particleruns as $particle) {
			$runId=$particle['DEF_id'];
			$particlestats = $this->getStats($runId, $inspect, $selexval);
			$html .= "<tr>";
			$numptl=$particlestats['totparticles'];
			$numimg=$particlestats['num'];
			$ppimg = ($numimg > 0) ? (sprintf("%.1f", $numptl/$numimg)) : 0;
			$particlestats['numimgs']=$numimg.'<br />('.$ppimg.' prtl/img)';
			$particlestats['img'] = '<a href="'.$this->$baseurl.'particlegraph.php?hg=1&run='.$runId.'">'
				.'<img border="0" '
				.'src="'.$this->$baseurl.'particlegraph.php?w=150&hg=1&run='
				.$runId.'"></a>';
			$q = "select name from `ApSelectionRunData` where `DEF_id` = $runId";
			list($r0) = $this->mysql->getSQLResult($q);
			$html .= '<td><a target="params" href="'.$this->$baseurl.'particlerunreport.php?rId='.$runId.'">'.$r0['name'].'</a></td>';
			foreach($display_keys as $field) {
							$data=$particlestats[$field];
				if (eregi('^min|^max|^avg|^stddev', $field)) $data=format_sci_number($data,4);
				$html .= "<td> $data </td> \n";
			}
			$html .= "</tr>\n";
		}
		$html .= "</table>\n";
		return $html;
	}

	#--------- MAKE MASK FUNCTIONS---------------#

	function getMaskMakerRunIds ($sessionId) {
		$q = "select * "
			."from `ApMaskMakerRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaskAssessRunIds ($sessionId) {
		$q = "select * "
			."from `ApMaskAssessmentRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function hasMaskMakerData ($sessionId) {
		$r= ($this->getLastMaskMakerRun($sessionId)) ? true : false;
		return $r;
	}

	function getLastMaskMakerRun ($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApMaskMakerRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId];
	}

	function getMaskMakerParams ($runId) {
		$q = "select * from ApMaskMakerRunData "
			." where `DEF_id` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);
		
		//print_r ($r);
		//echo $r['REF|ApMaskMakerParamsData|params'];
		$q = "select s.*, r.name, r.`REF|leginondata|SessionData|session` ";

		if ($r['REF|ApMaskMakerParamsData|params']) {
			$maskparamid=$r['REF|ApSelectionParamsData|params'];
			$q .= "from ApMaskMakerParamsData s "
				 ."left join ApMaskMakerRunData r on (s.`DEF_id` = r.`REF|ApMaskMakerParamsData|params`) "
				."LEFT JOIN ApPathData AS p ON "
				."(r.`REF|ApPathData|path`= p.`DEF_id`) ";
		}
		
		$q .= "where r.`DEF_id` = '$runId' ";
		//echo $q;
		$r=$this->mysql->getSQLResult($q);
		//print_r ($r);
		return $r;
	}

	function getMaskRegions ($runId) {
		$q="select r.DEF_id, r.x, r.y, r.area, r.mean, r.stdev "
			."from ApMaskRegionData r "
			."where r.`REF|ApMaskMakerRunData|maskrun` = ".$runId." ";				 $r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaskRegionStats ($runId, $inspect=False){
		$q="select count(r.`DEF_id`) as `totregions`, "
			."count(distinct r.`REF|leginondata|AcquisitionImageData|image`) as num, "
			."avg(r.area) as `areamean`, "
			."avg(r.mean) as `Imean`, "
			."avg(r.stdev) as `Istddev` "
						."from ApMaskRegionData r ";
		// use the latest inspection value. This should be changed later 
		if ($inspect) {
						$q.= "left join ApAssessmentData ad "
				."on (ad.`REF|leginondata|AcquisitionImageData|image` = r.`REF|leginondata|AcquisitionImageData|image`) ";
		}
		$q.="WHERE ";
		if ($inspect) {
			$q.= "ad.`DEF_id`=(select max(ad2.`DEF_id`) from ApAssessmentData ad2 where ad2.`REF|leginondata|AcquisitionImageData|image` = ad.`REF|leginondata|AcquisitionImageData|image`) "
				."and ad.selectionkeep=1 AND ";
		}
		$q.="r.`REF|ApMaskMakerRunData|maskrun` = '$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
			
	}

	function displayMaskRegionStats ($particleruns, $display_keys, $inspect=False, $selexval=False) {
		if (!is_array($particleruns))
			return ;
		$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html .= "<tr> <td> </td>";
		foreach($display_keys as $key) {
			$html .= "<td> <span class='datafield0'>".$key."</span> </td> ";
		}
		$html .= "</tr>";

		foreach ($particleruns as $particle) {
			$runId=$particle['DEF_id'];
			$regionstats = $this->getMaskRegionStats($runId, $inspect);
			$html .= "<tr>";
			$numregn=$regionstats['totregions'];
			$numimg=$regionstats['num'];
			$rpimg = ($numimg > 0) ? (sprintf("%.1f", $numregn/$numimg)) : 0;
			$regionstats['numimgs']=$numimg.'<BR>('.$rpimg.' regions/img)';
			$regionstats['img'] = '<a href="maskregiongraph.php?hg=1&run='.$runId.'">'
							.'<img border="0" '
							.'src="maskregiongraph.php?w=150&hg=1&run='
				.$runId.'"></a>';
			$q = "select name from `ApMaskMakerRunData` where `DEF_id` = $runId";
			$r = $this->mysql->getSQLResult($q);
			$r0 = $r[0];
			$html .= '<td><a target="params" href="maskrunreport.php?rId='.$runId.'">'.$r0[name].'</a></td>';
			foreach($display_keys as $field) {
							$data=$regionstats[$field];
				if (eregi('^areamean|^Imean|^Istddev', $field)) $data=format_sci_number($data,4);
				$html .= "<td> $data </td> \n";
			}
			$html .= "</tr>\n";
		}
		$html .= "</table>\n";
		return $html;
	}

	function getMaskAssessRunByName ($sessionId,$name){
		$q = "select * "
			."from `ApMaskAssessmentRunData` "
			."where "
			."`REF|leginondata|SessionData|session` = '$sessionId' AND "
			." `name` = '$name' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaskAssessNames ($sessionId){
		$q = "select `name` "
			."from `ApMaskAssessmentRunData` "
			."where `REF|leginondata|SessionData|session` = '$sessionId' "	
			." group by `name` ";
		$r = $this->mysql->getSQLResult($q);
		if ($r) {
			$names=array();
			foreach ($r as $ra) $names[]=$ra[name];
		}
		return $names;
	}

	function getMaskAssessStats ($runId, $inspect=False){
		$q="select count(m.`keep`) as `totkeeps`, "
			."count(distinct r.`REF|leginondata|AcquisitionImageData|image`) as num "
						."from ApMaskAssessmentData m "
			."left join ApMaskRegionData r "
			." on m.`REF|ApMaskRegionData|region` = r.`DEF_id` ";
		// use the latest inspection value. This should be changed later 
		if ($inspect) {
						$q.= "left join ApAssessmentData ad "
				."on (ad.`REF|leginondata|AcquisitionImageData|image` = r.`REF|leginondata|AcquisitionImageData|image`) ";
		}
		$q.="WHERE ";
		if ($inspect) {
			$q.= "ad.`DEF_id`=(select max(ad2.`DEF_id`) from ApAssessmentData ad2 where ad2.`REF|leginondata|AcquisitionImageData|image` = ad.`REF|leginondata|AcquisitionImageData|image`) "
				."and ad.selectionkeep=1 AND ";
		}
		$q.="m.`REF|ApMaskAssessmentRunData|run` = '$runId' AND "
			."m.`keep` = 1 ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
			
	}

	#--------- REF-FREE ALIGNMENT FUNCTIONS---------------#

	function getNoRefIds ($sessionId) {
		$q = "SELECT nr.`DEF_id` "
			."FROM ApNoRefRunData AS nr "
			."LEFT JOIN ApRunsInStackData AS sd ON "
			."(nr.`REF|ApStackData|stack` = sd.`REF|ApStackData|stack`) "
			."LEFT JOIN ApStackRunData AS sr ON "
			."(sd.`REF|ApStackRunData|stackRun` = sr.`DEF_id`) "
			."WHERE sr.`REF|leginondata|SessionData|session` = '$sessionId' "
			."ORDER BY nr.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

		function getRefAliIds ($sessionId) {
		$q = "SELECT rr.`DEF_id` "
			."FROM ApRefRunData AS rr "
			."LEFT JOIN ApRunsInStackData AS sd ON "
			."(rr.`REF|ApStackData|stack` = sd.`REF|ApStackData|stack`) "
			."LEFT JOIN ApStackRunData AS sr ON "
			."(sd.`REF|ApStackRunData|stackRun` = sr.`DEF_id`) "
			."WHERE sr.`REF|leginondata|SessionData|session` = '$sessionId' "
			."ORDER BY rr.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getRefInfoFromId ($refid) {
		$q = "SELECT * "
			."FROM ApRefRunData "
			."WHERE ApRefRunData.`DEF_id`='$refid'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRefTemplatesFromId ($refid) {
		$q = "SELECT t.*, pd.`path` "
			."FROM ApRefTemplateRunData AS rt "
			."LEFT JOIN ApTemplateImageData AS t ON "
			."(rt.`REF|ApTemplateImageData|refTemplate` = t.`DEF_id`) "
			."LEFT JOIN ApPathData AS pd ON "
			."(t.`REF|ApPathData|path` = pd.`DEF_id`) "
			."WHERE rt.`REF|ApRefRunData|refRun`='$refid'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNoRefParams ($norefId) {
		$q = "SELECT p.*, r.*, pd.path "
			."FROM ApNoRefRunData as r "
			."LEFT JOIN ApNoRefParamsData as p "
			."ON (r.`REF|ApNoRefParamsData|norefParams`=p.`DEF_id`) "
			."LEFT JOIN ApPathData AS pd ON "
			."(r.`REF|ApPathData|path` = pd.`DEF_id`) "
			//."LEFT JOIN ApStackData as sd "
			//."ON (r.`REF|ApStackData|stack`=sd.`DEF_id`) "
			//."LEFT JOIN `ApStackParamsData` sp "
			//."ON (sp.`DEF_id` = s.`REF|ApStackParamsData|stackParams`) "
			."WHERE r.`DEF_id` = '$norefId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRefAliParams ($refaliId) {
		$q = "SELECT	par.*, run.*, path.path "
			."FROM ApRefRunData as run "
			."LEFT JOIN ApRefParamsData as par "
			."ON (run.`REF|ApRefParamsData|refParams`=par.`DEF_id`) "
			."LEFT JOIN ApPathData AS path ON "
			."(run.`REF|ApPathData|path` = path.`DEF_id`) "
			."WHERE run.`DEF_id` = '$refaliId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getNoRefClassRuns ($norefId) {
	$q = "SELECT * "
		."FROM ApNoRefClassRunData as cr "
		."WHERE cr.`REF|ApNoRefRunData|norefRun` = '$norefId' "
		."ORDER BY cr.`num_classes`";
	$r = $this->mysql->getSQLResult($q);
	return $r;
	}

	function getRefAliIters ($refaliId) {
	$q = "SELECT * "
		."FROM ApRefIterationData as i "
		."WHERE i.`REF|ApRefRunData|refRun` = '$refaliId' "
		."ORDER BY i.`iteration`";
	$r = $this->mysql->getSQLResult($q);
	return $r;
	}

	#---------RECONSTRUCTION FUNCTIONS---------------#

	function getSymmetries() {
		$q="SELECT * "
			."FROM `ApSymmetryData`";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
	function getModelsFromProject ($projectId) {
		$q="SELECT i.*, p.path "
			."FROM `ApInitialModelData` i "
			."LEFT JOIN `ApPathData` p "
			." ON (p.`DEF_id` = i.`REF|ApPathData|path`) "
			."WHERE i.`project|projects|project`='$projectId' "
			." AND (i.`hidden` IS NULL OR i.`hidden` = 0) "
			."ORDER BY i.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getMiscInfoFromProject ($projectId) {
		$q="SELECT i.*, p.path "
			."FROM `ApMiscData` i "
			."LEFT JOIN `ApPathData` p "
			." ON (p.`DEF_id` = i.`REF|ApPathData|path`) "
			."WHERE i.`project|projects|project`='$projectId' "
			."ORDER BY i.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getJobIdsFromSession($expId) {
		$q="SELECT `DEF_id` "
		  ."FROM `ApClusterJobData` "
		  ."WHERE `REF|leginondata|SessionData|session` = $expId";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

  function getJobInfoFromId($jobid) {
    $q="SELECT j.*, "
      ."p.path as appath, "
      ."d.path as dmfpath, "
      ."c.path as clusterpath "
      ."FROM `ApClusterJobData` AS j "
      ."LEFT JOIN ApPathData AS p ON "
      ."(j.`REF|ApPathData|path` = p.`DEF_id`) "
      ."LEFT JOIN ApPathData AS d ON "
      ."(j.`REF|ApPathData|dmfpath` = d.`DEF_id`) "
      ."LEFT JOIN ApPathData AS c ON "
      ."(j.`REF|ApPathData|clusterpath` = c.`DEF_id`) "
      ."WHERE j.`DEF_id` = $jobid";
    $r = $this->mysql->getSQLResult($q);
    return $r[0];
  }

  function getJobFileFromPath($path,$name) {
    $q="SELECT j.*, p.path "
      ."FROM `ApClusterJobData` AS j "
      ."LEFT JOIN ApPathData AS p ON "
      ."(j.`REF|ApPathData|path` = p.`DEF_id`) "
      ."WHERE p.`path` = '$path' AND j.`name` = '$name'";
    $r = $this->mysql->getSQLResult($q);
    return $r;
  }

  function insertClusterJobData($pathdir,$dmfpathdir,$clusterdir,$name,$expId) {
    // put appion path in db
    $q = "SELECT DEF_id "
      ."FROM `ApPathData` "
      ."WHERE `path`='$pathdir'";
    $r = $this->mysql->getSQLResult($q);
    $pathid=$r[0]['DEF_id'];
    if (!$pathid) {
      $pdata['path']=$pathdir;
      $pathid=$this->mysql->SQLInsert('ApPathData',$pdata);
    }
    // put dmf path in db
    $q = "SELECT DEF_id "
      ."FROM `ApPathData` "
      ."WHERE `path`='$dmfpathdir'";
    $r = $this->mysql->getSQLResult($q);
    $dmfpathid=$r[0]['DEF_id'];
    if (!$dmfpathid) {
      $pdata['path']=$dmfpathdir;
      $dmfpathid=$this->mysql->SQLInsert('ApPathData',$pdata);
    }
    // put cluster path in db
    $q = "SELECT DEF_id "
      ."FROM `ApPathData` "
      ."WHERE `path`='$clusterdir'";
    $r = $this->mysql->getSQLResult($q);
    $clusterpathid=$r[0]['DEF_id'];
    if (!$clusterpathid) {
      $pdata['path']=$clusterdir;
      $clusterpathid=$this->mysql->SQLInsert('ApPathData',$pdata);
    }
    // find if job is in database
    $q = "SELECT DEF_id "
      ."FROM `ApClusterJobData` "
      ."WHERE `REF|ApPathData|path` = $pathid AND "
      ."`name` = '$name' AND "
      ."`REF|leginondata|SessionData|session` = $expId";
    $r = $this->mysql->getSQLResult($q);
    $jid=$r[0]['DEF_id'];
    // if not in database, insert
    if (!$jid) {
      $jdata['REF|ApPathData|path'] = $pathid;
      $jdata['name'] = $name;
      $jdata['REF|leginondata|SessionData|session'] = $expId;
      $jdata['REF|ApPathData|dmfpath'] = $dmfpathid;
      $jdata['REF|ApPathData|clusterpath'] = $clusterpathid;
      $jid=$this->mysql->SQLInsert('ApClusterJobData',$jdata);
    }
    return $jid;
  }

  function updateClusterQueue($jobid,$queueid) {
    $data = array('clusterjobid'=>$queueid);
    $data['status']='Q';
    $where = array('DEF_id'=>$jobid);
    $this->mysql->SQLUpdate('ApClusterJobData',$data,$where);			 
  }

  function getSubmittedJobs($expId) {
    $q="SELECT * "
      ."FROM `ApClusterJobData` "
      ."WHERE `REF|leginondata|SessionData|session`=$expId";
    $r = $this->mysql->getSQLResult($q);
    return $r;
  }

	function getReconIdFromClusterJobId ($jobid) {
		$q="SELECT * "
		  ."FROM `ApRefinementRunData` "
		  ."WHERE `REF|ApClusterJobData|jobfile` = $jobid";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getReconIdsFromSession ($sessionId) {
		$q = "SELECT refrun.*  "
			." FROM `ApRefinementRunData` AS refrun "
			."LEFT JOIN ApRunsInStackData AS runs "
			." ON refrun.`REF|ApStackData|stack` = runs.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			." ON runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id` "
			."WHERE stackrun.`REF|leginondata|SessionData|session` = '$sessionId' "
			." ORDER BY refrun.`DEF_id` DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	} 

	function getReconIds ($stackId) {
		$q = "SELECT * "
			."FROM `ApRefinementRunData` AS r "
			."WHERE r.`REF|ApStackData|stack` = '$stackId'"
			."ORDER BY r.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	} 

	function getRefinementRunInfo($refinementRun) {
		$q="select r.*, p.path "
			."FROM `ApRefinementRunData` AS r "
			."LEFT JOIN ApPathData AS p ON "
			."(r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$refinementRun' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getInitModelInfo ($modelId) {
		$q = "SELECT d.*,p.path "
				."FROM `ApInitialModelData` AS d "
				."LEFT JOIN ApPathData AS p ON "
				."(d.`REF|ApPathData|path` = p.`DEF_id`) "
				."WHERE d.`DEF_id` = '$modelId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getSymInfo ($symId){
		$q = "SELECT * "
				."FROM `ApSymmetryData` WHERE `DEF_id` = '$symId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getResolutionInfo ($resId) {
		$q = "SELECT * "
				."FROM `ApResolutionData` WHERE `DEF_id` = '$resId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getRMeasureInfo ($resId) {
		$q = "SELECT * "
				."FROM `ApRMeasureData` WHERE `DEF_id` = '$resId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getHighestResForRecon ($reconid) {
		$q = "SELECT ref.iteration AS iter, res.half AS half, rmeas.rMeasure AS rmeas " 
				."FROM `ApRefinementData` AS ref "
				."LEFT JOIN `ApResolutionData` AS res "
				." ON (ref.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
				."LEFT JOIN `ApRMeasureData` AS rmeas "
				." ON (ref.`REF|ApRMeasureData|rMeasure` = rmeas.`DEF_id`) "
				."WHERE ref.`REF|ApRefinementRunData|refinementRun` = '$reconid' "
				//."ORDER by rmeas.rMeasure ";
				."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getHighestRMeasureForRecon ($reconid) {
		$q = "SELECT ref.iteration AS iter, res.half AS half, rmeas.rMeasure AS rmeas " 
				."FROM `ApRefinementData` AS ref "
				."LEFT JOIN `ApResolutionData` AS res "
				." ON (ref.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
				."LEFT JOIN `ApRMeasureData` AS rmeas "
				." ON (ref.`REF|ApRMeasureData|rMeasure` = rmeas.`DEF_id`) "
				."WHERE ref.`REF|ApRefinementRunData|refinementRun` = '$reconid' "
				."ORDER by rmeas.rMeasure ";
				//."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getIterationInfo ($reconId) {
		$q = "SELECT * "
				."FROM `ApRefinementData` r "
				."LEFT JOIN `ApRefinementParamsData` p "
				."ON (r.`REF|ApRefinementParamsData|refinementParams` = p.`DEF_id`) "
				."WHERE r.`REF|ApRefinementRunData|refinementRun` = '$reconId' "
				."ORDER BY r.`iteration` ASC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getRefinementData ($refinementRun,$iteration) {
		$q = "SELECT * "
				."FROM `ApRefinementData` "
				."WHERE `REF|ApRefinementRunData|refinementRun` = $refinementRun "
				."AND `iteration` = $iteration";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getParamsFromRefinementDataId ($refinementId) {
		$q = "SELECT * "
				."FROM `ApRefinementData` r "
				."LEFT JOIN `ApRefinementParamsData` p "
				."ON (r.`REF|ApRefinementParamsData|refinementParams` = p.`DEF_id`) "
				."WHERE r.`DEF_id` = $refinementId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getStackFromRefinement ($refinementDataId) {
		$q = "SELECT r.*, rr.*, s.*, path.path "
				."FROM `ApRefinementData` r "
				."LEFT JOIN `ApRefinementRunData` rr "
				."ON (r.`REF|ApRefinementRunData|refinementRun` = rr.`DEF_id`) "
				."LEFT JOIN `ApStackData` s "
				."ON (rr.`REF|ApStackData|stack` = s.`DEF_id`) "
				."LEFT JOIN `ApPathData` path "
				."ON (s.`REF|ApPathData|path` = path.`DEF_id`) "
				."WHERE r.`DEF_id` = $refinementDataId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSubsetParticlesInStack ($refinementDataId, $subset) {
		$q = "SELECT particleNumber as p "
		  ."FROM `ApParticleClassificationData` apcd "
		  ."LEFT JOIN `ApStackParticlesData` aspd "
		  ."ON (apcd.`REF|ApStackParticlesData|particle` = aspd.`DEF_id`) "
		  ."WHERE apcd.`REF|ApRefinementData|refinement` = '$refinementDataId' ";
		if ($subset=='bad') $q.="AND `thrown_out` = 1 ";
		elseif ($subset=='good') $q.="AND `thrown_out` is NULL ";
		$q.= "ORDER BY aspd.`DEF_id` ASC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNumBadParticles ($refinementDataId) {
		$q="SELECT count(DEF_id) "
			."FROM `ApParticleClassificationData` "
			."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' "
			."AND `thrown_out` = 1";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['count(DEF_id)'];
	}

  function listAllStackParticles ($stackId) {
    $q="SELECT sp.`particleNumber`, db.`MRC|image`, "
      ."p.`xcoord` , p.`ycoord` "
      ."FROM  `ApStackParticlesData` sp "
      ."LEFT JOIN ApParticleData p ON "
      ."( sp.`REF|ApParticleData|particle` = p.`DEF_id` ) " 
      ."LEFT JOIN dbemdata.AcquisitionImageData db ON "
      ."( p.`REF|leginondata|AcquisitionImageData|image` = db.`DEF_id` ) " 
      ."WHERE sp.`REF|ApStackData|stack`=$stackId";
    $r = $this->mysql->getSQLResult($q);
    return $r;
  }

	function getMsgPRejectParticlesInStack ($refinementDataId) {
		$q = "SELECT particleNumber as p "
				."FROM `ApParticleClassificationData` apcd "
				."LEFT JOIN `ApStackParticlesData` aspd "
				."ON (apcd.`REF|ApStackParticlesData|particle` = aspd.`DEF_id`) "
				."WHERE apcd.`REF|ApRefinementData|refinement` = '$refinementDataId' "
				."AND `msgp_keep` = 0";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNumMsgPRejectParticles ($refinementDataId) {
		$q = "SELECT count(DEF_id) as num "
				."FROM `ApParticleClassificationData` "
				."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' "
				."AND `msgp_keep` = 0";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumClasses ($refinementDataId) {
		$q = "SELECT count(distinct(`REF|ApEulerData|eulers`)) as num "
				."FROM `ApParticleClassificationData` "
				."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getEulerIds ($refinementDataId) {
		$q = "SELECT distinct(`REF|ApEulerData|eulers`) as eulers "
				."FROM `ApParticleClassificationData` "
				."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticleEuler ($refinementDataId) {
		$q = "SELECT distinct(`REF|ApEulerData|eulers`) as eulers "
			."FROM `ApParticleClassificationData` "
			."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNumInClass ($refinementDataId,$eulerId) {
		$q = "SELECT count(DEF_id) as num "
			."FROM `ApParticleClassificationData` "
			."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' "
			."AND `REF|ApEulerData|eulers` = $eulerId";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getEulerAngles ($eulerId) {
		$q = "SELECT * "
			."FROM `ApEulerData` "
			."WHERE `DEF_id` = $eulerId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getCommonParticles ($refine1, $refine2) {
		# compare 2 iterations, get all the particles that were used in both
		# reconstructions (ignore those that were thrown out) and return the eulers"
		$q = "SELECT cls1.`REF|ApStackParticlesData|particle` as prtl, "
				."spd.particleNumber, "
				."euler1.euler1 as euler1_1, "
				."euler1.euler2 as euler1_2, "
				."euler1.euler3 as euler1_3, "
				."euler2.euler1 as euler2_1, "
				."euler2.euler2 as euler2_2, "
				."euler2.euler3 as euler2_3, "
				."cls1.`shiftx` as shiftx1, "
				."cls2.`shiftx` as shiftx2, "
				."cls1.`shifty` as shifty1, "
				."cls2.`shifty` as shifty2, "
				."cls1.`inplane_rotation` as rot1, "
				."cls2.`inplane_rotation` as rot2, "
				."cls1.`quality_factor` as qf1, "
				."cls2.`quality_factor` as qf2 "
				."FROM (`ApParticleClassificationData` as cls1) "
				."LEFT JOIN ( "
				." `ApParticleClassificationData` as cls2, "
				." `ApStackParticlesData` as spd, "
				." `ApEulerData` euler1, `ApEulerData` euler2) "
				."ON ( "
				."cls1.`REF|ApStackParticlesData|particle`=cls2.`REF|ApStackParticlesData|particle` "
				."AND spd.DEF_id=cls1.`REF|ApStackParticlesData|particle` "
				."AND cls1.`thrown_out` is NULL AND cls2.`thrown_out` is NULL "
				."AND euler1.DEF_id=cls1.`REF|ApEulerData|eulers` "
				."AND euler2.DEF_id=cls2.`REF|ApEulerData|eulers` "
				.") "
				."WHERE (cls1.`REF|ApRefinementData|refinement`=$refine1 "
				."AND cls2.`REF|ApRefinementData|refinement`=$refine2 "
				.") "
				."ORDER by prtl";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticlesFromRefinementId($refine1) {
		# compare 2 iterations, get all the particles that were used in both
		# reconstructions (ignore those that were thrown out) and return the eulers"
		$q = "SELECT cls1.`REF|ApStackParticlesData|particle` as prtl, "
				."spd.particleNumber, "
				."euler1.euler1 as euler1_1, "
				."euler1.euler2 as euler1_2, "
				."euler1.euler3 as euler1_3, "
				."cls1.`shiftx` as shiftx1, "
				."cls1.`shifty` as shifty1, "
				."cls1.`inplane_rotation` as rot1, "
				."cls1.`quality_factor` as qf1 "
				."FROM (`ApParticleClassificationData` as cls1) "
				."LEFT JOIN ( "
				." `ApStackParticlesData` as spd, "
				." `ApEulerData` euler1) "
				."ON ( "
				."spd.DEF_id=cls1.`REF|ApStackParticlesData|particle` "
				."AND cls1.`thrown_out` is NULL "
				."AND euler1.DEF_id=cls1.`REF|ApEulerData|eulers` "
				.") "
				."WHERE ( "
				." cls1.`REF|ApRefinementData|refinement`=$refine1 "
				.") "
				."ORDER by prtl";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackParticleNum ($particleId) {
					$q = "SELECT particleNumber "
					."FROM `ApStackParticlesData` "
					."WHERE `DEF_id` = $particleId";
					list($r) = $this->mysql->getSQLResult($q);
					return $r['particleNumber'];
		}

	function getMiscInfoFromReconId ($reconid) {
		$q = "SELECT m.*, p.path "
		."FROM `ApMiscData` AS m "
		."LEFT JOIN ApPathData AS p ON "
		."(m.`REF|ApPathData|path` = p.`DEF_id`) "
		."WHERE m.`REF|ApRefinementRunData|refinementRun` = $reconid";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}		

	function getEulerStats($reconId, $iterId1, $iterId2) {
		$q = "SELECT difference, eulers,	mean from `ApProcEulerData` "
				." WHERE `reconId`=$reconId AND `iter1`=$iterId1 AND `iter2`=$iterId2";
		$r=$this->mysql->getSQLResult($q);

		return $r;
	}

	function getReconInfoFromRefinementId($refineid) {
		$q="SELECT *"
		."FROM "
		."`ApRefinementData` AS `ApRefinementData` "
		."LEFT JOIN `ApRefinementRunData` AS `ApRefinementRunData` "
		."ON (`ApRefinementRunData`.`DEF_id`=`ApRefinementData`.`REF|ApRefinementRunData|refinementRun`) "
		."LEFT JOIN `ApPathData` AS `ApPathData` "
		."ON (`ApPathData`.`DEF_id`=`ApRefinementRunData`.`REF|ApPathData|path`) "
		."WHERE `ApRefinementData`.`DEF_id`=$refineid ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}
	
	function insertEulerStats($stats) {
		$mean = $stats->myMean;
		$errors = $stats->myData;
		$reconId=$stats->myReconId;
		$iterId1=$stats->myIterId1;
		$iterId2=$stats->myIterId2;
		$eulers=$stats->eulers1;
		$min = $stats->myMin;
		$max = $stats->myMax;
		$stdev = $stats->myStandardDeviation;


		$euler = array_map('simplify',$eulers);

		$table="ApProcEulerData";
		# $this->mysql->SQLInsert($table, $data);
		$q = "SELECT DEF_id from `ApProcEulerData` "
				." WHERE `reconId`=$reconId AND `iter1`=$iterId1 AND `iter2`=$iterId2";
			 //--- print_r($r=$this->mysql->SQLQuery($q));
			 //--- if (!$r=$this->mysql->getSQLResult($q)) {
					$q = "INSERT INTO `ApProcEulerData` "
							."(`reconId`, `iter1`, `iter2`, `difference`, `eulers`, `mean`, `min`, `max`, `stdev`) "
							." VALUES "
							."($reconId, $iterId1, $iterId2, "
							."'".implode(",",$errors)."',"
							."'".implode(",",$euler)."',"
							."$mean, $min, $max, $stdev)";
					$r=$this->mysql->SQLQuery($q);
					if ($e=$this->mysql->getError()) {
							echo "error -> $e \n";
							exit;
					}
			//--- }
		return $r;
		
	}
}

function simplify($e) {
	return $e['a'].','.$e['b'].','.$e['c'];
}
?>
