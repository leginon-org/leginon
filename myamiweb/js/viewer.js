/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

var autoscale=false
var pl_interval = false
var lastoptions = new Array()

if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest()
        xmlhttp.overrideMimeType('text/xml')
} else if (window.ActiveXObject) {
        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP")
}
String.prototype.trim = function() { return this.replace(/^\s+|\s+$/, ''); }

function image_is_examplar(view) {
	if (list = eval("document.viewerform."+view+"pre"))
		selpreset=list.options[list.selectedIndex].value
	displaydebug("a:"+view+" "+selpreset)
	var jsUsername=null
	if (obj=document.viewerform.imageId) {
		jsindex = obj.selectedIndex
		jsimgId = obj.options[jsindex].value
		var url = 'updateimagelist.php?username='+jsUsername+'&imageId='+jsimgId+'&sessionId='+jsSessionId+'&p='+selpreset+'&s=ex'
		xmlhttp.open('GET', url, true)
		xmlhttp.onreadystatechange = function() {
			if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
				// --- check
				dbresult = xmlhttp.responseText
				displaydebug("c:"+jsindex+" l:"+obj.length+": dbe:"+dbresult.length+"  "+dbresult)
			}
		}
	xmlhttp.send(null)
	}
}

function update_image_list(view) {
	if (list = eval("document.viewerform."+view+"pre"))
		selpreset=list.options[list.selectedIndex].value
	displaydebug("a:"+view+" "+selpreset)
	var jsUsername=null
	if (obj=document.viewerform.imageId) {
		jsindex = obj.selectedIndex
		jsimgId = obj.options[jsindex].value
		var url = 'updateimagelist.php?username='+jsUsername+'&imageId='+jsimgId+'&sessionId='+jsSessionId+'&p='+selpreset+'&ac=h'
		xmlhttp.open('GET', url, true)
		xmlhttp.onreadystatechange = function() {
			if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
				// --- check
				dbresult = xmlhttp.responseText
				displaydebug("c:"+jsindex+" l:"+obj.length+": dbe:"+dbresult.length+"  "+dbresult)
				// --- set index to next image
				if (jsindex<obj.length && dbresult=="1") {
					obj.remove(jsindex)
					if (jsindex<obj.length)
						obj.options[jsindex].selected=true
					else if (obj.length-1>0)
						obj.options[obj.length-1].selected=true
					updateviews()
				}
			}
		}
	xmlhttp.send(null)
	}
}

function setproject(id) {
	if (obj=document.viewerform.projectId) {
		for (var i in obj.options) {
			if (obj.options[i].value == id) {
				obj.options[i].selected=true
				break
			}
		}
		newexp()
	}
}

function setevents()
{
	if (obj=document.viewerform.imageId) {
	     obj.onkeyup   = checkevents
	     obj.onkeydown = checkevents
	     obj.onchange  = checkevents
	}
} 

function checkevents(e)
{
	var code
	if (!e) var e = window.event
	if (e.keyCode) code = e.keyCode
	else if (e.which) code = e.which
	if (code == key_down_unicode || code == key_up_unicode)  {
		if (e.type == eventdown) {
			keydown=true
			stopInterval()
		} else if (e.type == eventup) {
			startInterval()
			keydown=false
		}
	} else if (e.type == eventchange && !keydown) {
			updateviews()
	}
}

function getKey(e)
{
  var code
  if (!e) var e = window.event
  if (e.keyCode) code = e.keyCode
  else if (e.which) code = e.which
  var character = String.fromCharCode(code)

	switch (character) {
		case 'N':
			incIndex()
			updateviews()
			break
		case 'H':
			update_image_list()
			break
		case 'E':
			image_is_examplar()
			incIndex()
			updateviews()
			break
  }
}

function dwdpre(preset) {
	alert(preset)
	"http://stratocaster.scripps.edu/dbemd/download.php?id=574467&preset=all"
}

function getImageAutoScale(view) {
	var url = 'getimagestat.php?id='+jsimgId
	alert(url)
	xmlhttp.open('GET', url, true)
	xmlhttp.onreadystatechange = function() {
		if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
		var xmlDocument = xmlhttp.responseXML
		var minval = parseFloat(xmlDocument.getElementsByTagName('min').item(0).firstChild.data)
		var maxval = parseFloat(xmlDocument.getElementsByTagName('max').item(0).firstChild.data)
		var meanval = parseFloat(xmlDocument.getElementsByTagName('mean').item(0).firstChild.data)
		var stdevval = parseFloat(xmlDocument.getElementsByTagName('stdev').item(0).firstChild.data)
		var minval = ((meanval - 3*stdevval)-minval)*255/(maxval-minval)
		var maxval = ((meanval + 3*stdevval)-minval)*255/(maxval-minval)
		setminmax(view, minval, maxval)
		}
	}
	xmlhttp.send(null)
}

