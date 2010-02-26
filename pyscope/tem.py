# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import baseinstrument

class TEM(baseinstrument.BaseInstrument):
	name = None
	capabilities = baseinstrument.BaseInstrument.capabilities + (
		######## get only
		{'name': 'ColumnPressure', 'type': 'property'},
		{'name': 'ColumnValvePositions', 'type': 'property'},
		{'name': 'ExternalShutterStates', 'type': 'property'},
		{'name': 'FilmAutomaticExposureTime', 'type': 'property'},
		{'name': 'FilmDateTypes', 'type': 'property'},
		{'name': 'FilmExposureTime', 'type': 'property'},
		{'name': 'FilmExposureTypes', 'type': 'property'},
		{'name': 'HighTensionState', 'type': 'property'},
		{'name': 'HighTensionStates', 'type': 'property'},
		{'name': 'HolderStatus', 'type': 'property'},
		{'name': 'HolderTypes', 'type': 'property'},
		{'name': 'LowDoseModes', 'type': 'property'},
		{'name': 'LowDoseStates', 'type': 'property'},
		{'name': 'Magnifications', 'type': 'property'},
		{'name': 'MainScreenMagnification', 'type': 'property'},
		{'name': 'MainScreenPositions', 'type': 'property'},
		{'name': 'ObjectiveExcitation', 'type': 'property'},
		{'name': 'ScreenCurrent', 'type': 'property'},
		{'name': 'ShutterPositions', 'type': 'property'},
		{'name': 'SmallScreenPosition', 'type': 'property'},
		{'name': 'SmallScreenPositions', 'type': 'property'},
		{'name': 'StageStatus', 'type': 'property'},
		{'name': 'VacuumStatus', 'type': 'property'},

		######## get/set
		{'name': 'BeamBlank', 'type': 'property'},
		{'name': 'BeamShift', 'type': 'property'},
		{'name': 'BeamTilt', 'type': 'property'},
		{'name': 'ColumnValvePosition', 'type': 'property'},
		{'name': 'CorrectedStagePosition', 'type': 'property'},
		{'name': 'DarkFieldMode', 'type': 'property'},
		{'name': 'Defocus', 'type': 'property'},
		{'name': 'DiffractionMode', 'type': 'property'},
		{'name': 'Emission', 'type': 'property'},
		{'name': 'ExternalShutter', 'type': 'property'},
		{'name': 'FilmDateType', 'type': 'property'},
		{'name': 'FilmExposureNumber', 'type': 'property'},
		{'name': 'FilmExposureType', 'type': 'property'},
		{'name': 'FilmManualExposureTime', 'type': 'property'},
		{'name': 'FilmStock', 'type': 'property'},
		{'name': 'FilmText', 'type': 'property'},
		{'name': 'FilmUserCode', 'type': 'property'},
		{'name': 'Focus', 'type': 'property'},
		{'name': 'GunShift', 'type': 'property'},
		{'name': 'GunTilt', 'type': 'property'},
		{'name': 'HighTension', 'type': 'property'},
		{'name': 'HolderType', 'type': 'property'},
		{'name': 'ImageShift', 'type': 'property'},
		{'name': 'Intensity', 'type': 'property'},
		{'name': 'LowDose', 'type': 'property'},
		{'name': 'LowDoseMode', 'type': 'property'},
		{'name': 'Magnification', 'type': 'property'},
		{'name': 'MainScreenPosition', 'type': 'property'},
		{'name': 'RawImageShift', 'type': 'property'},
		{'name': 'Shutter', 'type': 'property'},
		{'name': 'SpotSize', 'type': 'property'},
		{'name': 'StagePosition', 'type': 'property'},
		{'name': 'Stigmator', 'type': 'property'},
		{'name': 'TurboPump', 'type': 'property'},

		######## methods
		{'name': 'filmExposure', 'type': 'method'},
		{'name': 'findMagnifications', 'type': 'method'},
		{'name': 'normalizeLens', 'type': 'method'},
		{'name': 'postFilmExposure', 'type': 'method'},
		{'name': 'preFilmExposure', 'type': 'method'},
		{'name': 'resetDefocus', 'type': 'method'},
		{'name': 'runBufferCycle', 'type': 'method'},
	)
