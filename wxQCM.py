#!/Users/simonmartin/.virtualenvs/rigolScope/python
"""QCM system - basedon Rigol oscilloscope"""
# wxQCM.py

import wx
import os
import time 
import numpy
import scipy
from scipy.optimize import leastsq
import matplotlib
import visa
import dummyRigol
#import rigol


from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

class Panel1(wx.Panel):
    """ This panel will display the scope output and the fit"""
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,size=(10,10))
        #configure graph
        self.figure=matplotlib.figure.Figure()
        self.scopeAxes=self.figure.add_subplot(211)
        t=numpy.arange(0.,10.,0.1)
        s=t*2.
        self.y_max=numpy.max(s)
        self.y_min=numpy.min(s)
        self.scopeAxes.plot(t,s)
        self.qcmAxes=self.figure.add_subplot(212)
        self.qcmAxes.plot(s,t)
        self.canvas=FigureCanvas(self,-1,self.figure)


    def plotScope(self,xdata,ydata,StatusBar):
        #StatusBar.SetStatusText("updating")
        self.y_max=numpy.max(ydata)
        self.y_min=numpy.min(ydata)
        self.x_max=numpy.max(xdata)
        self.x_min=numpy.min(xdata)
        self.scopeAxes.clear()
        self.scopeAxes.plot(xdata,ydata)
        self.figure.canvas.draw()
        
    def plotScope(self,xdata,ydata,params,func):
        self.y_max=numpy.max(ydata)
        self.y_min=numpy.min(ydata)
        self.x_max=numpy.max(xdata)
        self.x_min=numpy.min(xdata)
        self.scopeAxes.clear()
        self.scopeAxes.plot(xdata,func(xdata,params),xdata,ydata)
        self.figure.canvas.draw()
        
    def plotResults(self,xdata,ydata):
        # plots fitted results
        #self.y_max=numpy.max(ydata)
        #self.y_min=numpy.min(ydata)
        #self.x_max=numpy.max(xdata)
        #self.x_min=numpy.min(xdata)
        self.qcmAxes.clear()
        self.qcmAxes.set_ylim([900,1100])
        self.qcmAxes.set_autoscaley_on(False)
        self.qcmAxes.plot(xdata,ydata)
        self.figure.canvas.draw()


#class Panel2(wx.Panel):
#    """The controls for the qcm measurement go here"""
#    def __init__(self,parent):
#        wx.Panel.__init__(self,parent,-1,size=(10,10))
#        self.runButton=wx.Button(self,-1,"Run",size=(50,20),pos=(10,10))
#        self.runButton.Bind(wx.EVT_BUTTON,self.run) 
#        self.fileNameButton=wx.Button(self,-1,"File name",size=(100,20),pos=(80,10))
#        self.fileNameButton.Bind(wx.EVT_BUTTON,self.SetFileSaveAs)
        
    
           