function startInterval()
{
	begin = new Date()
	interval = window.setInterval("trigger()",10)
}

function stopInterval()
{
    window.clearInterval (interval)
    interval=""
}

function trigger()
{
	end = new Date()
	diff = end-begin
	// --- if key released at least for 150ms
	// --- then triggered his action 
	if (diff > 150) {
		stopInterval()
		// --- action
		updateviews()
	}
	
}

function startPlayback(refreshtime) {
	if (refreshtime) {
		stopPlayback()
		pl_interval = window.setInterval("playback()", refreshtime)
	}
}

function rstartPlayback(refreshtime) {
	if (refreshtime) {
		stopPlayback()
		pl_interval = window.setInterval("rplayback()", refreshtime)
	}
}

function stopPlayback() {
	window.clearInterval (pl_interval)
	pl_interval = ""
}

function playback() {
	if (isImageLoaded(mainview)) {
		incIndex()
		if (getIndex()==document.viewerform.imageId.length-1) {
			stopPlayback()
		}
		updateviews()
	}
}

function rplayback() {
	if (isImageLoaded(mainview)) {
		decIndex()
		if (!getIndex()) {
			stopPlayback()
		}
		updateviews()
	}
}

function setprogressbar(view) {
	loadingdiv = false
	if (loadingdivstyle = document.getElementById("loadingdiv"+view).style) {
		loadingdiv = true
	}
	if (isImageLoaded(view)) {
		eval("window.clearInterval(n_img_interval"+view+");")
		eval("n_img_interval"+view+"='';")
		if (loadingdiv) {
			loadingdivstyle.visibility = 'hidden'
		}
	} else {
		if (loadingdiv) {
			loadingdivstyle.visibility = 'visible'
		}
	}
}

function loadImage(view) {
	if (loadingdivstyle = document.getElementById("loadingdiv"+view).style) {
		loadingdiv = true
	}
	if (img = document.images[eval("\"" +view+ "img\"")]) {
		n_img = eval("n_img_"+view)
		eval("n_img_interval"+view+" = window.setInterval(\"setprogressbar('"+view+"')\", 500)")
		img.src=n_img.src;	
	}
}

function setimgId() {
	if (obj=document.viewerform.imageId) {
	if (!obj.length)
		return
	jsindex = obj.selectedIndex; 
	if (jsindex < 0) {
		jsindex=0; 
		obj.options[0].selected=true; 
	} 
	jsimgId = obj.options[jsindex].value; 
	}
}

function newexp() {
    window.document.viewerform.submit(); 
    return true
}

function getMainView() {
	mainview = 'v1'
	if (controlview=eval("document.viewerform.controlview")) {
		mainview=controlview.value
	}
	return mainview
}

function getviewindex(name) {
	index=0
	for (var i in jsviews) {
		if (jsviews[i] == name) {
			index=i
			break
		}
	}
	return index
}

function addComment() {
	name = document.viewerform.name.value
	comment = document.viewerform.comment.value
	url = "addcomment.php?sessionId="+jsSessionId+"&imageId="+jsimgId+"&name="+escape(name)+"&comment="+escape(comment)
	if (img = document.images[eval("\"commentimg\"")]) 
		img.src = url

	if (commentdivstyle = document.getElementById("commentdiv").style) {
		commentdivstyle.visibility = 'visible'
		setTimeout("commentdivstyle.visibility = 'hidden'; img.src = 'addcomment.php'", 1500)
	}
}

function newdatatype(view) {
	if (listcontrol = eval("document.viewerform.controlpre.value"))
		if (listcontrol==view+"pre") {
			newexp()
			return
		}
	else
		newfile(view)
}

