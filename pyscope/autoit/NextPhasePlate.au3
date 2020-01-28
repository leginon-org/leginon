; Move to next phase plate
; Phase plate OCX and flapout needs to be opened in UI!
; inspired by Wim Hagen
; modified for leginon by M.Wolf and A.Chen
; compile to exe (right click nextphaseplate.au3)

#RequireAdmin
AutoItSetOption('MouseCoordMode', 0)

; Set the Escape hotkey to terminate the script.
; HotKeySet("{ESC}", "_Terminate")

NextPP()

Func NextPP()
;    While 1
;	  WinWait("[TITLE:Apertures; CLASS:#32770; W:638; H:270]")
	  If WinExists("[TITLE:Apertures; CLASS:#32770; W:638; H:270]") Then
		 WinActivate("[TITLE:Apertures; CLASS:#32770; W:638; H:270]")
		 MouseClick('primary', 524, 5, 1, 0)
		 MouseClick('primary', 335, 103, 1, 0)
	  EndIf

	  ; Avoid high CPU usage.
;	  Sleep(50000)
;    WEnd
EndFunc   ;==>Example

Func _Terminate()
    Exit
 EndFunc   ;==>_Terminate

; in tecnai.py on scope PC:
; AUTOIT_EXE_PATH = "C:\\Program Files\\AutoIt3\\nextphaseplate.exe"