class QCMFrame(wx.Frame):
    def __init__(self,parent,title):
        wx.Frame.__init__(self,parent,title=title,size=(600,600))
        # Add splitter to the frame
        self.sp=wx.SplitterWindow(self)
        self.panel1=Panel1(self.sp)
        self.panel2=wx.Panel(self.sp,style=wx.SUNKEN_BORDER)
        self.sp.SplitHorizontally(self.panel1,self.panel2,500)
        self.running=False
        self.StatusBar=self.CreateStatusBar()
        self.StatusBar.SetStatusText("Off")
        self.runButton=wx.Button(self.panel2,-1,"Run",size=(50,20),pos=(10,10))
        self.runButton.Bind(wx.EVT_BUTTON,self.run)
        # need to be able to set filename for saving data
        self.dirName=""
        self.fileName=""
        self.fileNameButton=wx.Button(self.panel2,-1,"File name",size=(100,20),pos=(80,10))
        self.fileNameButton.Bind(wx.EVT_BUTTON,self.SetFileSaveAs)
        # need to keep updating the data and plots - use a timer system
        self.acquire_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_acquire_timer, self.acquire_timer)
        self.Scope=dummyRigol.Rigol(self)
        #self.Scope=rigol.Rigol(self)
        self.fittedFrequency=6182.
        self.fittedAmplitude=1.
        self.fittedPhase=0.
        self.fittedOffset=0.
        # list to store fitted frequencies
        self.freqData=[0]
        self.nData=[0]
        self.dataFilename=""
        # a timer to keep track of times
        self.startTime=0.
        
    def run(self,event):
        if self.running:
            self.acquire_timer.Stop()
            self.StatusBar.SetStatusText("off")
            self.running=False
        else:
            self.StatusBar.SetStatusText("run")
            self.running=True
            # set to update at 1Hz - should make this configurable in the future      
            self.acquire_timer.Start(1000)
            # should make timer start once run has been pressed
            self.startTime=time.time()
        
    
    def on_acquire_timer(self,event):
        # Timer says it is time to get new data set
        self.Scope.getWaveform()
        # Have data, now to fit it.
        self.fitSingleFrequency()
        #self.panel1.plotScope(self.Scope.getTime(),self.Scope.getData(),self.StatusBar)
        self.panel1.plotScope(self.Scope.getTime(),self.Scope.getData(),[self.fittedAmplitude, self.fittedFrequency, self.fittedPhase,self.fittedOffset],self.peval)
        self.panel1.plotResults(self.nData,self.freqData)
        self.StatusBar.SetStatusText("Frequency"+str(self.fittedFrequency))
        
    def fitSingleFrequency(self):
        # use last values as start values
        #p0 = [self.fittedAmplitude, self.fittedFrequency, self.fittedPhase,self.fittedOffset]
        p0 = [self.fittedAmplitude, self.fittedFrequency, self.fittedPhase,self.fittedOffset]
        # fit data using least squares
        #plsq = leastsq(self.residuals, p0, args=(self.Scope.getData(), self.Scope.getTime()),Dfun=self.jacobian,col_deriv=1)
        plsq = leastsq(self.residuals, p0, args=(self.Scope.getData(), self.Scope.getTime()))
        # preserve values
        data=plsq[0]
        self.fittedAmplitude=data[0]  
        self.fittedFrequency=data[1]
        print "fitted frequency:",self.fittedFrequency 
        #print self.Scope.getTime()[20]
        self.fittedPhase=data[2]
        self.fittedOffset=data[3]
        # add new frequency to list
        self.freqData.append(self.fittedFrequency)
        self.nData.append(len(self.nData))
        with open(os.path.join(self.dirName, self.fileName), 'a') as f:
            f.write('{:.3f},{:.7f}\n'.format(time.time()-self.startTime,self.fittedFrequency))
            
 
        
    def peval(self,x, p):
        return (p[0]*numpy.sin(p[1]*x+p[2])+p[3])
        # parameters: amplitude, frequency (radians per sec), phase shift, y offset

    def residuals(self,p, y, x):
        err=y-(p[0]*numpy.sin(p[1]*x+p[2])+p[3])
        return err    

    def jacobian(self,p,x,y):
        return [numpy.sin(p[1]*x+p[2]),x*p[0]*numpy.cos(p[1]*x+p[2]),p[0]*numpy.cos(p[1]*x+p[2]),numpy.ones(len(x))]
        
    def SetFileSaveAs(self, event):
        """ File|SaveAs event - Prompt for File Name. """
        ret = False
        dlg = wx.FileDialog(self, "Save As", self.dirName, self.fileName,
                           "Text Files (*.txt)|*.txt|All Files|*.*", wx.SAVE)
        if (dlg.ShowModal() == wx.ID_OK):
            self.fileName = dlg.GetFilename()
            self.dirName = dlg.GetDirectory()
            ### - Use the OnFileSave to save the file
            if self.OnFileSave(event):
                self.SetTitle(APP_NAME + " - [" + self.fileName + "]")
                ret = True
        dlg.Destroy()
        return ret
    
#---------------------------------------
    def OnFileSave(self, event):
        """ File|Save event - Just Save it if it's got a name. """
        print self.dirName,":",self.fileName
        if (self.fileName != "") and (self.dirName != ""):
            try:
                f = file(os.path.join(self.dirName, self.fileName), 'w')
                #f.write(self.rtb.GetValue())
                f.write("time,freq\n")
                self.PushStatusText("Saved file: " )
                f.close()
                return True
            except:
                self.PushStatusText("Error in saving file.")
                return False
        else:
            ### - If no name yet, then use the OnFileSaveAs to get name/directory
            return self.OnFileSaveAs(e)


app = wx.App(redirect=False)

frame = QCMFrame(None, 'QCM.py')
frame.Show()

app.MainLoop()
