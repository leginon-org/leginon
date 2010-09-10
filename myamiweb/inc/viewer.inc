<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "config.php";
require_once "inc/util.inc";
require_once "inc/mysql.inc";
require_once "inc/button.inc";
require_once "inc/pref.inc";
require_once "inc/ace.inc";
if (ENABLE_LOGIN) {
	require_once "inc/dbemauth.php";
}

$VIEWNB=0;

/**
 *	Viewer
 *
 *	@example simpleviewer.phps How to use
 *
 *
 */

class viewer {

	var $crlf="\n";
	var $nbview=0;
	var $debug=false;

	var $jsparams;

	function viewer() {
	}

	function displayDebug() {
		$this->debug=true;
	}

	function setSessionId($sessionId) {
		$this->sessionId=$sessionId;
	}

	function setProjectId($projectId) {
		$this->projectId=$projectId;
	}

	function setImageId($imageId) {
		$this->imageId=$imageId;
	}

	function setUsername($username) {
		$this->username=$username;
	}

	function setCommentBox($array) {
		if (is_array($array) && !empty($array))
			$this->comment_box_val=$array;
	}

	function setCommentId($id) {
		$this->commentId=$id;
	}

	function addProjectSelector($projects=array(), $currentproject=false) {
		$projectselector = '<select name="projectId" onchange="newexp()">'.$this->crlf;
		foreach ($projects as $project) {
			if ($project['id']==$this->projectId) $s='selected'; else $s='';
			if ($project['age'] && $project['age'] < 30) $style="style='background-color: Beige;'"; else $style='';
			$projectselector .= "<option $style value=".$project['id']." ".$s." >"
						.substr($project[name],0,32)." (".$project['id'].")</option>".$this->crlf; 
		}
		$projectselector .= '</select>'.$this->crlf;
		if ($currentproject) {
			$name = $currentproject['name'];
			$id = $currentproject['projectId'];
		if ($this->projectId==$id) 
			$projectselector .= '<br>Select <a href="javascript:setproject(\'all\')">all projects</a>'.$this->crlf;
		else
			$projectselector .= '<br>Select <a href="javascript:setproject('.$id.')">'.$name.' project</a>'.$this->crlf;

		}
		$this->addprojectsel = $projectselector;
	}

	function addFilterSelector($filters=array()) {
		$filterselector = '<select name="filterId" onchange="get_image_list()">'.$this->crlf;
		foreach ($filters as $filter) {
			if ($filter[id]==$this->filterId) $s='selected'; else $s='';
			$filterselector .= '<option value='.$filter[id].' '.$s.' >'
						.$filter[name].'</option>'.$this->crlf; 
		}
		$filterselector .= '</select>'.$this->crlf;
		$this->addfiltersel = $filterselector;
	}

	function addSessionSelector($sessions=array()) {
		$selector = '<select name="sessionId" onchange="newexp()">'.$this->crlf;
		foreach ((array)$sessions as $session) {
			if ($session[id]==$this->sessionId) $s='selected'; else $s='';
			$maxlength=70;
			if (strlen($session[name])>$maxlength) {
				$session[name]=substr($session[name],0,$maxlength)."... ";
			}
			$selector .= '<option value='.$session[id].' '.$s.' >'
					.$session[name].'</option>'.$this->crlf; 
		}
		$selector .= '</select>';
		$selector .= '<input type="hidden" name="sessionIdmemo" value="'.$this->sessionId.'">';
		$this->addsessionsel = $selector;
	}

