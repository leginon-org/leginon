#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:         myName

 Script Function:
	Template AutoIt script.

#ce ----------------------------------------------------------------------------

; Script Start - Add your code below here
#include <AutoItConstants.au3>
#include <Misc.au3>
If _Singleton("TuiAcquire", 1) == 0 Then
   Exit
EndIf
#include <MsgBoxConstants.au3>
Local $before
Local $after
$before = WinActive("TEM User Interface")
; activate the window
Local $my_window, $my_text
$my_window = "CCD/TV Camera"
$my_text = ""
WinActivate($my_window)
WinWaitActive($my_window, "", 5)
$after = WinActive($my_window)

; Select camera from combobox
Local $error_text, $camera, $sampling
$camera = ControlGetText($my_window, "", "ComboBox1")
$exptime = ControlGetText($my_window,"", "Edit1")
$sampling = ControlGetText($my_window, "", "ComboBox2")
$readout_area = ControlGetText($my_window, "", "ComboBox3")
$errortext = ""
If $camera <> "BM-Ceta" Then
   $errortext &= "Camera is not BM-Ceta" & @LF
EndIf
If $sampling <> 2 Then
   ControlSend($my_window,"","ComboBox2",2)
   Sleep(200)
EndIf
If $readout_area <> "Full" Then
   ControlSend($my_window,"", "ComboBox3","Full")
EndIf
; Exposure time
If $CmdLine[0] > 0 Then
   $PresetTime = Number($CmdLine[1])
Else
   $PresetTime = 1.0
EndIf
If Number($exptime) <> $PresetTime Then
   ControlSetText($my_window,"", "Edit1",$PresetTime)
   ControlClick($my_window,"", "[CLASS:editenter;INSTANCE:1]")
EndIf

; preset settings
Local $settings_preset, $mode, $rolling_shutter, $series_size
$setting_preset = ControlGetText($my_window, "", "ComboBox8")
$mode = ControlGetText($my_window, "", "ComboBox14")
$rolling_shutter = ControlCommand($my_window, "", "[CLASS:Button;INSTANCE:16]", "IsChecked")
$series_size = ControlGetText($my_window, "", "Edit8")
If $setting_preset <> "Acquire" Then
   $errortext &= "Settings is not set to Acquire" & @LF
EndIf
If $mode <> "Continuous" Then
   ControlSend($my_window,"", "ComboBox14","Continuous")
EndIf
If $rolling_shutter <> 1 Then
   $errortext &= "Rolling shutter is not enabled" & @LF
EndIf
If $series_size < 5 Then
   $errortext &= "Series size is not large enough" & @LF
EndIf
; Display Error and exit
If StringLen($errortext) > 0 Then
   MsgBox($MB_OK, "Fatal Settings Error", $errortext)
   Exit
EndIf

; Left click Acquire Button
Local $status
$status = ControlClick($my_window, $my_text, "[CLASS:Button;INSTANCE:3]", "left", 1)
Sleep(500)
If $status <> 1 Then
   MsgBox($MB_OK, "Error", "Failed to click")
EndIf