function newfile(view){
	jssize = eval(view+"size")
	jsvfile = eval("jsvfile"+view)
	selpreset = eval("jspreset"+view)
	if (cbinning = eval("jsbinning"+view)) binning="&binning="+cbinning; else binning=""
	jsimagescriptcur = eval("jsimagescript"+view)
	jspresetscriptcur = eval("jspresetscript"+view)
	jscommentscriptcur = eval("jscommentscript"+view)
	vid = getviewindex(view)
	
	if (list = eval("document.viewerform."+view+"pre"))
		selpreset=list.options[list.selectedIndex].value

	if (prem = eval("document.viewerform."+view+"prem"))
		if (list)
			prem.value = selpreset

	eval("jspreset"+view+"='"+selpreset+"'")

	setImageStatus(view)

	if (eval(view+"fft_bt_st")) fft="&fft=1"; else fft=""
	if (eval(view+"ace_bt_st")) {
		jsimagescriptcur="getaceimg.php"
		jspresetscriptcur="getacepreset.php"
	} else { 
		jsimagescriptcur="getimg.php"
		jspresetscriptcur="getpreset.php"
	}
	jscommentscriptcur = "getcomment.php"
	pselp = (cpselpar = eval("jsptclpick"+view)) ? "&psel="+cpselpar : ""
	ag = (cacepar = eval("jsaceparam"+view)) ? "&g="+cacepar : ""
	sb = (eval(view+"scale_bt_st")) ? "&sb=1" : ""
	tg = (eval(view+"target_bt_st")) ? "&tg=1" : ""
	displayfilename = (eval(view+"tag_bt_st")) ? "&df=1" : ""
	nptcl = (eval(view+"nptcl_bt_st")) ? "&nptcl=1" : ""
	np = (cmin = eval("jsmin"+view)) ? "&np="+cmin : ""
	if (cmax = eval("jsmax"+view)) xp="&xp="+cmax; else xp=""
	if (cfilter = eval("jsfilter"+view)) flt="&flt="+cfilter; else flt=""
	if (cbinning = eval("jsbinning"+view)) binning="&binning="+cbinning; else binning=""
	if (cquality = eval("jsquality"+view)) quality="&t="+cquality; else quality=""
	if (ccolormap= eval("jscolormap"+view)) colormap="&colormap="+ccolormap; else colormap=""
	if (cautoscale= eval("jsautoscale"+view)) autoscale="&autoscale="+cautoscale; else autoscale=""
	if (cloadjpg= eval("jsloadjpg"+view)) loadjpg="&lj="+cloadjpg; else loadjpg=""
	if (cptclsel = eval("jsptclsel"+view)) ptclsel="&psel="+escape(cptclsel); else ptclsel=""

	options = "imgsc="+jsimagescriptcur+
		"&preset="+selpreset+
		"&session="+jsSessionId+
		"&id="+jsimgId+
		"&s="+jssize+quality+tg+sb+fft+np+xp+flt+binning+colormap+autoscale+displayfilename+loadjpg+pselp+nptcl+ag

	if (options == lastoptions[vid])
		return

	ni = jsimagescriptcur+"?"+options
	nlink = "javascript:popUpMap('map.php?"+options+"')"
	ninfolink = "imgreport.php?id="+jsimgId+"&preset="+selpreset
	ndeqlink = "javascript:popUpW('removequeue.php?id="+jsimgId+"&preset="+selpreset+"')"
	ndownloadlink = "download.php?id="+jsimgId+"&preset="+selpreset+fft
	nexportlink = "getfilenames.php?sessionId="+jsSessionId+"&pre="+selpreset

	if (img = document.images[eval("\"" +view+ "img\"")]) {
		n = img.name
		n_img = eval("n_img_"+view)
		n_img.name="n"+n
		n_img.src = ni
		loadImage(view)
	}
	if (link = document.getElementById(view+"href"))
		link.href = nlink
	if (infolink = document.getElementById("info"+view+"_bthref"))
		infolink.href = ninfolink
	if (deqlink = document.getElementById("deq"+view+"_bthref"))
		deqlink.href = ndeqlink
	if (downloadlink = document.getElementById("download"+view+"_bthref"))
		downloadlink.href = ndownloadlink
	if (exportlink = document.getElementById("export"+view))
		exportlink.href = nexportlink

	if (cif=eval("this."+view+"if")) {
		iflink = jspresetscriptcur+"?vf="+jsvfile+"&id="+jsimgId+"&preset="+selpreset
		cif.document.location.replace(iflink)
	}
	if (cmt=eval("this."+view+"cmt")) {
		cmtlink = jscommentscriptcur+"?id="+jsimgId+"&preset="+selpreset
		cmt.document.location.replace(cmtlink)
	}

	lastoptions[vid] = options
}

