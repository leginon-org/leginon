<?

class notedata {

	var $file_path = 'notes/';
	var $image_path = 'img/';
	var $isadmin = false;

	function notedata($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB);
	}

	function setPrivilege($privilege) {
		if ($privilege==2)
			$this->isadmin=true;
	}

	function getNotes($projectId, $complete=false) {
		$notes=array();
		$noteformat = ($complete) ? 'note' :
			"concat(substring_index(left(note, 110),'\n',2),' ...') as `note`";
		$q='select noteId, timestamp, '
		   .'date_format(timestamp, "%d-%b-%Y") as `date`, '
		   .$noteformat
		   .' from notes '
		   .'where projectId="'.$projectId.'" '
		   .'order by timestamp desc';
		$RnoteInfo = $this->mysql->SQLQuery($q);
		while ($row = mysql_fetch_array($RnoteInfo))
			$notes[]=array(
			0 => $row[noteId], 'noteId' => $row[noteId],
			1 => $row[timestamp], 'timestamp' => $row[timestamp],
			2 => $row[date], 'date' => $row[date],
			3 => $row[note], 'note' => $row[note] );
		return $notes;
	}

	function getNote($noteId, $complete=false) {
		$note=array();
		$noteformat = ($complete) ? 'note' :
			"concat(substring_index(left(note, 110),'\n',4),' ...') as `note`";
		$q='select noteId, timestamp, '
		   .'date_format(timestamp, "%d-%b-%Y") as `date`, '
		   .$noteformat
		   .' from notes '
		   .'where noteId="'.$noteId.'" '
		   .'order by timestamp desc';
		$RnoteInfo = $this->mysql->SQLQuery($q);
		$note = mysql_fetch_array($RnoteInfo);
		return $note;
	}

	function getFiles($projectId) {
		$files=array();
		$q='select fileId, timestamp, '
		   .'date_format(timestamp, "%d-%b-%Y") as `date`, '
		   .'filename, filetype '
		   .'from files '
		   .'where projectId="'.$projectId.'" '
		   .'order by timestamp desc';
		$RfileInfo = $this->mysql->SQLQuery($q);
		while ($row = mysql_fetch_array($RfileInfo))
			$files[]=array(
			0 => $row[fileId], 'fileId' => $row[fileId],
			1 => $row[timestamp], 'timestamp' => $row[timestamp], 
			2 => $row[date], 'date' => $row[date], 
			3 => $row[filename], 'filename' => $row[filename],
			5 => $row[filetype], 'filetype' => $row[filetype] );
		return $files;
	}

	function getFile($fileId) {
		$file=array();
		$q='select fileId, timestamp, '
		   .'date_format(timestamp, "%d-%b-%Y") as `date`, '
		   .'filename, filetype, projectId '
		   .'from files '
		   .'where fileId="'.$fileId.'" '
		   .'order by timestamp desc';
		$RfileInfo = $this->mysql->SQLQuery($q);
		$file = mysql_fetch_array($RfileInfo);
		return $file;
	}

	function getFilePath($projectId) {
		return $this->file_path.'project_note_'.$projectId.'/';
	}

	function setRedirection($redirect) {
		$this->redirect = $redirect;
	}

	function deleteNote($noteId) {
		if (!$noteId) return false;
		$q[]='delete from notes where noteId="'.$noteId.'"';
		$this->mysql->SQLQueries($q);
		return true;
	}

	function deleteFile($fileId) {
		if (!$fileId) return false;
		$fileinfo = $this->getFile($fileId);
		$projdir = $this->getFilePath($fileinfo[projectId]);
		$filename = $projdir.stripslashes($fileinfo[filename]);
		$q[]='delete from files where fileId="'.$fileId.'"';
		$this->mysql->SQLQueries($q);
		if (file_exists($filename))
			unlink($filename);
		return true;
	}

	function checkIfNoteExists($note) {
		if (!$note) return false;
		$q=' select noteId from notes where note="'.$note.'"';
		$RnoteInfo = $this->mysql->SQLQuery($q);
		$noteInfo = mysql_fetch_array($RnoteInfo);
		return $noteInfo[noteId];
	}

	function checkIfNoteExistsbyId($noteId) {
		if (!$noteId) return false;
		$q=' select noteId from notes where noteId="'.$noteId.'"';
		$RnoteInfo = $this->mysql->SQLQuery($q);
		$noteInfo = mysql_fetch_array($RnoteInfo);
		return $noteInfo[noteId];
	}

	function checkIfFileExists($projectId, $filename) {
		if (!$filename) return false;
		$q=' select fileId from files where projectId="'.$projectId.'" and filename="'.$filename.'"';
		$RfileInfo = $this->mysql->SQLQuery($q);
		$fileInfo = mysql_fetch_array($RfileInfo);
		return $fileInfo[fileId];
	}

	function checkIfFileExistsbyId($fileId) {
		if (!$fileId) return false;
		$q=' select fileId from files where fileId="'.$fileId.'"';
		$RfileInfo = $this->mysql->SQLQuery($q);
		$fileInfo = mysql_fetch_array($RfileInfo);
		return $fileInfo[fileId];
	}

	function addNote($projectId, $note="") {
		if (!get_magic_quotes_gpc())
		    $note= addslashes($note);
		if ($checknoteId=$this->checkIfNoteExists($note))
			return false;

		$q = "insert into notes "
			  ."(projectId, note) "
			  ."values "
			  ."('".$projectId."', "
			  ." '".$note."') ";
		$noteId =  $this->mysql->SQLQuery($q, true);
		return $noteId;
	}

	function addFile($projectId, $tmpfile, $filename="", $filetype="") {
		if (!get_magic_quotes_gpc()) {
		    $filename = addslashes($filename);
		    $filetype = addslashes($filetype);
		}

		$projdir = $this->getFilePath($projectId);
		if (!is_dir($projdir))
			mkdir($projdir, 0755);
		 

		if ($checkfileId=$this->checkIfFileExists($projectId,$filename))
			return "exist";

		$newfile = $projdir.stripslashes($filename);
		if (is_file($new_file))
			return "exist";

		if (!move_uploaded_file($tmpfile, $newfile))
			return false;

		$q = "insert into files "
			  ."(projectId, filename, filetype) "
			  ."values "
			  ."('".$projectId."', "
		  	  ." '".$filename."', "
			  ." '".$filetype."') ";
		$fileId =  $this->mysql->SQLQuery($q, true);
		return $fileId;

	}

	function displayAll($projectId) {
		$notes = $this->getNotes($projectId);
		foreach($notes as $note)
			$this->displayNote($note);

		$files = $this->getFiles($projectId);
		foreach($files as $file)
			$this->displayFile($file);
	}

	function displayNotes($projectId) {
		$redirect = $this->redirect;
		$redirect_str = (empty($redirect)) ? "" : 'red='.$redirect.'&';
		$notes = $this->getNotes($projectId);
		$html_str = '<div><table class="tableborder" border="1">';
		
		foreach($notes as $note) {
			$html_str .='<tr valign="top">'
				  .'<td width="235">'
				  .nl2br(htmlentities($note[note]))
				  .'</td>'
				  .'<td>'
				  .$note[date]
				  .'</td>'
				  .'<td>'
				  .'<a target="pdb_note" href="viewnote.php?id='
				  .$note[noteId].'">'
				  .'<img border="0" src="'
				  .$this->image_path.'btn-file-view.gif"></a>'
				  .'</td>';
			if ($this->isadmin) {
				$html_str .= '<td>'
					.'<a href="deletenote.php?'.$redirect_str.'id='
					.$note[noteId].'"><img src="'
					.$this->image_path.'btn-trash.png" border="0"></a>'
					.'</td>';
			}
			$html_str .= '</tr>';
		}

		$html_str .= '</table></div>';
		return $html_str;
	}

	function displayFiles($projectId) {
		$redirect = $this->redirect;
		$redirect_str = (empty($redirect)) ? "" : 'red='.$redirect.'&';
		$files = $this->getFiles($projectId);
		$path = $this->getFilePath($projectId);
		$html_str = '<div><table class="tableborder" border="1">';
		
		foreach($files as $file) {
			$html_str .='<tr>'
				  .'<td>'
				  .$file[filename]
				  .'</td>'
				  .'<td>'
				  .$file[date]
				  .'</td>';
			if ($this->isImage($path.$file[filename])) {
				$html_str .='<td>'
					  .'<a href="getfilethumb.php?f='
					  .$file[fileId].'">'
					  .'<img border="0" src="getfilethumb.php?w=40&f='
					  .$file[fileId].'">'
					  .'</a>'
					  .'</td>';
			} else {
				$html_str .='<td>'
					  .'<img src="'
					  .$this->image_path
					  .$this->getFileIcon($file[filetype])
					  .'" border="0">'
					  .'</td>';
			}
			$html_str .='<td>'
				  .'<a href="downloadfile.php?id='
				  .$file[fileId].'"><img src="'
				  .$this->image_path.'btn-download.gif" border="0"></a>'
				  .'</td>'
				  .'</tr>';
		}

		$html_str .= '</table></div>';
		return $html_str;
	}
		
	function displayNote($noteId) {
	$note = $this->getNote($noteId, true);
	echo '
	 <div class="note">
	  <strong>'.$note['date'].'</strong><br />
	   '.$date.'
	  <div class="text">
		'.nl2br(htmlentities(stripslashes($note[note]))).'
	  </div>
	 </div>
	';
	}

	function displayFile($file) {
	echo '
	 <div class="file">
	  <strong>'.$file[filename].'</strong><br />
	   '.$date.'
	  <div class="text">
		'.$file[filetype].'
	  </div>
	  <div class="text">
		'.$file[date].'
	  </div>
	 </div>
	';
	}

	function getFileIcon($filetype) {
		$icon='btn-file.gif';
		if (ereg('application.*pdf',$filetype))
				$icon='btn-pdf.gif';
		else if (ereg('application.*powerpoint|ppt',$filetype))
				$icon='btn-ppt.gif';
		else if (ereg('application.*msword|doc',$filetype))
				$icon='btn-word.gif';
		else if (ereg('application.*excel|xls',$filetype))
				$icon='btn-xls.gif';
		else
				$icon='btn-file.gif';
		return $icon;
	}

	function isImage($filename) {	
		$isimage=false;
		if ($source = @imagecreatefromstring(file_get_contents($filename))) {
			$isimage=true;
			imagedestroy($source);
		}
		return $isimage;
	}


}
?>
