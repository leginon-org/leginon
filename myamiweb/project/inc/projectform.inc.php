<form action="<?=$_SERVER['REQUEST_URI'] ?>" method="POST">
  <input type="hidden" name="projectId" value="<?=$projectId?>">
  <table border="0" cellspacing="0" cellpadding="1" >
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2" >Name
          </font><font color=red>*</font>&nbsp;:&nbsp;</div>
      </td>
      <td><font face="Arial, Helvetica, sans-serif" size="2"> 
        <input class="field" type="text" name="name" value="<?=$curproject['Name']?>" size="40" tabindex="1" >
        </font></td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Category
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<input class="field" type="text" name="category" value="<?=$curproject['Category']?>" size="40" maxlength="100" tabindex="2" >
      </td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Funding
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<textarea class="textarea" name="funding" cols="40" rows="2" tabindex="3"><?=$curproject['Funding']?></textarea> 
      </td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Short description
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<textarea class="textarea" name="short_description" rows="3" cols="60" tabindex="4"><?=$curproject['Title']?></textarea>
        </td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Long description
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<textarea class="textarea" name="long_description" rows="10" cols="60" tabindex="5"><?=$curproject['Description']?></textarea>
      </td>
    </tr>
    <tr>
      <td>
        <input type="submit" value="<?=$action?>" name="submit">
      </td>
    </tr>
  </table>
</form>
