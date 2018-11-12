<?php
require_once "publicationList.inc";
require_once "html_elements.inc";

class Publication
{
	private $title;
	private $year;
	private $authorList;
	private $journal;
	private $volume;
	private $issue;
	private $pmid;
	private $pmcid;
	private $doi;
	private $logo; //path to logo img ex. "img/eman_logo.png"
	private $pages;
	
	function __construct( $key )
	{
		global $PUBLICATIONS;
		
		// if we got a key that we don't know, fail gracefully and 
		// display the appion reference. We can throw an exception here
		// instead, but that will require more testing, too close to release.
		if ( empty($PUBLICATIONS[$key])) {
			$key = "appion";
		}
		
		$this->setTitle( $PUBLICATIONS[$key]['title'] );
		$this->setYear( $PUBLICATIONS[$key]['year'] );
		$this->setAuthorList( $PUBLICATIONS[$key]['authorlist'] );
		$this->setJournal( $PUBLICATIONS[$key]['journal'] );
		$this->setVolume( $PUBLICATIONS[$key]['volume'] );
		$this->setIssue( $PUBLICATIONS[$key]['issue'] );
		$this->setPmid( $PUBLICATIONS[$key]['pmid'] );
		$this->setPmcid( $PUBLICATIONS[$key]['pmcid'] );
		$this->setDoi( $PUBLICATIONS[$key]['doi'] );
		$this->setLogo( $PUBLICATIONS[$key]['logo'] );
		$this->setPages( $PUBLICATIONS[$key]['pages'] );
	}
	
	// TODO: getters
	public function setTitle( $title ) 			{ $this->title = $title; }
	public function setYear( $year ) 			{ $this->year = $year; }
	public function setAuthorList( $authorList ) { $this->authorList = $authorList; }
	public function setJournal( $journal ) 		{ $this->journal = $journal; }
	public function setVolume( $volume ) 		{ $this->volume = $volume; }
	public function setIssue( $issue ) 			{ $this->issue = $issue; }
	public function setPmid( $pmid ) 			{ $this->pmid = $pmid; }
	public function setPmcid( $pmcid ) 			{ $this->pmcid = $pmcid; }
	public function setDoi( $doi ) 				{ $this->doi = $doi; }
	public function setLogo( $logo ) 			{ $this->logo = $logo; }
	public function setPages( $pages ) 			{ $this->pages = $pages; }
	
	public function getHtmlTable()
	{
		return html_elements::referenceBox( $this->title, $this->year, $this->authorList, 
									$this->journal, $this->volume, $this->issue, $this->pmid, 
									$this->pmcid, $this->doi, $this->logo);
	}

	public function getShortRef()
	{
		return  $this->authorList.'. ('.$this->year.'). <i>"'.$this->title.'"</i> '.$this->journal.' v'.$this->volume.'('.$this->issue.'): pp. '.$this->pages.'.';
	}
}


?>
