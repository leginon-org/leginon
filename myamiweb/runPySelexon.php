<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
  
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runSelexon();
}

// CREATE FORM PAGE
elseif ($_POST['templates']) {
	createSelexonForm();
}

// MAKE THE TEMPLATE SELECTION FORM
else {
	createTemplateForm();
}

function createTemplateForm() {
	// check if coming directly from a session
	$expId = $_GET[expId];
	$formAction=$_SERVER['PHP_SELF'];	

	// retrieve template info from database for this project
	if ($expId){
	$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}

	// if user wants to use templates from another project
	if($_POST['projectId']) $projectId =$_POST[projectId];

	$projects=getProjectList();

	if (is_numeric($projectId)) {
	        $particle=new particleData;
		$templateData=$particle->getTemplatesFromProject($projectId);
	}

	// extract template info
	if ($templateData) {
	        $i=1;
		$javafunctions="<SCRIPT LANGUAGE='JavaScript'>\n";
		$templatetable="<TABLE BORDER='1' CELLPADDING='5' WIDTH='600'>\n";
		$numtemplates=count($templateData);
		foreach($templateData as $templateinfo) { 
		        if (is_array($templateinfo)) {
			        $filename=$templateinfo[templatepath];
				$checkboxname='template'.$i;
				// create the javascript functions to enable the templates
				$javafunctions.="function enable".$checkboxname."() {
                                                 if (document.viewerform.$checkboxname.checked){
                                                 document.viewerform.".$checkboxname."strt.disabled=false;
                                                 document.viewerform.".$checkboxname."strt.value='';
                                                 document.viewerform.".$checkboxname."end.disabled=false;
                                                 document.viewerform.".$checkboxname."end.value='';
                                                 document.viewerform.".$checkboxname."incr.disabled=false;
                                                 document.viewerform.".$checkboxname."incr.value='';
                                         }
                                         else {
                                                 document.viewerform.".$checkboxname."strt.disabled=true;
                                                 document.viewerform.".$checkboxname."strt.value='0';
                                                 document.viewerform.".$checkboxname."end.disabled=true;
                                                 document.viewerform.".$checkboxname."end.value='90';
                                                 document.viewerform.".$checkboxname."incr.disabled=true;
                                                 document.viewerform.".$checkboxname."incr.value='10';
                                         }
                                 }\n";

				// create the image template table
				$templatetable.="<TR><TD>
	                                         <IMG SRC='loadmrc.php?filename=$filename&rescale=True' WIDTH='200'></TD>
	                                         <TD>
                                                 <INPUT TYPE='hidden' NAME='templateId".$i."' VALUE='".$templateinfo[DEF_id]."'>
	                                         <INPUT TYPE='checkbox' NAME='$checkboxname' onclick='enable".$checkboxname."()'>
	                                         <B>Use This Template</B><BR>
                                                 Enter rotation values (leave blank for no rotation):<BR>
                                                 <INPUT TYPE='text' NAME='".$checkboxname."strt' DISABLED VALUE='0' SIZE='3'> Starting Angle<BR>
	                                         <INPUT TYPE='text' NAME='".$checkboxname."end' DISABLED VALUE='90' SIZE='3'> Ending Angle<BR>
	                                         <INPUT TYPE='text' NAME='".$checkboxname."incr' DISABLED VALUE='10' SIZE='3'> Angular Increment<BR>
	                                         <P>
                                                 Template ID: $templateinfo[DEF_id]<BR>
	                                         $templateinfo[description]
	                                         <P>
	                                         pixel size:$templateinfo[apix]</TD></TR>\n";	
	                        $i++;
	                }
                }
		$javafunctions.="</SCRIPT>\n";
		$templatetable.="</TABLE>\n";
	}
	$javafunctions.="<script src='js/viewer.js'></script>\n";

	writeTop("PySelexon Launcher","Automated Particle Selection with PySelexon",$javafunctions);
	echo"
  <FORM NAME='viewerform' method='POST' ACTION='$formAction'>
  <B>Select Project:</B><BR>
  <SELECT NAME='projectId' onchange='newexp()'>\n";

	foreach ($projects as $k=>$project) {
                $sel = ($project['id']==$projectId) ? "selected" : '';
		echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
	}
	echo"
  </select>
  <P>\n";
	if ($templatetable) {
	        echo"
    $templatetable
    <CENTER>
    <INPUT TYPE='hidden' NAME='numtemplates' value='$numtemplates'>
    <INPUT TYPE='submit' NAME='templates' value='Use These Templates'>
    </CENTER>\n";
	}
	else echo "<B>Project does not contain any templates.</B>\n";
	echo"</FORM>\n";
}

