import math

from leginon.tomography.exposure import Exposure, Default

class Exposure2(Exposure):
    
    def __init__(self, total_dose=0.0, tilts=[], dose=0.0, exposure=0.0,
                       exposure_min=None, exposure_max=None, fixed_exposure=False):
        Exposure.__init__(self, total_dose=0.0, tilts=[], dose=0.0, exposure=0.0,
                       exposure_min=None, exposure_max=None, fixed_exposure=False)
        self.dose_rate = 0.0
        
    def updateScale(self):
        self.scales = []
        self.sum = 0
        for tilts in self.tilts:
            if not self.fixed_exposure:
                scales = [1.0/math.cos(tilt) for tilt in tilts]
            else:
                scales = [1.0 for tilt in tilts]
            self.scales.append(scales)
            self.sum += sum(scales)
        
    def getDoseRate(self):
        return self.dose_rate

    def updateExposures(self):
        default = ''
        exposure = self.exposure        # Exposure time 
        sum_ = self.sum                 # Sum of exposure times
        dose = self.dose                # Dose if dose measurment has been made
        self.exposures = []
        
        # NOTE: self.scales needs to be updated first to apply cosine dose or not. 
        
        # keep the exposure value
        #if self.fixed_exposure:
        #  for scales in self.scales:
        #      self.exposures.append(map((lambda x: exposure), scales))
        #  raise Default('%.2f s' % exposure)

        #if self.total_dose <= 0:
        #    default = 'total dose is zero'
        
        if dose <= 0:
            default = 'dose is zero'
        elif exposure <= 0:
            exposure = 1.0
            default = 'exposure time is zero'
        elif sum_ <= 0:
            default = 'exposure time sum is zero'
        else:
            self.dose_rate = dose/exposure
            #exposure = self.total_dose/(sum_*dose_rate)
        for scales in self.scales:
            self.exposures.append([exposure*scale for scale in scales])

        if default:
            raise Default(default)

if __name__ == '__main__':
    import tilts

    args = [math.radians(arg) for arg in (-60, 60, 0, 1)]
    tilts = tilts.Tilts()
    tilts.tilts = [args]
    tilts = tilts.getTilts()
    exposure = Exposure2(total_dose=200.0, tilts=tilts, dose=None)
    exposure.update(dose=None, exposure=0.2)

