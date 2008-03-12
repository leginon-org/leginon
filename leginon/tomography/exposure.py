import math

class LimitError(Exception):
    pass

class Default(Exception):
    pass

class Exposure:
    def __init__(self, total_dose=0.0, tilts=[], dose=0.0, exposure=0.0,
                       exposure_min=None, exposure_max=None):
        self.total_dose = total_dose
        self.tilts = tilts
        self.dose = dose
        self.exposure = exposure
        self.exposure_min = exposure_min
        self.exposure_max = exposure_max
        self.updateScale()
        try:
            self.updateExposures()
        except Default:
            pass
        self.checkExposureLimits()

    def update(self, **kwargs):
        attrs = [
            'total_dose',
            'tilts',
            'dose',
            'exposure',
            'exposure_min',
            'exposure_max',
        ]

        for attr in attrs:
            if attr not in kwargs:
                continue
            setattr(self, attr, kwargs[attr])

        self.updateScale()
        self.updateExposures()
        self.checkExposureLimits()

    def getTotalDose(self):
        return self.total_dose

    def setTotalDose(self, total_dose):
        self.total_dose = total_dose
        self.updateExposures()

    def getTilts(self):
        return list(self.tilts)

    def setTilts(self, tilts):
        self.tilts = tilts
        self.updateScale()
        self.updateExposures()

    def updateScale(self):
        self.scales = []
        self.sum = 0
        for tilts in self.tilts:
            scales = [1.0/math.cos(tilt) for tilt in tilts]
            self.scales.append(scales)
            self.sum += sum(scales)

    def getDose(self):
        return self.dose

    def setDose(self, dose):
        self.dose = dose
        self.updateExposures()

    def getExposure(self):
        return self.exposure

    def setExposure(self, exposure):
        self.exposure = exposure
        self.updateExposures()

    def setExposureLimits(self, exposure_min, exposure_max):
        self.exposure_min = exposure_min
        self.exposure_max = exposure_max

    def checkExposureLimits(self):
        if not self.exposures or self.dose <= 0 or self.exposure <= 0:
            return

        exposures = []
        for e in self.exposures:
            exposures += e
        exposure_min = min(exposures)
        exposure_max = max(exposures)

        min_flag = (self.exposure_min is not None
                    and exposure_min < self.exposure_min)
        max_flag = (self.exposure_max is not None
                    and exposure_max > self.exposure_max)

        if min_flag or max_flag:
            max_scale = max([max(scales) for scales in self.scales])
            exposure = self.exposure_max/max_scale
            dose_min = self.total_dose/sum([sum([exposure*scale for scale in scales]) for scales in self.scales])*self.exposure
            exposure = self.exposure_min
            dose_max = self.total_dose/sum([sum([exposure*scale for scale in scales]) for scales in self.scales])*self.exposure
            s = 'dose must be between %g and %g e-/A^2'
            s %= (dose_min, dose_max)
            raise LimitError(s)

    def getExposures(self):
        return list(self.exposures)

    def updateExposures(self):
        default = ''
        exposure = self.exposure
        self.exposures = []

        if self.total_dose <= 0:
            default = 'total dose is zero'
        elif self.dose <= 0:
            default = 'dose is zero'
        elif self.exposure <= 0:
            exposure = 1.0
            default = 'exposure time is zero'
        elif self.sum <= 0:
            default = 'exposure time sum is zero'
        else:
            dose_rate = self.dose/self.exposure
            exposure = self.total_dose/(self.sum*dose_rate)

        for scales in self.scales:
            self.exposures.append([exposure*scale for scale in scales])

        if default:
            raise Default(default)

    def getExposureRange(self):
        exposures = []
        for e in self.exposures:
            exposures += e
        if not exposures:
            raise ValueError
        return min(exposures), max(exposures)

if __name__ == '__main__':
    import tilts

    args = [math.radians(arg) for arg in (-60, 60, 0, 1)]
    tilts = tilts.Tilts()
    tilts.tilts = [args]
    tilts = tilts.getTilts()
    exposure = Exposure(total_dose=200.0, tilts=tilts, dose=None)
    exposure.update(dose=None, exposure=0.2)