function createSelexonForm($extra=false, $title='PySelexon Launcher', $heading='Automated Particle Selection with PySelexon') {
  // check if coming directly from a session
  $expId = $_GET['expId'];
  if ($expId) {
    $sessionId=$expId;
    $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  }
  else {
    $sessionId=$_POST['sessionId'];
    $formAction=$_SERVER['PHP_SELF'];	
  }
  $projectId=$_POST['projectId'];

  // --- find hosts to run SELEXON
  $hosts=getHosts();
  $users[]="glander";
 
  $numtemplates=$_POST[numtemplates];
  $templateForm='';
  $templateTable="<TABLE CLASS='tableborder'><TR><TD>\n";
  $templateCheck='';

  $particle=new particleData;

  for ($i=1; $i<=$numtemplates; $i++) {
    $templateimg="template".$i;
    if ($_POST[$templateimg]){
      $templateIdName="templateId".$i;
      $tmpltstrt=$templateimg."strt";
      $tmpltend=$templateimg."end";
      $tmpltincr=$templateimg."incr";
      $templateId=$_POST[$templateIdName];
      $start=$_POST[$tmpltstrt];
      $end=$_POST[$tmpltend];
      $incr=$_POST[$tmpltincr];

      $templateList.=$i.":".$templateId.",";
      $templateInfo=$particle->getTemplatesFromId($templateId);
      $tmpltrows=$templateInfo[0];
      $filename=$tmpltrows[templatepath];
      $templateTable.="<TD VALIGN='TOP'><IMG SRC='loadmrc.php?filename=$filename&rescale=True' WIDTH='200'><BR>\n";
      if (!$start && !$end && !$incr) $templateTable.="<B>no rotation</B>\n";
      elseif ($start=='' || !$end || !$incr) {
	echo "<B>Error in template $i</B><BR> missing rotation parameter - fix this<BR>\n";
	echo "starting angle: $start<BR>ending angle: $end<BR>increment: $incr<BR>\n";
	exit;
      }
      else {
	$templateTable.="<B>starting angle:</B> $start<BR>\n";
	$templateTable.="<B>ending angle:</B> $end<BR>\n";
	$templateTable.="<B>angular incr:</B> $incr</TD>\n";
      }
      $templateForm.="<INPUT TYPE='hidden' NAME='$templateIdName' VALUE='$templateId'>\n";
      $templateForm.="<INPUT TYPE='hidden' NAME='$templateimg' VALUE='$templateId'>\n";
      $templateForm.="<INPUT TYPE='hidden' NAME='$tmpltstrt' VALUE='$start'>\n";
      $templateForm.="<INPUT TYPE='hidden' NAME='$tmpltend' VALUE='$end'>\n";
      $templateForm.="<INPUT TYPE='hidden' NAME='$tmpltincr' VALUE='$incr'>\n";
    }
  }
  $templateTable.="</TD></TR></TABLE>\n";

  // check that there are templates, remove last comma
  if ($templateList) { $templateList=substr($templateList,0,-1);}
  else {
    echo "<B>no templates chosen, go back and choose templates</B>\n";
    exit;
  }
  $javascript="
  <script src='js/viewer.js'></script>
  <script LANGUAGE='JavaScript'>
     function enabledtest(){
       if (document.viewerform.testimage.checked){
         document.viewerform.testfilename.disabled=false;
         document.viewerform.testfilename.value='';
       }	
       else {
         document.viewerform.testfilename.disabled=true;
         document.viewerform.testfilename.value='mrc file name';
       }
     }
     function enable(thresh){
       if (thresh=='auto') {
         document.viewerform.autopik.disabled=false;
         document.viewerform.autopik.value='';
         document.viewerform.thresh.disabled=true;
         document.viewerform.thresh.value='0.4';
       }
       if (thresh=='manual') {
         document.viewerform.thresh.disabled=false;
         document.viewerform.thresh.value='';
         document.viewerform.autopik.disabled=true;
         document.viewerform.autopik.value='100';
       }
     }
     function infopopup(infoname){
       var newwindow=window.open('','name','height=150,width=300');
       newwindow.document.write('<HTML><BODY>');
       if (infoname=='runid'){
         newwindow.document.write('Specifies the name associated with the ACE results unique to the specified session and parameters.  An attempt to use the same run name for a session using different ACE parameters will result in an error.');
       }
       newwindow.document.write('</BODY></HTML>');
       newwindow.document.close();
     }
  </SCRIPT>\n";

  writeTop($title,$heading,$javascript);
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  echo"
  <form name='viewerform' method='POST' ACTION='$formAction'>\n";
  // Collect session info from database
  $sessiondata=getSessionList($projectId,$sessionId);
  $sessioninfo=$sessiondata['info'];
  $presets=$sessiondata['presets'];
  $sessions=$sessiondata['sessions'];
  $currentproject=$sessiondata['currentproject'];
  if (!empty($sessioninfo)) {
    $sessionpath=$sessioninfo['Image path'];
    $sessionpath=ereg_replace("rawdata","extract/",$sessionpath);
    $sessionname=$sessioninfo['Name'];
  }

  if ($expId){
    $proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
    $sessionDescr=$sessioninfo['Purpose'];
    echo "Project: $proj_link<BR>\nSession: $sessionDescr\n";
  }
  else {
    echo"
    <B>Select Session:</B><BR>
    <SELECT NAME='projectId' onchange='newexp()'>\n";
    $projects=getProjectList();
    foreach ($projects as $k=>$project) {
      $sel = ($project['id']==$projectId) ? "selected" : '';
      echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
    }
 
    echo"
    </select>
    <BR>
 
    <SELECT NAME='sessionId' onchange='newexp()'>
    <option value=''>all sessions</OPTION>\n";
    foreach ($sessions as $k=>$session) {
      $sel = ($session['id']==$sessionId) ? 'selected' : '';
      $shortname=substr($session['name'],0,90);
      echo "<option value='".$session['id']."'".$sel.">".$shortname."</option>";
    }
    echo"</select>\n";
  }

  // Set any existing parameters in form
  $runidval = ($_POST['runid']) ? $_POST['runid'] : 'run1';
  $presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
  $sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
  $defocpaircheck = ($_POST['defocpair']=='on') ? 'CHECKED' : '';
  $shiftonlycheck = ($_POST['shiftonly']=='on') ? 'CHECKED' : '';
  $contcheck = ($_POST['cont']=='on') ? 'CHECKED' : '';
  $commitcheck = ($_POST['commit']=='on') ? 'CHECKED' : '';
  $diamval = ($_POST['diam']) ? "VALUE='".$_POST['diam']."'" : ''; 
  $lpval = ($_POST['lp']) ? $_POST['lp'] : '30';
  $hpval = ($_POST['hp']) ? $_POST['hp'] : '600';
  $binval = ($_POST['bin']) ? $_POST['bin'] : '4';
  if ($_POST['threshcheck']=='auto') {
    $pikval = $_POST['autopik'];
    $manualval = '0.4';
    $autocheck='CHECKED';
    $manualcheck='';
    $autodisable='';
    $manualdisable='DISABLED';
  }
  else {
    $pikval = '100';
    $manualval = $_POST['thresh'];
    $autocheck='';
    $manualcheck='CHECKED';
    $autodisable='DISABLED';
    $manualdisable='';
  }
  $testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
  $testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
  $testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

  echo"
  <P>
  <TABLE BORDER=0 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>
    <TABLE CELLPADDING='5' BORDER='0'>
    <TR>
      <TD VALIGN='TOP'>
      <A HREF=\"javascript:infopopup('runid')\"><B>Selexon Run Name:</B></A>
      <INPUT TYPE='text' NAME='runid' VALUE='$runidval'>
      <HR>
      </TD>
    </TR>
    <TR>
      <TD VALIGN='TOP'>   
      <B>Output Directory:</B><BR>
      <INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='38'>
      </TD>
    </TR>
    <TR
      <TD>\n";

  if ($presets) {
    echo"<B>Preset</B>\n<SELECT NAME='preset'>\n";
    foreach ($presets as $preset) {
      echo "<OPTION VALUE='$preset' ";
      // make en selected by default
      if ($preset==$presetval) echo "SELECTED";
      echo ">$preset</OPTION>\n";
    }
  }
  else {
    echo"<FONT COLOR='RED'><B>No Presets for this Session</B></FONT>\n";
  }
  echo"
      </SELECT>
      </TD>
    </TR>
    <TR>
      <TD>
      <INPUT TYPE='checkbox' NAME='defocpair' $defocpaircheck>
      Calculate Shifts for Defocal Pairs<BR>
      <INPUT TYPE='checkbox' NAME='shiftonly' $shiftonlycheck>
      ONLY Calculate Shifts for Pairs<BR>
      <INPUT TYPE='checkbox' NAME='cont' $contcheck>
      Continue<BR>
      <INPUT TYPE='checkbox' NAME='commit' $commitcheck>
      Commit to Database<BR>
      </TD>
    </TR>
    </TABLE>
    </TD>
    <TD CLASS='tablebg'>
    <TABLE CELLPADDING='5' BORDER='0'>
    <TR>
      <TD VALIGN='TOP'>
      <INPUT TYPE='text' NAME='diam' SIZE='5' $diamval>
      Particle Diameter (in Angstroms)
      </TD>
    </TR>
    <TR>
      <TD VALIGN='TOP'>
      <B>Filter Values:</B></A><BR>
      <INPUT TYPE='text' NAME='lp' VALUE='$lpval' SIZE='4'>
      Low Pass<BR>
      <INPUT TYPE='text' NAME='hp' VALUE='$hpval' SIZE='4'>
      High Pass<BR>
      <INPUT TYPE='text' NAME='bin' VALUE='$binval' SIZE='4'>
      Binning<BR>
    </TR>
    <TR>
      <TD>
      <INPUT TYPE='radio' NAME='threshcheck' onclick='enable(\"auto\")' $autocheck VALUE='auto'>
      Automatically Set Threshold<BR>
      Avg Particles Per Micrograph:<INPUT TYPE='text' $autodisable NAME='autopik' VALUE='$pikval' SIZE='5'>
      <P>
      <INPUT TYPE='radio' NAME='threshcheck' onclick='enable(\"manual\")' $manualcheck VALUE='manual'>
      Set Manual Threshold<BR>
      <INPUT TYPE='text' NAME='thresh' $manualdisable VALUE='$manualval' SIZE='4'>
      (0.0 - 1.0)
      </TD>
    </TR>
    </TABLE>
    </TD>
  </TR>
  <TR>
    <TD COLSPAN='2' ALIGN='CENTER'>
    <HR>
    <INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
    Test these setting on image:
    <INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
    <HR>
    </TD>
  </TR>
  <TR>
    <TD COLSPAN='2' ALIGN='CENTER'>
    Host: <select name='host'>\n";
  foreach($hosts as $host) {
    $s = ($_POST['host']==$host) ? 'selected' : '';
    echo "<option $s >$host</option>\n";
  }
  echo "</select>
  User: <select name='user'>\n";
  foreach($users as $user) {
    $s = ($_POST['user']==$user) ? 'selected' : '';
    echo "<option $s >$user</option>\n";
  }
  echo"
    </select>
    <BR>
    <input type='submit' name='process' value='Run Selexon'><BR>
    <FONT COLOR='RED'>Submission will NOT run ACE, only output that command that you can copy and paste into a unix shell</FONT>    </TD>
  </TR>
  </TABLE>
  </TD>
  </TR>
  </TABLE>
  <B>Using Templates:</B>
  <TABLE><TR>
    <TD>\n";
  // Display the templates that will be used for selexon
  echo "<INPUT TYPE='hidden' NAME='templateList' VALUE='$templateList'>\n";
  echo "<INPUT TYPE='hidden' NAME='templates' VALUE='continue'>\n";
  echo "<INPUT TYPE='hidden' NAME='numtemplates' VALUE='$numtemplates'>\n";
  echo "<INPUT TYPE='hidden' NAME='sessionname' VALUE='$sessionname'>\n";
  echo "$templateForm\n";
  echo "$templateTable\n";
  ?>
    </TD>
  </TR></TABLE>

  </CENTER>
  </FORM>
  <?
  writeBottom();
}

