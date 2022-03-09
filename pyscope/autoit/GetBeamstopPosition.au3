#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:       Anchi Cheng

 Script Function:
	Get and Set Aperture Selection
	To run from command line needs parameters

	Requires setting the position selections in fei.cfg

    $sFeiConfigPath: the path to fei.cfg
	$tem:(talos or titan)
	$mechanism: (condenser_2, objective, selected_area)
	$action: (get or set)

	If setting, also the sizes in um or 'open' as defined in fei.cfg.

	$sSelection

#ce ----------------------------------------------------------------------------

; Script Start - Add your code below here
#include <AutoItConstants.au3>
#include <MsgBoxConstants.au3>
#include <Array.au3>
Global $error_log = @UserProfileDir & "\myami_log\autoit_error.log"
Global $result_log = @UserProfileDir & "\myami_log\autoit_result.log"
_ResetError()
_ResetResult()
; TODO pass info from cfg files
Global $sFeiConfigPath = "c:\Program Files\myami\fei.cfg"
; Set Default
; Xposition of the reference area relative to tool bar control to grab the background color
Local $iRefControlPosX = 496

; Defautl XPositions of In/Halfway/Out buttons relative to toolbar control.
Local $aButPosXs[3] = [312, 335, 355]
; Softwareversion with more buttons displacement
; TODO get it from fei.cfg
Local $iExtraButton = 0
Local $iEButtonPosX = $iExtraButton * 27

; Take extra buttons into account.
For $i = 0 To 2 Step 1
   $aButPosXs[$i] = $aButPosXs[$i] + $iEButtonPosX
Next

; Check and click at this XY position relative to tollbar control.
; Must be in the area with background color but clickable
; In position
Local $after
Local $iClickable = 0
Local $tCurrentPosName = "unknown"
Global $my_window, $my_text
; window constants
$my_window = "Flucam Viewer"; window title
$my_text = "toolStrip1"; control text
; activate the window
$hMyWin = WinActivate($my_window, $my_text)
WinWaitActive($my_window, $my_text, 5)
$after = WinActive($my_window)
If $after = 0 Then
   ;Click somewhere on Window title bar
   MouseClick($MOUSE_CLICK_LEFT, 507,12)
   WinActivate($my_window, $my_text)
   WinWaitActive($my_window, $my_text, 5)
   $after = WinActive($my_window)
   If $after = 0 Then
      MsgBox($MB_OK, "Manual Beamstop Test", "Please insert beamstop" & WinGetTitle(''))
      Exit(0)
   EndIf
EndIf
$tCurrentPosName = GetBeamstopPosition($aButPosXs, $iRefControlPosX)


   _WriteResult($tCurrentPosName)

Func GetBeamstopPosition($aButtonXs, $iRefControlPos0)
   ; Y position at 15 as default
   Local $aButPos[2] = [0,15]
   Local $aPositionNames = ["in","halfway","out"]
   Local $tPosition = "unknown"
   For $n = 0 To 2 Step 1
      $aButPos[0] = $aButtonXs[$n]
      $iResult = IsClickable($aButPos, $iRefControlPos0)
      If $iResult == 0 Then
         $tPosition = $aPositionNames[$n]
         ExitLoop
      EndIf
   Next
   ;MsgBox($MB_OK,'current beamstop position=',$tPosition)
   return $tPosition
EndFunc

Func IsClickable($aButPos, $iRefControlPos0)
   ; Check Beamstop button background color in comparison to the background empty area.
   ;Reference position relative to the origin of the toolbar control object
   Local $aRefPos[2] = [$iRefControlPos0, $aButPos[1]]
   Local $iColor = 0
   Local $iRefColor = 0

   ControlFocus($my_window,"",$my_text)
   $aWinPos = WinGetPos($my_window)
   $aConPos = ControlGetPos($my_window,"",$my_text)
   ; Check at some empty Position in the button
   $iCheckMousePos0 = $aWinPos[0]+$aConPos[0]+$aButPos[0]
   $iCheckMousePos1 = $aWinPos[1]+$aConPos[1]+$aButPos[1]
   ;
   $iRefMousePos0 = $aWinPos[0]+$aConPos[0]+$aRefPos[0]
   $iRefMousePos1 = $aWinPos[1]+$aConPos[1]+$aRefPos[1]
   $iColor = PixelGetColor($iCheckMousePos0, $iCheckMousePos1)
   $iRefColor = PixelGetColor($iRefMousePos0, $iRefMousePos1)

   ;MsgBox($MB_SYSTEMMODAL,"",$iCheckMousePos0 & ": " & $iCheckMousePos1 & ":" & $iColor & "ref: " & $iRefMousePos0 & ", " & $iRefMousePos1 & ':' & $iRefColor)
   If $iColor = $iRefColor Then
	    return 1
   Else
	    return 0
   EndIf
