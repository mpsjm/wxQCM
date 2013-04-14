import numpy
import visa
import random
# all active parts stripped out - for development without scope plugged in
class Rigol(object):
# gets waveform from scope on demand
    def __init__(self,scopeID="USB0::0x1AB1::0x0588::DS1EB144007484"):
        #self.Instrument=visa.instrument(scopeID)
        #self.Time=numpy.array( range(600), float )
        self.Time=numpy.arange(0,10*1e-3,1e-3/20.)
        self.Data=numpy.sin(self.Time*1000)
        #self.data=numpy.array( range(600), float )
        self.Tunit=""

    def getTime(self):
        return self.Time
    def getData(self):
#        print self.data
        return self.data


    def getWaveform(self):
        # get waveform from the oscilloscope
        # results stored in Time and data
        amp=1.
        phase=0.
        offset=0.
        #self.Time=numpy.arange(0,599.,1)
        randomF=random.uniform(980,1020) # use this as noisy frequency
        r = random.random()
        self.data = amp*numpy.sin(2*numpy.pi*randomF*self.Time+phase)+offset
        #self.data = amp*numpy.sin(2*numpy.pi*1110*self.Time)
        print "random frequency",(2*numpy.pi*randomF),self.Time[20]
         
        





