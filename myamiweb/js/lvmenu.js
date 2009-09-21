var menu_cookie="menu";
var remember=true; 
var contractall_default=false;
var viewmenu=1;

var menu, titles, submenus, arrows;
var bypixels=3;
var heights = new Array();

var n = navigator.userAgent;
if(/Opera/.test(n) || /MSIE/.test(n)) {
	bypixels = 2;
}


function m_expandall(){
	if (typeof menu!="undefined"){
		for(i=0; i<Math.max(titles.length, submenus.length); i++){
			titles[i].className="title";
			arrows[i].src = "../img/lvmenu/expanded.gif";
			submenus[i].style.display="";
			submenus[i].style.height = heights[i]+"px";
		}
	}
}

function m_collapseall(){
	if (typeof menu!="undefined"){
		for(i=0; i<Math.max(titles.length, submenus.length); i++){
			titles[i].className="titlehidden";
			arrows[i].src = "../img/lvmenu/collapsed.gif";
			submenus[i].style.display="none";
			submenus[i].style.height = 0;
		}
	}
}

function initmenu() {
    menu = getElementsByClassName("lvmenu", "div", document)[0];
    titles = getElementsByClassName("title", "span", menu);
    submenus = getElementsByClassName("submenu", "div", menu);
    arrows = getElementsByClassName("arrow", "img", menu);
    for(i=0; i<Math.max(titles.length, submenus.length); i++) {
        titles[i].onclick = gomenu;
        arrows[i].onclick = gomenu;
        heights[i] = submenus[i].offsetHeight;
        submenus[i].style.height = submenus[i].offsetHeight+"px";
    }
    if(remember) {
				restore()
		} else if (contractall_default) {
				m_collapseall() 
		}
		if (viewmenu==0)
			m_hideall()
}

function restore() {
    if(getcookie(menu_cookie) != null) {
        var cookiestring = getcookie(menu_cookie).split("|");
				viewmenu=cookiestring[1];
        var hidden = cookiestring[0].split(",");
        for(var i in hidden) {
						if (titles[hidden[i]]) {
							titles[hidden[i]].className = "titlehidden";
							submenus[hidden[i]].style.height = "0px";
							submenus[hidden[i]].style.display = "none";
							arrows[hidden[i]].src = "../img/lvmenu/collapsed.gif";
						}
        }
    }
}

function gomenu(e) {
    if (!e)
        var e = window.event;
    var ce = (e.target) ? e.target : e.srcElement;
    var sm;
    for(var i in titles) {
        if(titles[i] == ce || arrows[i] == ce)
            sm = i;
    }
    if(parseInt(submenus[sm].style.height) > parseInt(heights[sm])-2) {
        hidemenu(sm);
    } else if(parseInt(submenus[sm].style.height) < 2) {
        titles[sm].className = "title";
        showmenu(sm);
    }
}

function hidemenu(sm) {
    var nr = submenus[sm].getElementsByTagName("a").length*bypixels;
    submenus[sm].style.height = (parseInt(submenus[sm].style.height)-nr)+"px";
    var to = setTimeout("hidemenu("+sm+")", 30);
    if(parseInt(submenus[sm].style.height) <= nr) {
        clearTimeout(to);
        submenus[sm].style.display = "none";
        submenus[sm].style.height = "0px";
        arrows[sm].src = "../img/lvmenu/collapsed.gif";
        titles[sm].className = "titlehidden";
    }
}

function showmenu(sm) {
    var nr = submenus[sm].getElementsByTagName("a").length*bypixels;
    submenus[sm].style.display = "";
    submenus[sm].style.height = (parseInt(submenus[sm].style.height)+nr)+"px";
    var to = setTimeout("showmenu("+sm+")", 30);
    if(parseInt(submenus[sm].style.height) > (parseInt(heights[sm])-nr)) {
        clearTimeout(to);
        submenus[sm].style.height = heights[sm]+"px";
        arrows[sm].src = "../img/lvmenu/expanded.gif";
    }
        
        
}

function store() {
    var hidden = new Array();
    for(var i in titles) {
        if(titles[i].className == "titlehidden")
            hidden.push(i);
    }
		var cookie_value=hidden.join(",")+"|"+viewmenu
    putcookie(menu_cookie, cookie_value, 30);
}

function getElementsByClassName(strClassName, strTagName, oElm){
    var arrElements = (strTagName == "*" && document.all)? document.all : oElm.getElementsByTagName(strTagName);
    var arrReturnElements = new Array();
    strClassName = strClassName.replace(/\-/g, "\\-");
    var oRegExp = new RegExp("(^|\\s)" + strClassName + "(\\s|$)");
    var oElement;
    for(var i=0; i<arrElements.length; i++){
        oElement = arrElements[i];      
        if(oRegExp.test(oElement.className)){
            arrReturnElements.push(oElement);
        }   
    }
    return (arrReturnElements)
}

function putcookie(c_name,value,expiredays) {
    var exdate=new Date();
    exdate.setDate(exdate.getDate()+expiredays);
    document.cookie = c_name + "=" + escape(value) + ((expiredays==null) ? "" : ";expires="+exdate);
}

function getcookie(c_name) {
    if(document.cookie.length > 0) {
        var c_start = document.cookie.indexOf(c_name + "=");
        if(c_start != -1) {
            c_start = c_start + c_name.length + 1;
            var c_end = document.cookie.indexOf(";",c_start);
            if(c_end == -1)
                c_end = document.cookie.length;
            return unescape(document.cookie.substring(c_start, c_end));
        }
    }
    return null;
}

window.onload = initmenu;
if(remember) window.onunload = store;