function setAceParam(view) {
	if (param = document.getElementById(view+"aceparam")) {
		vf = param.options[param.selectedIndex].value
		eval("jsaceparam"+view+"="+vf)
		newfile(view)
	}
}

function setPtclParam(view) {
	if (param = document.getElementById(view+"ptclparam")) {
		vf = param.options[param.selectedIndex].value
		eval("jsptclpick"+view+"="+vf)
		newfile(view)
	}
}

function toggleButton(imagename, name) {
	state = toggleimage(imagename, name)
	if (m = eval("document.viewerform."+imagename+"_st")) {
		m.value=state
	}
	return state
}

function setform(input, value) {
	if (m = eval("document.viewerform."+input)) {
		m.value=value
		return true
	}
	return false
}

function isImageLoaded(view) {
	if (img = document.images[eval("\"" +view+ "img\"")]) {
		if (n_img.complete){
			eval("n_img_"+view+"=new Image()")
			return true
		}
	}
	return false
}

function setImageStatus(viewname) {
	if (ccolormap= eval("jscolormap"+viewname)) colormap="&colormap="+ccolormap; else colormap=""
	if (cmin = eval("jsmin"+viewname)) np="&min="+cmin; else np=""
	if (cmax = eval("jsmax"+viewname)) xp="&max="+cmax; else xp=""
	options = np+xp+colormap
	if (img = document.images[eval("\"" +viewname+ "imgstatgrad\"")]) 
		img.src = 'img/dfe/grad.php?h=10&w=100&dm=1'+options
	filter = eval("jsfilter"+viewname)
	binning = eval("jsbinning"+viewname)
	quality = eval("jsquality"+viewname)
	quality = (isNaN(quality)) ? quality : "jpg"+quality
	newstatus = " filter:"+filter+" bin:"+binning+" "+quality
}

function setImageHistogram(viewname) {
	if (w=eval(viewname+"adjw")) {
		jssize = eval(viewname+"size")
		selpreset = eval("jspreset"+viewname)
		if (list = eval("document.viewerform."+viewname+"pre"))
			selpreset=list.options[list.selectedIndex].value
		if (eval(viewname+"fft_bt_st")) fft="&fft=1"; else fft=""
		if (cfilter = eval("jsfilter"+viewname)) flt="&flt="+cfilter; else flt=""
		if (ccolormap= eval("jscolormap"+viewname)) colormap="&colormap="+ccolormap; else colormap=""
		if (cmin = eval("jsmin"+viewname)) np="&np="+cmin; else np=""
		if (cmax = eval("jsmax"+viewname)) xp="&xp="+cmax; else xp=""
		if (cbinning = eval("jsbinning"+viewname)) binning="&binning="+cbinning; else binning=""

		options = "preset="+selpreset+
			"&id="+jsimgId+
			"&s="+jssize+quality+np+xp+flt+binning+colormap+fft

		if (!w.closed) {
			if (histo = w.document.imghisto)
				histo.src="imagehistogram.php?tf=1&"+options
		}
	}
}

function setminmax(viewname, min,max) {
	eval("jsmin"+viewname+"="+min)
	eval("jsmax"+viewname+"="+max)
	if (m = eval("document.viewerform."+viewname+"minpix")) {
		m.value=min
	}
	if (x = eval("document.viewerform."+viewname+"maxpix")) {
		x.value=max
	}
}

function getminmax(viewname, min,max) {
	if (m = eval("document.viewerform."+viewname+"minpix")) {
		min=m.value
	}
	if (x = eval("document.viewerform."+viewname+"maxpix")) {
		max=x.value
	}
	return Array(min,max)
}

function setcolormap(viewname, colormap) {
	eval("jscolormap"+viewname+"="+colormap)
	if (cm = eval("document.viewerform."+viewname+"cm")) {
		cm.value=colormap
	}
}

function setquality(viewname, quality) {
	eval('jsquality'+viewname+'="'+quality+'"')
	if (q = eval("document.viewerform."+viewname+"q")) {
		q.value=quality
	}
}

function setParticleSelection(viewname, selection) {
	eval('jsptclsel'+viewname+'="'+selection+'"')
	if (q = eval("document.viewerform."+viewname+"psel")) {
		q.value=selection
	}
}

function setfilter(viewname, filter) {
	eval("jsfilter"+viewname+"='"+filter+"'")
	if (f = eval("document.viewerform."+viewname+"f")) {
		f.value=filter
	}
}

