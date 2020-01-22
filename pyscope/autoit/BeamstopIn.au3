#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:         myName

 Script Function:
	Template AutoIt script.

#ce ----------------------------------------------------------------------------

; Script Start - Add your code below here
#include <MsgBoxConstants.au3>
Local $before
Local $after
$before = WinActive("TEM User Interface")
If $before = 0 Then
   MsgBox($MB_OK, "Manual Beamstop", "Please insert beamstop")
   Exit(0)
EndIf
; activate the window
Local $my_window, $my_text
$my_window = "Flucam Viewer"
$my_text = "toolStrip1"
WinActivate($my_window)
WinWaitActive($my_window, "", 5)
$after = WinActive($my_window)
If $after = 0 Then
   MsgBox($MB_OK, "Manual Beamstop", "Please insert beamstop")
   Exit(0)
EndIf
; Left click beam stop insertion by coords
Local $status
$status = ControlClick($my_window, $my_text, 69572, "left", 1, 316, 12)
Sleep(500)
If $status <> 1 Then
   MsgBox($MB_OK, "Error", "Failed to click toinsert beam stop")
EndIf