function runSelexon() {
        $host = $_POST['host'];
	$user = $_POST['user'];
 
	//make sure a session was selected
	if (!$_POST[outdir]) {
	        createSelexonForm("<B>ERROR:</B> Select an experiment session");
		exit;
	}
	$outdir=$_POST[outdir];
	// make sure outdir ends with '/'
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$runid=$_POST[runid];
	$templateList=$_POST[templateList];
	$templates=split(",", $templateList);

	// get the list of templates
	$i=1;
	foreach ($templates as $tmplt) {
	        list($tmpltNum,$tmpltId)=split(":",$tmplt);
		$templateIds.="$tmpltId,";
		$tmpltstrt="template".$tmpltNum."strt";
		$tmpltend="template".$tmpltNum."end";
		$tmpltincr="template".$tmpltNum."incr";
		// set the ranges specified
		$rangenum="range".$i;
		if ($_POST[$tmpltstrt]!=''){
		        $range=$_POST[$tmpltstrt].",".$_POST[$tmpltend].",".$_POST[$tmpltincr];
		}
		// if no rotation
		else {
		        $range="0,10,20";
		}
		$ranges[$rangenum]=$range;
		$i++;
	}
	$templateIds=substr($templateIds,0,-1);
  
	$defocpair= ($_POST[defocpair]=="on") ? "1" : "0";
	$shiftonly= ($_POST[shiftonly]=="on") ? "1" : "0";
	$continue = ($_POST[cont]=="on") ? "1" : "0";
	$commit = ($_POST[commit]=="on") ? "1" : "0";
	$diam = $_POST[diam];
	if (!$diam) {
	        createSelexonForm("<B>ERROR:</B> Specify a particle diameter");
		exit;
	}
	$lp = $_POST[lp];
	$hp = $_POST[hp];
	$bin = $_POST[bin];
	if ($_POST[threshcheck]=="auto") $autopik=$_POST[autopik];
	elseif ($_POST[threshcheck]=="manual") $thresh=$_POST[thresh];
	if (!$autopik && !$thresh) {
	        createSelexonForm("<B>ERROR:</B> No thresholding value was entered");
		exit;
	}

	if ($_POST['testimage']=="on") {
	        if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		else {
		        createSelexonForm("<B>ERROR:</B> Specify an mrc file to test these parameters");
			exit;
		}
	}
	elseif ($_POST['sessionname']) {
	        if ($_POST['preset']) $dbimages=$_POST[sessionname].",".$_POST[preset];
		else {
		        createSelexonForm("<B>ERROR:</B> Select an image preset for template matching");
			exit;
		}
	}

//	$command ="source /ami/sw/ami.csh;";
//	$command.="source /ami/sw/share/python/usepython.csh common32;";
//	$command.="source /home/$user/pyappion/useappion.csh;";
	$command.="/home/glander/pyappion/particle_manager/selexon.py ";
	if ($testimage) $command.="$testimage ";
	else $command.="dbimages=$dbimages ";
	$command.="templateIds=$templateIds ";
	foreach ($ranges as $rangenum=>$rangevals) {
	        $command.="$rangenum=$rangevals ";
	}	
	$command.="runid=$runid ";
	$command.="outdir=$outdir ";
	$command.="diam=$diam ";
	$command.="lp=$lp ";
	$command.="hp=$hp ";
	$command.="bin=$bin";
	if ($autopik) $command.=" autopik=$autopik";
	if ($thresh) $command.=" thresh=$thresh";
	if ($shiftonly==1) $command.=" shiftonly";
	if ($defocpair==1) $command.=" defocpair";
	if ($continue==1) $command.=" continue";
	if ($commit==1) $command.=" commit";

	$cmd = "exec ssh $user@$host '$command > selexonlog.txt &'";
//	exec($cmd ,$result);

	writeTop("PySelexon Results","PySelexon Results");

	if ($testimage) {
	        $jpgimg=$outdir.$runid."/jpgs/".$testimage.".prtl.jpg";
		$ccclist=array();
		$i=1;
		foreach ($templates as $tmplt) {
		        $cccimg=$outdir.$runid."/cccmaxmap".$i."00.mrc";
		        $ccclist[]=$cccimg;
			$i++;
		}
		$images=writeTestResults($jpgimg,$ccclist);
		createSelexonForm($images,'PySelexon Results','');
		exit;
	}

	echo"
  <P>
  <TABLE WIDTH='600'>
  <TR><TD COLSPAN='2'>
  <B>Selexon Command:</B><BR>
  $command<HR>
  </TD></TR>
  <TR><TD>outdir</TD><TD>$outdir</TD></TR>
  <TR><TD>templateIds</TD><TD>$templateIds</TD></TR>";
	foreach ($ranges as $rangenum=>$rangevals) {
	        echo "<TR><TD>$rangenum</TD><TD>$rangevals</TD></TR>\n";
	}
	echo"<TR><TD>runid</TD><TD>$runid</TD></TR>
  <TR><TD>testimage</TD><TD>$testimage</TD></TR>
  <TR><TD>dbimages</TD><TD>$dbimages</TD></TR>
  <TR><TD>diameter</TD><TD>$diam</TD></TR>
  <TR><TD>lp</TD><TD>$lp</TD></TR>
  <TR><TD>hp</TD><TD>$hp</TD></TR>
  <TR><TD>bin</TD><TD>$bin</TD></TR>\n";
	if ($autopik) echo "<TR><TD>autopik</TD><TD>$autopik</TD></TR>\n";
	elseif ($thresh) echo "<TR><TD>manualthresh</TD><TD>$thresh</TD></TR>\n";
	echo"<TR><TD>defocuspair</TD><TD>$defocpair</TD></TR>
  <TR><TD>shiftonly</TD><TD>$shiftonly</TD></TR>
  <TR><TD>continue</TD><TD>$continue</TD></TR>
  <TR><TD>commit</TD><TD>$commit</TD></TR>
  </TABLE>\n";
	writeBottom();
}

function writeTestResults($jpg,$ccclist){
        echo"<CENTER>\n";
        echo"<A HREF='loadimg.php?filename=$jpg&scale=0.8'>\n";
        echo"<IMG SRC='loadimg.php?filename=$jpg&scale=0.35'></A>\n";
	if (count($ccclist)>1) echo "<BR>\n";
	foreach ($ccclist as $ccc){
	        echo"<A HREF='loadmrc.php?filename=$ccc&scale=0.8'>\n";
	        echo"<IMG SRC='loadmrc.php?filename=$ccc&scale=0.35'></A>\n";
	}
	echo"</CENTER>\n";
}

?>