function setbinning(viewname, binning) {
	eval("jsbinning"+viewname+"='"+binning+"'")
	if (b = eval("document.viewerform."+viewname+"b")) {
		b.value=binning
	}
}

function setautoscale(viewname, state) {
	eval("jsautoscale"+viewname+"='"+state+"'")
	if (b = eval("document.viewerform."+viewname+"autos")) {
		b.value=state
	}
}

function setloadfromjpg(viewname, state) {
	eval("jsloadjpg"+viewname+"='"+state+"'")
	if (b = eval("document.viewerform."+viewname+"loadjpg")) {
		b.value=state
	}
}

function setdisplayfilename(viewname, state) {
	eval("jsdisplayfilename"+viewname+"='"+state+"'")
	if (b = eval("document.viewerform."+viewname+"df")) {
		b.value=state
	}
}

function popUpMap(URL) {
	window.open(URL, "map"+window.name, "left=0,top=0,height=512,width=512,toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=1,alwaysRaised=yes")
}

function popUpW(URL) {
	window.open(URL, "deq", "left=0,top=0,height=512,width=300,toolbar=0,scrollbars=1,location=0,statusbar=0,menubar=0,resizable=1,alwaysRaised=yes")
}


function popUpAdjust(URL, view, param){
	min = eval("jsmin"+view)
	max = eval("jsmax"+view)
	filter = eval("jsfilter"+view)
	binning = eval("jsbinning"+view)
	quality = eval("jsquality"+view)
	colormap = eval("jscolormap"+view)
	autoscale = eval("jsautoscale"+view)
	displayfilename = eval("jsdisplayfilename"+view)
	loadjpg= eval("jsloadjpg"+view)
	min = (min) ? "&pmin="+min : ""
	max = (max) ? "&pmax="+max : ""
	filter = (filter) ? "&filter="+filter : ""
	binning = (binning) ? "&binning="+binning : ""
	quality = (quality) ? "&t="+quality : ""
	colormap= (colormap) ? "&colormap="+colormap : ""
	autoscale= (autoscale) ? "&autoscale="+autoscale : ""
	displayfilename= (displayfilename) ? "&df="+displayfilename : ""
	loadjpg= (loadjpg) ? "&lj="+loadjpg : ""
	param = (param) ? param : "left=0,top=0,height=200,width=370"
	eval (view+"adjw"+" = window.open('"+URL+min+max+filter+binning+quality+colormap+autoscale+displayfilename+loadjpg+"', '"+view+"adj', '"+param+"', 'toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes');")
}

function popUpPtcl(URL, view, param) {
	psel = eval('jsptclsel'+view)
	psel = (psel) ? "&psel="+psel : ""
	s = "&session="+jsSessionId
	param = (param) ? param : "left=0,top=0,height=170,width=370"
	eval (view+"adjw"+" = window.open('"+URL+s+psel+"', '"+view+"ptcl', '"+param+"', 'toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=0,alwaysRaised=yes');")
}

function getIndex() {
	cindex = 0
	if (document.viewerform.imageId.length !=0) {
		for (var i = 0; i < document.viewerform.imageId.length; i++) {
			if (document.viewerform.imageId.options[i].selected == true) {
				cindex=i  
			} 
    }
	}
	return cindex
}

function incIndex(){
	if (document.viewerform.imageId.length !=0) {
		index = getIndex()
		if (index == document.viewerform.imageId.length - 1) {
			index = index-1
		}	
		document.viewerform.imageId.options[index+1].selected=true
	}
}

function decIndex(){
	if (document.viewerform.imageId.length !=0) {
		index = getIndex()
		if (index == 0) {
			index = index+1
		}	
		document.viewerform.imageId.options[(index-1)].selected=true
	}
}

function displaydebug(string) {
	if (cur = document.viewerform.debug)
		document.viewerform.debug.value= cur.value+"\n"+string
}

function bsSliderChange1(sliderObj, val, newPos){ 
  jsminpix = val
  updateGradient()
}

function bsSliderChange2(sliderObj, val, newPos){ 
  jsmaxpix = val
  updateGradient()
}

function updateGradient() {
	document.getElementById('gradientDiv').style.background = 'url('+jsbaseurl+gradient+'?colormap='+jscolormap+'&min='+jsminpix+'&max='+jsmaxpix+'&gmin='+jsmingradpix+'&gmax='+jsmaxgradpix+')'; 
}

function cle(val) {
  eval(val)
}