	function addLoiControl($refreshtime="") {
		if (empty($refreshtime))
			$refreshtime = 10;
		$btstop = new button('st1', 'stop');
		$btstop->setLink('javascript:stop()');
		$btstart = new button('st2', 'start');
		$btstart->setLink('javascript:start()');
		$loijavascript = ''
		.$btstop->getJavascript().$this->crlf
		.$btstart->getJavascript().$this->crlf
		.'var mintime=1000;'.$this->crlf
		.'var maxtime=60000;'.$this->crlf
		.'var refreshtime=10000;'.$this->crlf
		.'window.name="loi";'.$this->crlf
		.''.$this->crlf
		.'function start(){'.$this->crlf
		.'	if (cif=this.myif) {'.$this->crlf
		.'		formatrefreshtime()'.$this->crlf
		.'		cif.start(refreshtime)'.$this->crlf
		.'	}'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function formatrefreshtime() {'.$this->crlf
		.'	refreshtime=parseInt(document.viewerform.refreshtime.value)*1000;'.$this->crlf
		.'	if (!refreshtime || refreshtime<mintime)'.$this->crlf
		.'		refreshtime = mintime;'.$this->crlf
		.'	if (refreshtime>maxtime)'.$this->crlf
		.'		refreshtime = maxtime;'.$this->crlf
		.'	document.viewerform.refreshtime.value = refreshtime/1000;'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function stop() {'.$this->crlf
		.'	if (cif=this.myif) {'.$this->crlf
		.'		cif.stop();'.$this->crlf
		.'	}'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function reset(id) {'.$this->crlf
		.'	jsimgId=id;'.$this->crlf
		.'	updateviews();'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf;

		$loicontrol = ''
		.'<table border="0">'.$this->crlf
		.'<tr>'.$this->crlf
		.'<td>'.$this->crlf
		.'	<label for="refreshtime">Refresh (s):</label>'.$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'	<input class="field" type="text" name="refreshtime" size="4" value="'.$refreshtime.'">'.$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'	'.$btstop->display().$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'	'.$btstart->display().$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'<iframe name="myif" '.$this->crlf
		.'	src="getlastfileid.php?session='.$this->sessionId.'"'.$this->crlf
		.'	frameborder="0" width="0" height="0"'.$this->crlf
		.'	marginheight="0" marginwidth="0"'.$this->crlf
		.'	scrolling="no" ></iframe>'.$this->crlf
		.'</td>'.$this->crlf
		.'</tr>'.$this->crlf
		.'</table>'.$this->crlf;

		$this->addloicontrol = $loicontrol;
		$this->addloijavascript = $loijavascript;
	}

	function addPlaybackControl($refreshtime="") {
		$btrstartpl = new button('st3pl', 'rstart');
		$btrstartpl->setLink('javascript:rstartpl()');
		$btstoppl = new button('st1pl', 'stop');
		$btstoppl->setLink('javascript:stoppl()');
		$btstartpl = new button('st2pl', 'start');
		$btstartpl->setLink('javascript:startpl()');
		$playbackjavascript = ''
		.$btstoppl->getJavascript().$this->crlf
		.$btstartpl->getJavascript().$this->crlf
		.$btrstartpl->getJavascript().$this->crlf
		.'var mintime=100;'.$this->crlf
		.'var maxtime=60000;'.$this->crlf
		.'var refreshtime=10000;'.$this->crlf
		.''.$this->crlf
		.'function startpl(){'.$this->crlf
		.'		formatrefreshtimepl();'.$this->crlf
		.'		startPlayback(refreshtime);'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function rstartpl(){'.$this->crlf
		.'		formatrefreshtimepl();'.$this->crlf
		.'		rstartPlayback(refreshtime);'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function formatrefreshtimepl() {'.$this->crlf
		.'	refreshtime=parseFloat(document.viewerform.refreshtimepl.value)*1000;'.$this->crlf
		.'	if (!refreshtime || refreshtime<mintime)'.$this->crlf
		.'		refreshtime = mintime;'.$this->crlf
		.'	if (refreshtime>maxtime)'.$this->crlf
		.'		refreshtime = maxtime;'.$this->crlf
		.'	document.viewerform.refreshtimepl.value = refreshtime/1000;'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function stoppl() {'.$this->crlf
		.'	stopPlayback();'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function resetpl(id) {'.$this->crlf
		.'	jsimgId=id;'.$this->crlf
		.'	updateviews();'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf;

		$playback= ''
		.'<li class="buttonmenu">'
		.'<input type="hidden" name="refreshtimepl" size="4" value="'.$refreshtime.'">'.$this->crlf
		.'</li>'
		.'<li class="buttonmenu">'
		.$btrstartpl->display()
		.'</li>'
		.'<li  class="buttonmenu">'
		.$btstoppl->display()
		.'</li>'
		.'<li class="buttonmenu">'
		.$btstartpl->display()
		.'</li>';

		$this->addplaybackcontrol = $playback;
		$this->addplaybackjavascript = $playbackjavascript;
	}

	function getPlaybackControl() {
		return $this->addplaybackcontrol;
	}

	function addCommentBox() {
		$this->addcommentbox = true;
	}

	function addQueueCountBox() {
		$this->qcountbox = true;
	}

	function addFileSelector($filenames=array(), $size=40) {
		if ($size) $htmlsize = "size=$size";
		$selector = '#images :'.count($filenames).'<br />';
		$selector .= '<select style="width: 250px" name="imageId" '.$htmlsize .' >'.$this->crlf;
		$default = ($this->imageId) ? $this->imageId : $filenames[0][id];
		foreach ((array)$filenames as $filename) {
			$filestr = ereg_replace('[[:alnum:]]+_(.*)', '\1', $filename[name]);
			$filestr = ereg_replace('_0*', '_', $filestr);
			$filestr = ereg_replace('^0*', '', $filestr);
			$filestr = ereg_replace('_v[0-2][0-9]_', '_', $filestr);
			$filestr = ereg_replace('grid', 'gr', $filestr);
			$filestr = ereg_replace('square', 'sq', $filestr);
			$filestr = ereg_replace('hole', 'hl', $filestr);
			$filestr = ereg_replace('focus', 'fc', $filestr);
			if ($filename[id]==$default) $s='selected'; else $s='';
				$selector .= '<option value='.$filename[id].' '.$s.' >'.$filestr.$this->crlf; 
		}
		$selector .= '</select>';
		$this->addfilesel = $selector;
	}

	function addjs($jsdata) {
			$this->jsparams.=$jsdata;
	}

	function getJavascript() {
		$str = '<script type="text/javascript" src="js/viewer.js"></script>'.$this->crlf;
		$str .= '<script type="text/javascript" src="js/button.js"></script>'.$this->crlf;
		$str .= '<script type="text/javascript" src="js/dropdiv.js"></script>'.$this->crlf;
		$str .= '<script type="text/javascript">'.$this->crlf;
		if ($params=$this->jsparams) {
			$str .= $params;
			$str .= $this->crlf;
		}
		if ($this->sessionId)
			$str .= 'var jsSessionId = '.$this->sessionId.";".$this->crlf;
		if ($this->commentId)
			$str .= 'var jsCommentId = '.$this->commentId.";".$this->crlf;
		if ($this->username)
			$str .= 'var jsUsername = "'.$this->username.'";'.$this->crlf;
		$str .= js_vars_from_post();
		$jsimgId = ($this->imageId) ? ' = '.$this->imageId.';' : ';';
		$str .= 'var jsimgId'.$jsimgId.$this->crlf;
		$str .= 'var key_up_unicode = 38;'.$this->crlf;
		$str .= 'var key_down_unicode = 40;'.$this->crlf;
		$str .= 'var eventdown = "keydown";'.$this->crlf;
		$str .= 'var eventup = "keyup";'.$this->crlf;
		$str .= 'var eventchange  = "change";'.$this->crlf;
		$str .= 'var keydown = false;'.$this->crlf;
		$str .= 'var interval;'.$this->crlf;
		$str .= 'var count;'.$this->crlf;
		$str .= 'var begin;'.$this->crlf;
		$str .= 'var end;'.$this->crlf;
		$str .= 'var mainview;'.$this->crlf;

		$str .= ''.$this->crlf;
		if ($this->addloijavascript)
			$str .= $this->addloijavascript;
		if ($this->addplaybackjavascript)
			$str .= $this->addplaybackjavascript;
		$str .= '</script>'.$this->crlf;
		return $str;
	}

	function getJavascriptInit() {
		$initbuttons="";
		$nv=0;
		$init = '<script type="text/javascript">'.$this->crlf;
		$init .= 'var jsviews = new Array();'.$this->crlf;
		$init .= 'var jscomments = new Array();'.$this->crlf;
		$init .= 'var bt_hide_state = false;'.$this->crlf;
		foreach ($this->views as $v) {
			if ($v->ismaster) {
				$init .= 'var jsmasterview = "'.$v->getName().'";'.$this->crlf;
			}
			$init .= $v->getJavascriptvar();
		}

		foreach ($this->views as $v) {
			$init .= $v->getJavascriptButton();
			$init .= 'jsviews['.$nv.']="'.$v->getName().'";'.$this->crlf;
			$nv++;
		}
		$init .= 'function updateviews() { '.$this->crlf;
		if ($this->qcountbox) {
			$init .= 'setQueueTiming();'.$this->crlf;
		}
		$init .= 'setimgId();'.$this->crlf;
		if ($this->displaytargetstats)
			$init .= 'getTargetStats();'.$this->crlf;
		foreach ($this->views as $v) {
			$name = $v->getName();
			$init .= '	newfile("'.$name.'");'.$this->crlf;
			$init .= '	setImageHistogram("'.$name.'");'.$this->crlf;
			if ($v->getJavaScriptInit())
				$initbuttons .= $v->getJavaScriptInit().$this->crlf;
		}
		$init .= '}'.$this->crlf;
		$init .= ''.$this->crlf;
		$init .= 'function initviewer() { '.$this->crlf;
		$init .= 'mainview=getMainView();'.$this->crlf;
		foreach ($this->views as $v) {
			$name = $v->getName();
			$init .= 'getParticleStat("'.$name.'");'.$this->crlf;
			$init .= 'setPtclParam("'.$name.'");'.$this->crlf;
		}
		if (!empty($initbuttons))
			$init .= $initbuttons.$this->crlf;
		$init .= 'setevents();'.$this->crlf;
		$init .= 'updateviews();'.$this->crlf;
		$init .= 'document.onkeydown = getKey;'.$this->crlf;
		if ($this->addloijavascript)
			$init .= '	start();'.$this->crlf;
		if ($this->comment_box_val) {
			$cb=0;
			foreach($this->comment_box_val as $box_name) {
				$init .= 'jscomments['.$cb.']="'.$box_name.'";'.$this->crlf;
				$cb++;
			}
		}
		$init .= '}'.$this->crlf;
		$init .= ''.$this->crlf;
		$init .= '</script>'.$this->crlf;
		return $init;
	}

	function add($view) {
		$view->setRestriction();
		$this->views[] = $view;
		$this->nbview++;
	}

	function display() {
		$nbviewperrow = ($this->nbviewperrow) ? $this->nbviewperrow : '3';
		$n=1;
		$display = '<form method="post" name="viewerform"  '.
				'action="'.$_SERVER['PHP_SELF'].'">'.$this->crlf;
		if ($this->debug) {
		$display .= '<textarea class="textarea" name=debug rows=10 cols=50></textarea>';
		$display .= '<input class="bt1" type="button" value="clear" onclick="javascript:document.viewerform.debug.value=\'\'">';
		$fct = "cle(document.viewerform.fctval.value)";
		$display .= '<input class="bt1" type="button" value="eval" onclick="'.$fct.'">';
		$display .= '<input class="bt1" name="fctval" type="text" size="50">';
		}
		if ($this->addloicontrol || $this->addcommentbox || $this->addplaybackcontrol) 
			$display .= '<table border="0"><tr valign="top">';
		if ($this->addloicontrol ) {
			$display .= '<td>';
			$display .= $this->addloicontrol;
			$display .= '</td>';
		}
		if ($this->addcommentbox) {
			$display .= '<td>';
			$display .='<div id="commentboxdiv" style="position:relative; border: 0px #696969 solid" >';
			$display .= '
 <table border="0" cellpadding="3" >
  <tr valign="top" width=50>
   <td>name<br>
   <input class="field" type="text" name="name" size="20" maxlength="20"
	value=""> 
	<div><div id="commentdiv" style="position:absolute; z-index:99; visibility: hidden"><img alt="comment" src="addcomment.php" name="commentimg" ></div></div>
   </td>
   <td rowspan="2" >comment<br>
   <textarea class="textarea" name="comment" rows="5" cols="20" wrap="virtual"
></textarea>
  </td>
  </tr>
  <tr>
   <td>
    <input class="bt1" type="button" name="action" value="Save" onclick=\'addComment()\'/>
   </td>
  </tr>
 </table>
';
			$display .= '</div>';
			$display .= '</td>';
		}
		if ($this->qcountbox) {
			$display .= '<td>';
			$display .='<div id="qcount"></div>';
			$display .= '</td>';
		}
		if ($this->displaytargetstats) {
			$display .= '<td>';
			$display .='<div id="targetstats" style="position:relative; width:150px; border: 1px #696969 solid" >Targets:</div>';
			$display .= '</td>';
		}
		if ($this->addloicontrol || $this->addcommentbox || $this->addplaybackcontrol) 
			$display .= '</tr></table>';
		$display .= '<table border="0">';
		if ($this->addsessionsel) {
			$display .= '<tr valign="top">';
			if ($this->addprojectsel || $this->addfiltersel) {
				$display .= '<td>';
				$display .= $this->addprojectsel;
				if ($this->addfiltersel) {
				$display .= "<br>";
					$display .= $this->addfiltersel;
				}
				$display .= '</td>';
			}
			$display .= '<td colspan=2>';
			$display .= $this->addsessionsel;
			$display .= '</td>';
			$display .= '</tr>';
		}
		$display .= '<tr>';
		if ($this->addfilesel) {
			$display .= '<td valign="top">';
			$display .= $this->addfilesel;
			$display .= '</td>';
		}
		if ($this->comment_box_val) {
		$display .= '<td valign="top">';
		foreach($this->comment_box_val as $box_name) {
			$display .= add_comment_box($box_name);
			$display .= '<br>';
		}
		$display .= '<input class="bt1" type="button" name="action_comment_box " '
				.'value="Save" onclick=\'addCommentBox()\'/>';
		$display .= '<input class="bt1" type="button" name="action_comment_box " '
				.'value="Clear" onclick=\'clearCommentBox()\'/>';
		$display .= '<input class="bt1" type="button" name="action_update_list" '
				.'value="Remove" onclick=\'update_image_list()\'/>';
		$display .= '<div><div id="commentboxdiv" style="position:absolute; z-index:99; visibility: hidden"><img alt="commentbox" src="addcommentbox.php" name="commentboximg" ></div></div>';
		$display .= '</td>';
		}
		$display .= '<td valign="top">';
		$display .= '<table border="0"><tr>';
		$viewoff = array();
		foreach ($this->views as $v) {
			if ($v->getViewState()== "true" ) {	
				$display .= '<td '.$v->getSpan().' valign="top">'.$v->display().'</td>';
			} else {
				$display .= '<td>&nbsp;<td>';
				$viewoff[]=$v;
			}
			if ($n % $nbviewperrow == 0) {
				$display .= '</tr><tr>';
			}
			$n++;
		}
		$display .= '</tr></table>';
		$display .= '</td>';
		$display .= '</tr></table>';
		$nbv=1;
		$display .= '<table border="0"><tr>';
		foreach($viewoff as $voff) {
			$voff->setSize(150);
			$display .= '<td>'.$voff->display().'</td>';
			if ($nbv % 3 == 0)
				$display .= "</tr><tr>";
			$nbv++;
		}
		$display .= '</tr></table>';
		$display .= '</form>';
		echo $display;
	}

	function setNbViewPerRow($n) {
		$this->nbviewperrow=$n;
	}

}

class view {

	var $crlf="\n";
	var $size=256;
	var $displayview='true';
	var $params;

	function view($title, $name) {
		global $VIEWNB;
		$this->viewnb = $VIEWNB++;
		$this->title = $title;
		$this->name = $name;
		$this->displayname = $this->name.'view';
		$this->displayPresets(true);
		$this->displayComment(false);
		$this->btdownload = new button('download'.$this->name, 'dwd');
		$this->btdownload->setLink('download.php','');
		$this->displayscaleicon = true;
		$this->btinfo = new button('info'.$this->name, 'info');
		$this->btinfo->setLink('imgreport.php','imginfo');
		$this->btscale = new toggleButton($this->name.'scale', 'scale');
		$this->btscale->onToggle($name.'btscaleaction');
		$this->bttarget = new toggleButton($this->name.'target', 'target');
		$this->bttarget->onToggle($name.'bttargetaction');
		$this->bttag = new toggleButton($this->name.'tag', 'tag');
		$this->bttag->onToggle($name.'bttagaction');
		$this->btfft = new toggleButton($this->name.'fft', 'fft');
		$this->btfft->onToggle($name.'btfftaction'); 
		$this->btclose = new toggleButton($this->name.'close', 'open', 'close');
		$this->btclose->onToggle($name.'btcloseaction'); 
		$this->btnptcl = new toggleButton($this->name.'nptcl', 'ptcl');
		$this->btnptcl->onToggle($name.'btnptclaction');
		$this->btace = new toggleButton($this->name.'ace', 'ace');
		$this->btace->onToggle($name.'btaceaction'); 
		$this->btdeq = new button('deq'.$this->name, 'deq');

		$param = "left=0,top=".($this->viewnb*180+20).",height=170,width=370";
		$url = "ptclsel.php?name=$name&displayname=$this->title";
		$pli =	"javascript:popUpPtcl('".$url."','".$name."','".$param."');";
		$this->btparticle = new button('ptcl'.$this->name, 'ptcl');
		$this->btparticle->setLink($pli);
		$this->displayscaleicon = true;
		$this->displayscaleicon = true;
		$this->displaytargeticon = true;
		$this->displaytagicon = true;
		$this->displaynptclicon = true;
		$this->displayffticon = true;
		$this->displayaceicon = true;
		$this->displayinfoicon = true;
		$this->displayparticleicon = false;
		$this->displaydownloadicon = true;
		$this->displaydeqicon = false;
		$this->displaycloseicon = true;
		$this->displayadjustlink = true;
		$this->displayexportlink = true;
		$this->displayhidebt = true;
		$this->displayhideallbt = true;
		$this->displaynextbt = true;
		$this->displayexemplarbt = true;
		$this->framecolor = ' class="bgcolor1" ';
		$this->menucolor = ' class="bgimg1" ';
		$this->presetscript = 'getpreset.php';
		$this->reportscript = 'imgreport.php';
		$this->dwdscript = 'download.php';
		$this->histoscript = 'imagehistogram.php';
		$this->imagescript = 'getimg.php';
		$this->commentscript = 'getcomment.php';
		$this->scale_st = "false";
		$this->target_st = "false";
		$this->tag_st = "false";
		$this->nptcl_st = "false";
		$this->btscalestate = "true";
		$this->bttargetstate = "true";
		$this->bttagstate = "true";
		$this->btfftstate = "false";
		$this->btnptclstate = "false";
		$this->quality = "80";
		$this->gradient = "";
		$this->filter= "default";
		$this->binning= "auto";
		$this->autoscale = "s;3";
		$this->displayfilename = "0";
		$this->loadjpg= "1";
		$this->ptclsel = "0";
		$this->jsacepar= "1";
		$this->jsaceopt= "2";
		$this->jstagpar1 = "1";
		$this->jstagpar2 = "1";
		if ($_POST) {
			$this->jstagpar1 = ($_REQUEST[$this->name.'tagp1']) ? "1" : $_POST[$this->name.'tagp1'];
			$this->jstagpar2 = ($_REQUEST[$this->name.'tagp2']) ? "1" : "0";
		}
		$this->jsprtlpick= "1";
		$this->ptclselmemo = $this->name.'psel';
		$this->qualitymemo = $this->name.'q';
		$this->gradientmemo = $this->name.'gr';
		$this->binningmemo = $this->name.'b';
		$this->filtermemo = $this->name.'f';
		$this->maxpixmemo = $this->name.'maxpix';
		$this->minpixmemo = $this->name.'minpix';
		$this->autoscalememo = $this->name.'autos';
		$this->displayfilenamememo= $this->name.'df';
		$this->loadjpgmemo= $this->name.'df';
		$this->btfftmemo = $this->name.'fft_bt_st';
		$this->bttagmemo = $this->name.'tag_bt_st';
		$this->btnptclmemo = $this->name.'nptcl_bt_st';
		$this->bttargetmemo = $this->name.'target_bt_st';
		$this->btscalememo = $this->name.'scale_bt_st';
		if ($ptcl=$_REQUEST[$this->ptclselmemo])
			$this->ptclsel = $ptcl;
		if ($quality=$_REQUEST[$this->qualitymemo])
			$this->quality = $quality;
		if ($gradient=$_REQUEST[$this->gradientmemo])
			$this->gradient = $gradient;
		if ($binning=$_REQUEST[$this->binningmemo])
			$this->binning = $binning;
		if ($filter=$_REQUEST[$this->filtermemo])
			$this->filter = $filter;
		if ($minpix=$_REQUEST[$this->minpixmemo])
			$this->minpix = $minpix;
		if ($maxpix=$_REQUEST[$this->maxpixmemo])
			$this->maxpix = $maxpix;
		if ($autoscale=$_REQUEST[$this->autoscalememo])
			$this->autoscale= $autoscale;
		if ($displayfilename=$_REQUEST[$this->displayfilenamememo])
			$this->displayfilename= $displayfilename;
		if ($loadjpg=$_REQUEST[$this->loadjpgmemo])
			$this->loadjpg= $loadjpg;
		if ($btfftstate=$_REQUEST[$this->btfftmemo])
			$this->btfftstate = $btfftstate;
		if ($btacestate=$_REQUEST[$this->btacememo])
			$this->btacestate = $btacestate;
		if ($bttargetstate=$_REQUEST[$this->bttargetmemo])
			$this->bttargetstate = $bttargetstate;
		if ($bttagstate=$_REQUEST[$this->bttagmemo])
			$this->bttagstate = $bttagstate;
		if ($btnptclstate=$_REQUEST[$this->btnptclmemo])
			$this->btnptclstate = $btnptclstate;
		if ($btscalestate=$_REQUEST[$this->btscalememo])
			$this->btscalestate = $btscalestate;
	}

	function setParam($key, $value) {
		$this->params[$key]=$value;
	}

	function addMenuItems($newitems) {
		$this->newitems = $newitems;
	}

	function setMinpix($n) {
		if (is_numeric($n))
			$this->minpix = $n;
	}

	function setMaxpix($n) {
		if (is_numeric($n))
			$this->maxpix = $n;
	}

	function setFFT($state) {
		if ($state)
			$this->btfftstate = "on";
	}

	function setAutoScale($state) {
		if ($state)
			$this->autoscale= "1";
	}

	function setSize($size) {
		$this->size = $size;
	}

	function setComment($comment) {
		$this->comment = $comment;
	}

	function getSize() {
		return $this->size;
	}

	function setSpan($r='', $c='') {
		$span  = ($r) ? "rowspan=$r" : "";
		$span  .= ($c) ? " colspan=$c" : "";
		$this->span = $span;
	}

	function getSpan() {
		return $this->span;
	}


	function setControl() {
		$this->ismaster = true;
	}

	function getName() {
		return $this->name;
	}

	function setDataTypes($datatypes) {
		$this->datatypes = $datatypes;
	}

	function setImageId($imageId) {
		$this->imageId=$imageId;
	}

	function displayPresets($state) {
		$this->displaypreset= $state;
	}

	function displayHideBt($state) {
		$this->displayhidebt = $state;
		$this->displayhideallbt = $state;

	}

	function displayHideAllBt($state) {
		$this->displayhideallbt = $state;
	}

	function displayNextBt($state) {
		$this->displaynextbt = $state;
	}

	function displayExemplarBt($state) {
		$this->displayexemplarbt = $state;
	}

	function displayExportBt($state) {
		$this->displayexportbt = $state;
	}

	function displayComment($state) {
		$this->displaycomment= $state;
	}

	function displayCloseIcon($state) {
		$this->displaycloseicon = $state;
	}

	function displayDownloadIcon($state) {
		$this->displaydownloadicon = $state;
	}

	function displayInfoIcon($state) {
		$this->displayinfoicon = $state;
	}

	function displayParticleIcon($state) {
		$this->displayparticleicon = $state;
	}

	function displayFFTIcon($state) {
		$this->displayffticon = $state;
	}

	function displayACEIcon($state) {
		$this->displayaceicon = $state;
	}

	function displayTargetIcon($state) {
		$this->displaytargeticon = $state;
	}

	function displayTarget($state) {
		$state_str = ($state) ? "true" : "false";
		$this->target_st= $state_str;
		$this->bttargetstate = $state_str;
	}

	function displayTagIcon($state) {
		$this->displaytagicon = $state;
	}

	function displayTag($state) {
		$state_str = ($state) ? "true" : "false";
		$this->tag_st= $state_str;
		$this->bttagstate = $state_str;
	}

	function displayPTCLIcon($state) {
		$this->displaynptclicon = $state;
	}

	function displayPTCL($state) {
		$state_str = ($state) ? "true" : "false";
		if ($btnptclstate=$_REQUEST[$this->btnptclmemo])
			return $btnptclstate;
		$this->nptcl_st= $state_str;
		$this->btnptclstate = $state_str;
	}

	function displayScaleIcon($state) {
		$this->displayscaleicon = $state;
	}

	function displayDeqIcon($state) {
		$this->displaydeqicon = $state;
	}

	function displayScale($state) {
		$state_str = ($state) ? "true" : "false";
		$this->scale_st = $state_str;
		$this->btscalestate= $state_str;
	}

	function displayAdjustLink($state) {
		$this->displayadjustlink = $state;
	}

	function displayExportLink($state) {
		$this->displayexportlink = $state;
	}

	function setPreset($preset) {
		$this->preset = $preset;
	}

	function setQuality($quality) {
		$this->quality = $quality;
	}

	function setGradient($gradient) {
		$this->gradient = $gradient;
	}

	function getJavascriptvar() {
		$javascript = ''
			.'var '.$this->name.'size='.$this->size.';'.$this->crlf
			.'var n_img_interval'.$this->name.'=false;'.$this->crlf
			.'var hide_interval'.$this->name.'=false;'.$this->crlf
			.'var n_img_'.$this->name.'= new Image();'.$this->crlf
			.'var jsimagescript'.$this->name.'="'.$this->imagescript.'";'.$this->crlf
			.'var jspresetscript'.$this->name.'="'.$this->presetscript.'";'.$this->crlf
			.'var jsreportscript'.$this->name.'="'.$this->reportscript.'";'.$this->crlf
			.'var jsdwdscript'.$this->name.'="'.$this->dwdscript.'";'.$this->crlf
			.'var jsdwdformat'.$this->name.'="'.$this->jsdwdformat.'";'.$this->crlf
			.'var jshistoscript'.$this->name.'="'.$this->histoscript.'";'.$this->crlf
			.'var jscommentscript'.$this->name.'="'.$this->commentscript.'";'.$this->crlf
			.'var jsvfile'.$this->name.'=1;'.$this->crlf
			.'var jsmin'.$this->name.'="'.$this->minpix.'";'.$this->crlf
			.'var jsmax'.$this->name.'="'.$this->maxpix.'";'.$this->crlf
			.'var jspsize'.$this->name.'="";'.$this->crlf
			.'var jscorrelation'.$this->name.'="";'.$this->crlf
			.'var jscorrelationmin'.$this->name.'="";'.$this->crlf
			.'var jscorrelationmax'.$this->name.'="";'.$this->crlf
			.'var jsfilter'.$this->name.'="'.$this->filter.'";'.$this->crlf
			.'var jsbinning'.$this->name.'="'.$this->binning.'";'.$this->crlf
			.'var jspreset'.$this->name.'="'.$this->preset.'";'.$this->crlf
			.'var jsquality'.$this->name.'="'.$this->quality.'";'.$this->crlf
			.'var jsgradient'.$this->name.'="'.$this->gradient.'";'.$this->crlf
			.'var jsautoscale'.$this->name.'="'.$this->autoscale.'";'.$this->crlf
			.'var jsdisplayfilename'.$this->name.'="'.$this->displayfilename.'";'.$this->crlf
			.'var jsloadjpg'.$this->name.'="'.$this->loadjpg.'";'.$this->crlf
			.'var jsptclsel'.$this->name.'="'.$this->ptclsel.'";'.$this->crlf
			.'var jsaceparam'.$this->name.'="'.$this->jsacepar.'";'.$this->crlf
			.'var jsaceopt'.$this->name.'="'.$this->jsaceopt.'";'.$this->crlf
			.'var jstagparam1'.$this->name.'="'.$this->jstagpar1.'";'.$this->crlf
			.'var jstagparam2'.$this->name.'="'.$this->jstagpar2.'";'.$this->crlf
			.'var jsptclpick'.$this->name.'="'.$this->jsptclpick.'";'.$this->crlf
			.'var jsptclparam'.$this->name.'="";'.$this->crlf
			.'var jsptclcolor'.$this->name.'="";'.$this->crlf
			.'var jsptcllabel'.$this->name.'=false;'.$this->crlf
			.'var '.$this->name.'adjw=false;'.$this->crlf
			.'var js'.$this->name.'done=false;'.$this->crlf
			.'var jslabelgroup'.$this->name.' = document.createElement("optgroup");'.$this->crlf
			.$this->crlf;
		return $javascript;
	}

	function getJavascriptButton() {
		$name = $this->name;
		$javascript = ''.$this->crlf
			.$this->btinfo->getJavascript()
			.$this->btdownload->getJavascript()
			.$this->btscale->getJavascript()
			.$this->bttarget->getJavascript()
			.$this->btparticle->getJavascript()
			.$this->bttag->getJavascript()
			.$this->btnptcl->getJavascript()
			.$this->btfft->getJavascript()
			.$this->btace->getJavascript()
			.$this->btdeq->getJavascript()
			.$this->btclose->getJavascript()
			.$this->crlf;

		$javascript .= 'function '.$name.'btaceaction() { '.$this->crlf
			.'	newfile("'.$this->name.'");'.$this->crlf
			.'}'.$this->crlf;
		$javascript .= 'function '.$name.'btfftaction() { '.$this->crlf
			.'	newfile("'.$this->name.'");'.$this->crlf
			.'	setImageHistogram("'.$this->name.'");'.$this->crlf
			.'}'.$this->crlf;
		$javascript .= 'function '.$name.'btscaleaction(state) { '.$this->crlf
		//	.'	setform("'.$this->btscalememo.'", state);'.$this->crlf
			.'	newfile("'.$this->name.'");'.$this->crlf
			//.'	setImageHistogram("'.$this->name.'");'.$this->crlf
			.'}'.$this->crlf;

		$javascript .= 'function '.$name.'bttargetaction(state) { '.$this->crlf
			.'	setform("'.$this->bttargetmemo.'", state);'.$this->crlf
			.'	setImageHistogram("'.$this->name.'");'.$this->crlf
			.'	updateviews();'.$this->crlf
			.'}'.$this->crlf;

		$javascript .= 'function '.$name.'bttagaction(state) { '.$this->crlf
			.'	newfile("'.$this->name.'");'.$this->crlf
			.'	setform("'.$this->bttagmemo.'", state);'.$this->crlf
			.'}'.$this->crlf;

		$javascript .= 'function '.$name.'btnptclaction(state) { '.$this->crlf
			.'	newfile("'.$this->name.'");'.$this->crlf
			.'	setform("'.$this->btnptclmemo.'", state);'.$this->crlf
			.'}'.$this->crlf;

		$javascript .= 'function '.$name.'btcloseaction(state) { '.$this->crlf
			.'	setform("'.$this->displayname.'", state);'.$this->crlf
			.'	newexp();'.$this->crlf
			.'}'.$this->crlf;

		return $javascript;
	}

	function getJavascriptInit() {
		$javascript = '';
		if ($this->getViewState()=='true')
			$javascript .= $this->btclose->getjstoggle();
		// --- set Scale, targets buttons on 
		if ($this->btfftstate=='true') 
			$javascript .= $this->btfft->getjstoggle();
		if ($this->btacestate=='true') 
			$javascript .= $this->btace->getjstoggle();
		if ($this->btnptclstate=='true') 
			$javascript .= $this->btnptcl->getjstoggle();
		if ($this->bttagstate=='true') 
			$javascript .= $this->bttag->getjstoggle();
		if ($this->bttargetstate=='true') 
			$javascript .= $this->bttarget->getjstoggle();
		if ($this->btscalestate=='true') 
			$javascript .= $this->btscale->getjstoggle();
		return $javascript;
	}

	function getViewState() {
		$this->displayview = ($_POST[$this->displayname]) ? $_POST[$this->displayname] : "true";
		return $this->displayview;
	}

	function selectDataType($type) {
		$this->selecteddatatype = $type;
	}

	function setFrameColor($color) {
		$this->framecolor = ' bgcolor="'.$color.'" ';
	}

	function setMenuColor($color) {
		$this->menucolor = ' bgcolor="'.$color.'" ';
	}

	function setRestriction() {
		if (privilege('data') < 2) {
			$this->displayHideBt(false);
			$this->displayExemplarBt(false);
			#$this->displayACEIcon(false);
			$this->displayDeqIcon(false);
		}
	}

	function setPresetScript($scriptname) {
		$this->presetscript = $scriptname;
	}

	function setHistogramScript($scriptname) {
		$this->histoscript = $scriptname;
	}

	function setDownloadScript($scriptname) {
		$this->dwdscript = $scriptname;
	}

	function setImageReportScript($scriptname) {
		$this->reportscript = $scriptname;
	}

	function setImageScript($scriptname) {
		$this->imagescript= $scriptname;
	}

	function setCommentScript($scriptname) {
		$this->commentscript= $scriptname;
	}

	function display() {
		$iconwidth=15;
		$datatypes = $this->datatypes;
		$displayname = $this->displayname;
		$name = $this->name;
		$imgname = $this->name.'img';
		$prename = $this->name.'pre';
		$prememo = $this->name.'prem';
		$defaultdatatype = ($this->selecteddatatype) ? $this->selecteddatatype : $datatypes[0];
		$defaultpre = ($_POST[$prememo]) ? $_POST[$prememo] : $defaultdatatype;
		$selpre = ($_POST[$prename]) ? $_POST[$prename] : $defaultpre;
		$displayview = $this->getViewState();

		$htmlframe = '
		<input type="hidden" name="'.$displayname.'" value="'.$displayview.'">
		<input type="hidden" name="'.$prename.'m" value="'.$selpre.'"> 
		<input type="hidden" name="'.$this->qualitymemo.'" value="'.$this->quality.'"> 
		<input type="hidden" name="'.$this->gradientmemo.'" value="'.$this->gradient.'"> 
		<input type="hidden" name="'.$this->binningmemo.'" value="'.$this->binning.'"> 
		<input type="hidden" name="'.$this->filtermemo.'" value="'.$this->filter.'">
		<input type="hidden" name="'.$this->autoscalememo.'" value="'.$this->autoscale.'">
		<input type="hidden" name="'.$this->displayfilenamememo.'" value="'.$this->displayfilename.'">
		<input type="hidden" name="'.$this->loadjpgmemo.'" value="'.$this->loadjpg.'">
		<input type="hidden" name="'.$this->minpixmemo.'" value="'.$this->minpix.'">
		<input type="hidden" name="'.$this->maxpixmemo.'" value="'.$this->maxpix.'"> 
		<input type="hidden" name="'.$this->btfftmemo.'" value="'.$this->btfftstate.'"> 
		<input type="hidden" name="'.$this->bttargetmemo.'" value="'.$this->bttargetstate.'"> 
		<input type="hidden" name="'.$this->bttagmemo.'" value="'.$this->bttagstate.'"> 
		<input type="hidden" name="'.$this->btnptclmemo.'" value="'.$this->btnptclstate.'"> 
		<input type="hidden" name="'.$this->btscalememo.'" value="'.$this->btscalestate.'"> 
		<input type="hidden" name="'.$this->ptclselmemo.'" value="0"> ';
		if ($this->ismaster) {
			$htmlframe .= '
		<input type="hidden" name="controlpre" value="'.$prename.'"> 
		<input type="hidden" name="controlview" value="'.$name.'"> 
			';
		}

		$htmlframe .= '
		<table '.$this->framecolor.' border="0" cellspacing="0" cellpadding="1">
		 <tr '.$this->menucolor.'> 
		';
		if ($this->displaycloseicon) {
		$htmlframe .= '
			<td width="15">';
		$htmlframe .= $this->btclose->display();
		$htmlframe .= '
			</td>
		';
		}
		$htmlframe .= '
			<td nowrap="nowrap" >'.$this->title.'</td>
			<td align="right">
			<table border="0" cellspacing="1" cellpadding="0">
			<tr>
		';
		if ($this->newitems) 
		$htmlframe .= '
			<td>'
			.$this->newitems.$this->crlf
			.'
			</td>
		';
		if ($this->displaydeqicon) {
		$htmlframe .= '
			<td width="15">'
			.$this->btdeq->display().$this->crlf
			.'</td> ';
		}
		if ($this->displaydownloadicon) {
		$htmlframe .= '
			<td width="15">'
			.$this->btdownload->display().$this->crlf;
			$htmlframe .= '</td><td width="9">';
			$downimg='<img alt="menu" src="img/menudown1.gif" border="0">';
			$closedownimg='<img alt="close" src="img/close_bt_off.gif" border="0">';
			$dwdmenu = new dropdown($downimg, $name."dwd");
			$dwdmenu->closeval=$closedownimg;
			$dwdmenu->height="";
			$dwdmenu->width="";
			$formats=array("mrc", "tiff", "jpeg");
			foreach ($formats as $format) {
				$sel = ($this->jsdwdformat==$format) ? "checked" : "";
				$dwdformats[]='<input type="radio" name="'.$name.'dwdformat1" id="'.$name.'dwdparam1" value="'.$format.'" '.$sel.' onClick="setFormat(\''.$name.'\', \''.$format.'\')">'.$format;
			}
			$dwdform=join("<br />", $dwdformats);
			$dwdmenu->setContent($dwdform);
			$htmlframe.=$dwdmenu->display();
		}
		if ($this->displayparticleicon)
		$htmlframe .= '
			<td width="15">ICI'
			.$this->btparticle->display().$this->crlf
			.'
	</td>
		';
		if ($this->displayinfoicon) {
		$htmlframe .= '
			<td width="15">'
			.$this->btinfo->display().$this->crlf
			.'</td> ';
		}
		if ($this->displayffticon) {
		$htmlframe .= '
			<td width="15">';
		$htmlframe .= $this->btfft->display();
		$htmlframe .= '
			</td>
		';
		}
		if ($this->displayaceicon) {
			$htmlframe .= '
				<td width="15">';
			$htmlframe .= $this->btace->display();
			$htmlframe .= '</td><td width="9">';
			$downimg='<img alt="menu" src="img/menudown1.gif" border="0">';
			$closedownimg='<img alt="close" src="img/close_bt_off.gif" border="0">';
			$acemenu = new dropdown($downimg, $name."ace");
			$acemenu->closeval=$closedownimg;
			$acemenu->height="";
			$acemenu->width="";
			$aceform=getAceViewerForm($name);
			$acemenu->setContent($aceform);
			$htmlframe.=$acemenu->display();
		$htmlframe .= '
			</td>
		';
		}
		if ($this->displaynptclicon) {
			$htmlframe .= '
				<td width="15">';
			$htmlframe .= $this->btnptcl->display();
			$htmlframe .= '</td><td width="9">';
			$downimg='<img alt="menu" src="img/menudown1.gif" border="0">';
			$closedownimg='<img alt="close" src="img/close_bt_off.gif" border="0">';
			$ptclmenu = new dropdown($downimg, $name."ptcl");
			$ptclmenu->closeval=$closedownimg;
			$ptclmenu->height="";
			$ptclmenu->width="";
			$ptclform='Picks:<br /><select name="'.$name.'ptclrun" id="'.$name.'ptclparam" onchange="getParticleStat(\''.$name.'\');setPtclParam(\''.$name.'\');setPtclLabels(\''.$name.'\');newfile(\''.$name.'\')" >';
			$runIndex = 0;
			if (is_array($this->params['ptclparams'])) {
				foreach ($this->params['ptclparams'] as $index=>$v) {
					if ($_POST[$name.'ptclrun']==$v['DEF_id']) {
						$sel = "selected";
						$runIndex = $index;
					} else {
						$sel = "";
					}
					$ptclform.= "<option value=\"".$v['DEF_id']."\" $sel >".$v['name']."</option>\n"; 
				}
			}
			$ptclform.='</select><br />';
			// Bug: ptclrun is never posted so that $runIndex is always 0
			if (is_array($this->params['ptclparams'][$runIndex]['labels'])) {
				$labels=$this->params['ptclparams'][$runIndex]['labels'];
				$ptclform.='Color by:<br /><select name="'.$name.'ptclcolor" id="'.$name.'ptclcolor" onchange="setPtclParam(\''.$name.'\');newfile(\''.$name.'\')" >';
				foreach (array('d'=>'diameter', 'l'=>'label') as $k=>$paramcolor) {
					$sel = ($_POST[$name.'ptclcolor']==$k) ? "selected" : "";
					$ptclform.= "<option value=\"".$k."\" $sel >".$paramcolor."</option>\n"; 
				}
				$ptclform.='</select><br />';
			}
			$ptclform.='<div id="'.$name.'ptclparamlabels" >';
			$ptclform.='</div>';
###		disable update, validation done by javascript 
###			$ptclform.='<input class="bt1" type="button" value="update" onclick=setPtclParam(\''.$name.'\') />';
			$ptclmenu->setContent($ptclform);
			$htmlframe.=$ptclmenu->display();
		}

		if ($this->displaytagicon) {
			$htmlframe .= '
				<td width="15">';
			$htmlframe .= $this->bttag->display();
			$tag1check = ($this->jstagpar1=="1") ? "checked" : "";
			if (SAMPLE_TRACK) {
				$htmlframe .= '</td><td width="9">';
				$downimg='<img alt="menu" src="img/menudown1.gif" border="0">';
				$closedownimg='<img alt="close" src="img/close_bt_off.gif" border="0">';
				$tagmenu = new dropdown($downimg, $name."tag");
				$tagmenu->closeval=$closedownimg;
				$tagmenu->height="";
				$tagmenu->width="";
				$tag2check = ($this->jstagpar2=="1") ? "checked" : "";

				$tagform='image:<input type="checkbox" name="'.$name.'tagp1" id="'.$name.'tagparam1" '.$tag1check.' >';
				$tagform.='<br />';
				$tagform.='sample:<input type="checkbox" name="'.$name.'tagp2" id="'.$name.'tagparam2" '.$tag2check.' >';
				$tagform.='<br />';
				$tagform.='<input type="button" value="update" onclick=setTagParam(\''.$name.'\') />';
				$tagmenu->setContent($tagform);
				$htmlframe.=$tagmenu->display();
			} else {
				// always on so that it is controled by $this->displaytagicon
				$htmlframe .= '<input type="hidden" name="'.$name.'tagp1" id="'.$name.'tagparam1" value="1" >';
			}
			$htmlframe .= '</td>';
		}

		if ($this->displaytargeticon) {
			$htmlframe .= '
				<td width="15">';
			$htmlframe .= $this->bttarget->display();
			$htmlframe .= '
			</td>';
		}

		if ($this->displayscaleicon) {
			$htmlframe .= '
			<td width="15">';
			$htmlframe .= $this->btscale->display();
			$htmlframe .= '
			</td> ';
		}
		$htmlframe .= '
			</tr>
			</table>
		 </tr>
		 <tr valign=bottom>
			<td colspan="5">	';
		if ($displayview=="true") {
		$htmlframe .='
			<table class="bgcolor0" border="0" cellspacing="0" cellpadding="0">
		';
		// --- begin option table
		if (is_array($datatypes) || $this->displayadjustlink || $this->displaypreset ) {
		$htmlframe .='
			 <tr>
				<td width="'.$this->size.'">
		';
		$htmlframe .='
				<table class="bgcolor0" border="0" cellspacing="3" cellpadding="0">
					<tr valign="center">
						<td>
		';
		if (is_array($datatypes)) {
		$htmlframe .='
				<select name="'.$prename.'" onchange="newdatatype(\''.$name.'\')" > 
		';
		foreach ($datatypes as $v) {
			if ($v==$selpre) $s='selected'; else $s=''; 	
			$htmlframe .= "<option value=\"$v\" $s>$v \n"; 
		}
		$htmlframe .='
					</select>
		';
		}
		$htmlframe .= '
						</td>';
		if ($this->displayexportlink) {
			$export_icon = '<a href="javascript:void(0)" id="export'.$name.'" ><img alt="export" class="setting" src="img/export.png" ></a>';
			if ($this->displayexportbt) {
				$htmlframe .= "<td>$export_icon</td>";
			}
		}
		$htmlframe .= '
						<td valign="center">
				';
		$param = "left=0,top=".($this->viewnb*180).",height=340,width=300";
		$url = "adjust.php?name=$name&displayname=$this->title";
		$htmlframe .= "<div id='".$this->name."imgstat'>";
		$htmlframe .='
			<a href="javascript:popUpAdjust(\''.$url.'\',\''.$name.'\',\''.$param.'\');">
		';
		$settings_icon = '<img alt="setting" class="setting" src="img/settings.png" >';
//		$quality = (is_numeric($this->quality)) ? "jpg".$this->quality : $this->quality;
//		$filter = ($this->filter=='default') ? "no filter": "filter:".$this->filter;
		$minpix = ($this->minpix) ? "&min=".$this->minpix : "";
		$maxpix = ($this->maxpix) ? "&max=".$this->maxpix : "";
		$gradoptions = "h=12&w=100&dm=1".$minpix.$maxpix;
		$gradient = "img/dfe/grad.php?".$gradoptions;
		$imgstatus = "<img alt='gradient' name='".$this->name."imgstatgrad' border='0' src='".$gradient."'> ".$settings_icon;
		$htmlframe .= $imgstatus;
		$htmlframe .='
			</a></div></td>';
		if ($this->ismaster) {
			$htmlframe .= '<td><ul style="padding:0; margin:0">';
			 if ($this->displayhidebt) {
				$htmlframe .= '<li class="list1"><button id="bt_hide" type="button" style="border: 1px solid #bdcebb; font-size: 10px;" '
								.' onclick=\'hide_image()\' ><u><b>h</b></u>ide</button>';
				$htmlframe .= '</li> ';
			}
			if ($this->displayhideallbt) {
				$htmlframe .= ' all<input type="checkbox" id="chk_hide_all"></li>';
			}
			if ($this->displaynextbt) {
				$htmlframe .= '<li class="list1"><button type="button" style="border: 1px solid #bdcebb; font-size: 10px;" '
							.' onclick=\'incIndex(); updateviews()\' ><u><b>n</b></u>ext</button></li>';
			}
			if ($this->displayexemplarbt) {
				$htmlframe .= '<li class="list1"> <button id="bt_ex" type="button" style="border: 1px solid #bdcebb; font-size: 10px;" '
							.' onclick=\'image_is_exemplar();\' ><u><b>e</b></u>xemplar</button></li></ul></td>';
			}
		}

		$htmlframe .= '
					 </tr>
				</table>';
		$htmlframe .= '
				</td>
			 </tr>';
		if ($this->displaypreset) {
			$htmlframe .= '
				 <tr>
					<td>
			<iframe name="'.$this->name.'if" 
	      src="'.$this->presetscript.'"
				frameborder="0" width="'.$this->size.'" height="50"
				marginheight="1" marginwidth="5"
				scrolling="no" ></iframe>
			';
			$htmlframe .= '</td>
				 </tr>
			';
		}
		if ($this->displaycomment) {
			$htmlframe .='<tr>'
			.'<td style="vertical-align: bottom;">'
			.'<iframe name="'.$this->name.'cmt" '
			.'frameborder="0" width="'.$this->size.'" height="30"'
			.'marginheight="0" marginwidth="5"'
			.'scrolling="auto" ></iframe>';
			$htmlframe .= '</td>'
			.'</tr>';
		}
	} // --- end option row

	$htmlframe .= '<tr>
			<td  width="'.$this->size.'">';
	$htmlframe .= '
<div><div id="loadingdiv'.$this->name.'" style="position:absolute; z-index:69; visibility: hidden"><h4> Loading <img alt="progress" src="img/progress_1.gif"></h4></div></div>
		';
		$htmlframe .= '
			<a href="javascript:void(0)" id="'.$this->name.'href">'.
			'<img alt="empty" name="'.$this->name.'img" src="img/empty.gif" border="0" hspace="0" vspace="0" width="'.$this->size.'" ></a>'; 

		$htmlframe .= '
				</td>
			 </tr>
			</table>';
		}
		$htmlframe .= '
			</td>
		 </tr>
		</table> 
		';	
		return $htmlframe;
	}
}

function add_comment_box($name) {
	$score=10;
	$cols=12;
	$rows=4;
	
	$comment_box = '<b>'.$name.'</b> score <select name="'.$name.'_score">';
	for ($i=0; $i<$score; $i++) {
		$comment_box .= "<option>".($i+1)."</option>\n";
	}
	$comment_box .= "</select>";
	$comment_box .= "<br>";
	$comment_box .= '<textarea class="textarea" name="'.$name.'_comment" '
			.'rows="'.$rows.'" cols="'.$cols.'" wrap="virtual"></textarea>';
	$comment_box .= "\n";
	return $comment_box;
}

function viewer_menu($sessionId) {
	$str = '<a class="header" target="summary" href="summary.php?expId='.$sessionId.'">[summary]</a> ';
	if (defined('PROCESSING')) {
		$str.='<a class="header" target="processing" href="processing/index.php?expId='.$sessionId.'">[processing]</a> ';
	}
	$str.='<a class="header" target="make jpgs" href="processing/runJpgMaker.php?expId='.$sessionId.'">[make jpgs]</a>';
	echo $str;
}

function getParticleInfo($sessionId) {
	### used in viewers redirected from project/report.php
	$particle = new particledata();
	$particleruns=$particle->getParticleRunIds($sessionId);
	$data = array();
	$datalabels = array();
	if (!$particleruns) return;
	foreach ($particleruns as $k=>$p) {
		$runId=$p['DEF_id'];
		$particlelabels = $particle->getParticleLabels($runId);
		$labels=array();
		foreach ($particlelabels as $label) {
			$labels[]=$label['label'];
		}
		list($selectionparams)=$particle->getSelectionParams($runId);
		$diam = $selectionparams['diam'];
		$correlationstats=$particle->getStats($runId);
		$correlationstats=array_map('formatnumber2decimal', $correlationstats);
		$correlationstats['diam']=$diam;
		$particleruns[$k]['diam']=$diam;
		$particleruns[$k]['labels']=$labels;
		$data[$runId]=$correlationstats;
		$datalabels[$runId]=$labels;
	}
	$jsdata = array2json($data, "particlestats");
	$jsdata .= array2json($datalabels, "particlelabels");
	return array($jsdata, $particleruns);
}

function getPredefinedVars() {
	### used in xxviewer.php redirected from ,for example, project/report.php
	$projectId = ($_POST['projectId']) ? $_POST['projectId'] : $_GET['projectId'];
	$sessionId = ($_POST['sessionId']) ? $_POST['sessionId'] : $_GET['expId'];
	$imageId = $_GET['imageId'];
	$preset = ($_POST) ? $_POST[$_POST['controlpre']] : $_GET['pre'];
	$runId = '';
	if ($sessionId == $_POST['sessionIdmemo']) {
		$imageId = ($_POST['imageId']) ? $_POST['imageId'] : $imageId;
		$runId = $_POST[$_POST['controlview'].'ptclrun'];
	}
	return array($projectId, $sessionId, $imageId, $preset, $runId);
}

?>
