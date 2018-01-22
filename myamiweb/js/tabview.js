/*
 * ANDYK DOCS TAB VIEW
 * Version: 1.0  
 * 2008-08-20
 * based on protoype 1.6.0.1 framework
 * Author: Andreas Koch
 * 
 * files: tabview.css, prototype.js, tabview.js
 */

var UI = {
	Tabview: {
		init: function(parent, options) {
		  /* START: SET DEFAULT OPTIONS */
  		  var defaultoptions = {};
        /* TAB CONTAINER WIDTH */
        defaultoptions.width = '500px';
        
  			/* COLOR CONSTANTS */
  			defaultoptions.activeColorText = 'rgb(255,255,255)'; /* white */
  			defaultoptions.inactiveColorText = 'rgb(0,0,0)'; /* black */
  			defaultoptions.activeColorBackground = "rgb(36,51,86)"; /* dark blue */
  			defaultoptions.inactiveColorBackground = "rgb(255,255,255)"; /* white */
      /* END: SET DEFAULT OPTIONS */ 		  
		
		  /* START: CHECK OPTION PARAMETER */
  		  if (options) {  		  
  		    /* TAB CONTAINER WIDTH */
          if (!options.width) {
            options.width = '500px';
          }
          
          /* Active Tab: Text Color */
          if (!options.activeColorText) {
            options.activeColorText = defaultoptions.activeColorText;
          }
          
          /* Active Tab: Background Color */
          if (!options.activeColorBackground) {
            options.activeColorBackground = defaultoptions.activeColorBackground;
          }
          
          /* Inactive Tab: Text Color */
          if (!options.inactiveColorText) {
            options.inactiveColorText = defaultoptions.inactiveColorText;
          }
          
          /* Inactive Tab: Background Color */
          if (!options.inactiveColorBackground) {
            options.inactiveColorBackground = defaultoptions.inactiveColorBackground;
          }                
        } else {
          /* use default options */
          options = defaultoptions;
        }
      /* END: CHECK OPTION PARAMETER */
      
      /* START: CSS CLASSNAME CONSTANTS */
        options.cssClasses = {};
        options.cssClasses.tabCollection = "tab-collection";
        options.cssClasses.tabContainer = "tab-container";
        options.cssClasses.tab = "tab";
        options.cssClasses.tabHeader = "tab-header";
        options.cssClasses.tabContentContainer = "tab-contentcontainer";
        options.cssClasses.tabContent = "tab-content";
        options.cssClasses.cleanerLeft = "cleaner-left";
      /* END: CSS CLASSNAME CONSTANTS */

      /* START: TRANSFORM UL LIST */
			$(parent).select('.' + options.cssClasses.tabCollection).each(function(tabCollection, i)
			{
				/* GLOBALS */
				var cleanerLeft1 = new Element('div', { className: options.cssClasses.cleanerLeft });
				var cleanerLeft2 = new Element('div', { className: options.cssClasses.cleanerLeft });
				
				/* GET TABS */
				var tabs = $(tabCollection).select('.'+options.cssClasses.tab);

				/* CREATE TAB CONTAINER */
				var tabContainer = new Element('div', { className: options.cssClasses.tabContainer });
				tabContainer.setStyle({ 'width': options.width });
				tabContainer.identify();
				$(tabCollection).wrap(tabContainer);
				
				/* INSERT CLEANER */
				$(tabContainer).insert({ top: cleanerLeft1 });				
				
				/* CREATE TABS */
				tabs.reverse();
				tabs.each(function(tab, x) {		
					x = tabs.length-(x+1);
					var tabHeader =  new Element('div', { className: options.cssClasses.tabHeader });	
					tabHeader.identify();
					tabHeader.writeAttribute({ rel: x });
					tabHeader.update($(tab).title);
					
					/* HIGHLIGHT FIRST TAB */
					if (x==0) {
						$(tabHeader).setStyle({ backgroundColor: options.activeColorBackground, color: options.activeColorText });
					}			
					
					tabHeader.observe('click', function() {		
						var clickedTabIndex = $(this).readAttribute('rel');
						
						/* ADD ONCLICK EVENT: TAB */
						var tabElements = $(tabContainer).select('.' + options.cssClasses.tabHeader);
						tabElements.each(function(clickedTab, z) {
							if ($(clickedTab).readAttribute('rel') === clickedTabIndex) {	
								/* HIGHLIGHT TAB */
								$(clickedTab).setStyle({ backgroundColor: options.activeColorBackground, color: options.activeColorText });
							} else {
								/* REMOVE HIGHTLIGHT */
								$(clickedTab).setStyle({ backgroundColor: options.inactiveColorBackground, color: options.inactiveColorText });
							};				
						});
						
						/* ADD ONCLICK EVENT: CONTENT */
						var contentElements = $(tabContainer).select('.' + options.cssClasses.tabContent);
						contentElements.each(function(content, z) {
							if ($(content).readAttribute('rel') === clickedTabIndex) {	
								/* DISPLAY TAB CONTENT */
								$(content).show();
							} else {
								/* HIDE TAB CONTENT */
								$(content).hide();
							};
						});
					});
					
					$(tabContainer).insert({ top: tabHeader });
				});
				tabs.reverse();
				
				/* CREATE CONTENT CONTAINER */
				var contentContainer = new Element('div', { className: options.cssClasses.tabContentContainer });
				contentContainer.identify();
				$(tabContainer).insert({ bottom: contentContainer });	
				
				/* PREPARE CONTENT ELEMENTS */
				tabs.each(function(tab, x) {
					$(tab).addClassName(options.cssClasses.tabContent);
					$(tab).writeAttribute({ rel: x });
					
					/* DISPLAY ONLY FIRST TAB CONTENT */
					if (x!==0) {
						$(tab).hide();
					}	
				});
				
				/* ADD SOURCE LIST TO CONTENT CONTAINER */
				$(tabCollection).wrap(contentContainer);	
				$(tabCollection).removeClassName(options.cssClasses.tabCollection);
				
				/* INSERT CLEANER */
				$(tabContainer).insert({ bottom: cleanerLeft2 });
			});
			/* END: TRANSFORM UL LIST */
		}
	
	}
};