EndFunc

Func getFeiConfigModuleLines($configpath, $module)
   ; Read lines under a module in fei.cfg
   Local $configx86path
   Local $h2 = FileOpen($configpath, 0)
   If $h2 == -1 Then
      $configx86path = StringReplace($configpath, "Program Files", "Program Files (x86)", 1)
      $h2 = FileOpen($configx86path, 0)
      If $h2 == -1 Then
         _WriteError("can not open " & $configpath & " nor " & $contigx86path)
         Exit
      EndIf
   EndIf
   Local $bInModule = False
   ; declare array must have at least one item
   Local $Lines[1]=['dummy']
   While 1
      Local $sLine = FileReadLine($h2)
	  If @error Then ExitLoop
	  If StringLeft($sLine,1)=="[" AND StringRight($sLine,1)=="]" Then
		 Local $modname = StringSplit(StringSplit($sLine,"]",2)[0],"[",2)[1]
		 If $modname == $module Then

			$bInModule = True
		 Else
			$bInModule = False
		 EndIf
	  ElseIf $bInModule == True Then
		 Local $aBits = StringSplit($sLine,"=",2)
		 If UBound($aBits) > 1 Then
			_ArrayAdd($Lines, $sLine)
		 EndIf
	  EndIf
   Wend
   FileClose($h2)
   ;remove dummy
   _ArrayDelete($Lines, 0)
   Return $Lines
EndFunc

Func GetFeiConfigHasAutoC3($configpath)
   ;Get boolean value of aperture:has_auto_c3 from fei.cfg
   Local $key = 'has_auto_c3'
   Local $aLines = getFeiConfigModuleLines($configpath, 'aperture')
   Local $hasAutoC3 = False
   For $i = 0 to UBound($aLines)-1
	  Local $sLine = $aLines[$i]
	  Local $aBits = StringSplit($sLine,"=",2)
	  $sKey = StringStripWS($aBits[0],3); strip leading and trailing white spaces
	  If StringLower($sKey) == StringLower($key) Then
		 If StringLower(StringStripWS($aBits[1],3)) = 'true' Then
			$hasAutoC3 = True
		 EndIf
	  EndIf
   Next
   return $hasAutoC3
EndFunc

Func GetFeiConfigSelections($configpath,$module,$key)
   Local $aListNames[10] ; In case there are 6 phase plates.
   Local $aLines = getFeiConfigModuleLines($configpath, $module)
   For $i = 0 to UBound($aLines)-1
	  Local $sLine = $aLines[$i]
	  Local $aBits = StringSplit($sLine,"=",2)
	  $sKey = StringStripWS($aBits[0],3); strip leading and trailing white spaces

	  If StringLower($sKey) == StringLower($key) Then
		 Local $aList = StringSplit($aBits[1],",",2)
		 For $i = 0 to UBound($aList)-1
			$aListNames[$i] = StringStripWS($aList[$i],3); strip leading and trailing white spaces
			;MsgBox(0,'config value',$sKey & ' ' & $i & ' ' & $aListNames[$i])
		 Next
	  EndIf
   Next
   If $aListNames[0]=='' Then
	  _WriteError("Can not find " & $key & " selection list in " & $module & " in fei.cfg")
	  Exit
   EndIf
   Return $aListNames
EndFunc

Func _ResetError()
   FileDelete($error_log)
EndFunc

Func _WriteError($msg)
   ;Error written to log is read by caller to retrieve error
   Local $h = FileOpen($error_log, 1)
   FileWriteLine($h,$msg)
   FileClose($h)
EndFunc

Func _ResetResult()
   FileDelete($result_log)
EndFunc

Func _WriteResult($msg)
   ;Result written to log is read by caller
   Local $h = FileOpen($result_log, 1)
   FileWriteLine($h,$msg)
   FileClose($h)
EndFunc




