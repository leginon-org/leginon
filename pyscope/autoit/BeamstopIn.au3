#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:         myName

 Script Function:
	Template AutoIt script.

#ce ----------------------------------------------------------------------------

; Script Start - Add your code below here
#include <MsgBoxConstants.au3>
; activate the window
Local $after
Local $my_window, $my_text
$my_window = "Flucam Viewer"; window title
$my_text = "toolStrip1"; control text
WinActivate($my_window)
WinWaitActive($my_window, "", 5)
$after = WinActive($my_window)
If $after = 0 Then
   MsgBox($MB_OK, "Manual Beamstop", "Please insert beamstop")
   Exit(0)
EndIf
; Left click beam stop out by coords
Local $status
$status = ControlClick($my_window, "", $my_text, "left", 1, 316, 12)
Sleep(500)
If $status <> 1 Then
   MsgBox($MB_OK, "Error", "Failed to click to insert beam stop")
EndIf
