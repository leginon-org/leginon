#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:         myName

 Script Function:
	Template AutoIt script.

#ce ----------------------------------------------------------------------------

; Script Start - Add your code below here
#include <AutoItConstants.au3>
#include <MsgBoxConstants.au3>
; Define the action, index, and waittime for the script
Local $mAction = "retract"
Local $iButIndex = 2
Local $mActionWaitTime = 3000 ; millisecond after click

; Default XPositions of In/Halfway/Out buttons relative to toolbar control.
Local $aButPosXs[3] = [312, 335, 355]
; Softwareversion 2.7.1  has an extra button more than the versions before.
; TODO get it from fei.cfg
Local $iExtraButton = 0
Local $iEButtonPosX = $iExtraButton * 27
;---------------Finish Scope-specific Settings------------------------
; Take the extra buttons into account.
For $i = 0 To 2 Step 1
   $aButPosXs[$i] = $aButPosXs[$i] + $iEButtonPosX
Next

; Check and click at this XY position relative to tollbar control.
; Must be in the area with background color but clickable
Local $aMyButPos[2] = [$aButPosXs[$iButIndex], 15]
; Xposition of the reference area relative to tool bar control to grab the background color
Local $iRefControlPos0 = 496
Local $after
Local $iClickable = 0
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

; Check if already at this state. Talos 2.7.1 flucam software crash if already
; in the state.
$iClickable = IsClickable($aMyButPos, $iRefControlPos0)
;MsgBox(0,'clickable',$iClickable)

; Left click beam stop button by coords
Local $status
If $iClickable = 1 Then
   $status = ControlClick($my_window, "", $my_text, "left", 1, $aMyButPos[0], $aMyButPos[1])
   Sleep($mActionWaitTime)
   If $status <> 1 Then
      MsgBox($MB_OK, "Error", "Failed to click to " & $mAction & " beam stop")
   EndIf
EndIf

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
   ; Reference background color
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
