<?php
class html_elements {
	function justifiedInputTableRow($doc_str,$doc_label,$post_name,$value_name,$size) {
		$text = "<tr><td>\n";
		$text .= docpop($doc_str, $doc_label);
		$text .= "</td><td align='right'>\n";
		$text .= "<input type='text' name='".$post_name."' value='".$tiltlist."' size='".$size."' style='text-align:center'>\n";
		$text .= "</td></tr>\n";
		return $text;
	}
	
	public static function referenceBox($title, $year, $authorlist, $journal, $volume=false, $issue=false, $pmid=false, $pmcid=false, $doi=false, $logo=false) 
	{
		$refbox = "<br/>";
		$refbox .= "<table class='tablebubble' border='0'><tr><td>\n";
		if ($logo)
		$refbox .= "<img height='80' src='$logo'>";
		$refbox .= "</td><td width='480'>\n";
		$refbox .= "<h4>If you find this software useful please cite:</h4>\n";
		$refbox .= "\n";
		// add period at end of certain fields
		if (substr($title,-1,1)!='.')
		$title.='.';
		if (substr($authorlist,-1,1)!='.')
		$authorlist.='.';
		if (substr($journal,-1,1)!='.')
		$journal.='.';
	
		$refbox .= "<i>\"$title\"</i>&nbsp;($year)\n";
		$refbox .= "$authorlist\n";
		$refbox .= "$journal";
		if ($volume)
		$refbox .= " v$volume";
		if ($issue)
		$refbox .= "<i>($issue)</i>";
		$refbox .= ".&nbsp;\n";
		if ($pmid)
		$refbox .= "PMID:&nbsp;<a href='http://www.ncbi.nlm.nih.gov/pubmed/$pmid'>$pmid</a>&nbsp;\n";
		if ($pmcid)
		$refbox .= "Free text:&nbsp;<a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC$pmcid'>PMC$pmcid</a>&nbsp;\n";
		if ($doi)
		$refbox .= "DOI:&nbsp;<a href='http://dx.doi.org/$doi'>$doi</a>&nbsp;\n";
		$refbox .= "\n";
		$refbox .= "</td></tr></table><br/>\n";
		return ($refbox);
		//echo referenceBox(title, year, authorlist, journal, volume, issue, pmid, pmc, doi, logo);
	}	
}
?>
