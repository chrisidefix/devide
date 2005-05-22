#!/usr/bin/env python
# $Id: devide.py,v 1.79 2005/05/22 00:01:53 cpbotha Exp $

# the current main release version
DEVIDE_VERSION = '20050522-T'

# VTK and ITK extra version information: here we add the
# cvs commands necessary to get the versions of VTK and ITK
# that are required for this release of DeVIDE checked out.
# If you're not cpbotha, you shouldn't change these.
VTK_VERSION_EXTRA = 'update -r ParaView-2-0-2 -dP'
ITK_VERSION_EXTRA = 'update -dAP'

# standard Python imports
import getopt
import mutex
import os
import re
import stat
import string
import sys
import time

# WX imports
# this HAS to go before we call import wx
import fixWxImports
import wx
import wx.html

# UI imports
import resources.python.mainFrame
import resources.graphics.images

class mainConfigClass(object):

    def __init__(self):
        import defaults
        self.useInsight = defaults.USE_INSIGHT
        self.itkPreImport = True
        
        self._parseCommandLine()

    def dispUsage(self):
        print "-h or --help               : Display this message."
        print "--insight or --itk         : Use ITK-based modules."
        print "--no-insight or --no-itk   : Do not use ITK-based modules."
        print "--no-itk-preimport         : Do not pre-import ITK."

    def _parseCommandLine(self):
        try:
            # 'p:' means -p with something after
            optlist, args = getopt.getopt(
                sys.argv[1:], 'h',
                ['help', 'no-itk', 'no-insight', 'itk', 'insight',
                 'no-itk-preimport'])
        except getopt.GetoptError,e:
            self.dispUsage()
            sys.exit(1)

        for o, a in optlist:
            if o in ('-h', '--help'):
                self.dispUsage()
                sys.exit(1)

            elif o in ('--insight', '--itk'):
                self.useInsight = True

            elif o in ('--no-itk', '--no-insight'):
                self.useInsight = False

            elif o in ('--no-itk-preimport',):
                self.itkPreImport = False

# ---------------------------------------------------------------------------
class devide_app_t(wx.App):
    """Main devide application class.

    Class that's used as communication hub for most other components of the
    platform.  We've derived from wxApp but this is not a requirement... we
    could just as well have contained the wxApp instance.  This inheritance
    does not prevent abstraction from the GUI.
    """
    
    def __init__(self):
        self.mainConfig = mainConfigClass()
        
        self._inProgress = mutex.mutex()
        self._previousProgressTime = 0
        self._currentProgress = -1
        self._currentProgressMsg = ''
        
        self._mainFrame = None

        #self._appdir, exe = os.path.split(sys.executable)
        if hasattr(sys, 'frozen') and sys.frozen:
            self._appdir, exe = os.path.split(sys.executable)
        else:
            dirname = os.path.dirname(sys.argv[0])
            if dirname and dirname != os.curdir:
                self._appdir = dirname
            else:
                self._appdir = os.getcwd()
        
        wx.App.__init__(self, 0)

        self._assistants = assistants(self)
        self._graphEditor = None
        self._pythonShell = None
        self._helpClass = None
	

    def OnInit(self):
        self._mainFrame = resources.python.mainFrame.mainFrame(
            None, -1, "dummy", name="DeVIDE")

        wx.InitAllImageHandlers()
        self._mainFrame.SetIcon(self.getApplicationIcon())

        wx.EVT_MENU(self._mainFrame, self._mainFrame.fileExitId,
                    self.exitCallback)
        
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowGraphEditorId,
                   self._handlerMenuGraphEditor)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowPythonShellId,
                    self._handlerMenuPythonShell)

        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowMinimiseChildrenId,
                    lambda e: self._windowIconizeAllChildren())
        wx.EVT_MENU(self._mainFrame, self._mainFrame.windowRestoreChildrenId,
                    lambda e: self._windowRestoreAllChildren())
        
        wx.EVT_MENU(self._mainFrame, self._mainFrame.testingAllTestsId,
                    self._handlerTestingAllTests)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.helpContentsId,
                    self._handlerHelpContents)
        wx.EVT_MENU(self._mainFrame, self._mainFrame.helpAboutId,
                    self.aboutCallback)

        wx.EVT_CHECKBOX(
            self._mainFrame, self._mainFrame.enableExecutionCheckBox.GetId(),
            self._handlerEnableExecution)

        wx.EVT_CHECKBOX(
            self._mainFrame, self._mainFrame.blockExecutionCheckBox.GetId(),
            self._handlerBlockExecution)

        self._mainFrame.Show(1)
        # here we also show twice: in wxPython 2.4.2.4 the TextCtrls sometimes
        # have difficulty completely drawing themselves at startup
        self._mainFrame.Show(1)        
        self.SetTopWindow(self._mainFrame)

        # pre-import VTK and optionally ITK (these are BIG libraries)
        import startupImports
        startupImports.doImports(
            self.setProgress, mainConfig=self.mainConfig)

        # perform post initialisation and pre-loading imports
        postWxInitImports()
        
        # find all modules that we can use
	self.moduleManager = moduleManager(self)

        # perform vtk initialisation
        self._vtkInit()

        #
        self.moduleManager.enableExecution()
        self._mainFrame.enableExecutionCheckBox.SetValue(1)

        # indicate that we're ready to go!
        self.setProgress(100, 'Started up')

        return True
        

    def _vtkInit(self):
        """All VTK specific initialisation is done from here.
        """
        
        # CRITICAL VTK CUSTOMISATION BIT:
        # multi-threaded vtk objects will call back into python causing
        # re-entrancy; usually, the number of threads is set to the number
        # of CPUs, so on single-cpu machines this is no problem
        # On Linux SMP this somehow does not cause any problems either.
        # On Windows SMP the doubleThreshold module can reliably crash your
        # machine.  Give me a Windows SMP machine, and I shall fix it.
        # for now we will just make sure that threading doesn't use more
        # than one thread. :)
        vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
        vtk.vtkMultiThreader.SetGlobalDefaultNumberOfThreads(1)
        
        # now make sure that VTK will always send error to vtk.log logfile
        temp = vtkdevide.vtkEventOutputWindow()
        temp.SetInstance(temp)

        def observerEOW(theObject, eventType):
            # theObject is of course a vtkEventOutputWindow
            textType = theObject.GetTextType()
            text = theObject.GetText()

            #print "EOW: %d - %s" % (textType, text)
            
            if textType == 0:
                # Text
                #wx.LogMessage(text)
                self.logMessage(text)

            elif textType == 1:
                # and we disable execution, else the error keeps on getting
                # triggered...
                self.moduleManager.disableExecution()
                self._mainFrame.enableExecutionCheckBox.SetValue(0)
                
                # ErrorText - shown and logged
                wx.LogError(text)
                self.logMessage(text)
                
            elif textType == 2:
                # WarningText
                #wx.LogWarning(text)
                self.logMessage(text)
                
            elif textType == 3:
                # GenericWarningText
                #wx.LogWarning(text)
                self.logMessage(text)
                
            else:
                # DebugText
                #wx.LogDebug(text)
                self.logMessage(text)

        temp.AddObserver('ErrorEvent', observerEOW)
        temp.AddObserver('WarningEvent', observerEOW)        
            
        del temp

    def OnExit(self):
        pass
    
    def getApplicationIcon(self):
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(
            resources.graphics.images.getdevidelogo32x32Bitmap())
        return icon

    def getMainWindow(self):
        return self._mainFrame        

    def get_main_window(self):
        return self.getMainWindow()

    def getModuleManager(self):
	return self.moduleManager

    def get_assistants(self):
        return self._assistants

    def getAppDir(self):
        return self._appdir

    def get_appdir(self):
        return self.getAppDir()

    def _handlerBlockExecution(self, event):
        if self._mainFrame.blockExecutionCheckBox.GetValue():
            self.moduleManager.interruptExecution()
            # this will also call disableExecution, so we set the correct box
            self._mainFrame.enableExecutionCheckBox.SetValue(0)

        else:
            self.moduleManager.resumeExecution()

    def _handlerEnableExecution(self, event):
        if self._mainFrame.enableExecutionCheckBox.GetValue():
            self.moduleManager.enableExecution()
        else:
            self.moduleManager.disableExecution()

    def _handlerHelpContents(self, event):
        self.showHelp()

    def _handlerTestingAllTests(self, event):
        import testing
        reload(testing)
        dt = testing.devideTesting(self)
        dt.runAllTests()

    def quit(self):
        # take care of the graphEditor if it exists
        if self._graphEditor:
            self._graphEditor.close()
            
        # shutdown all modules gracefully
        self.moduleManager.close()

        # take down the help
        if self._helpClass:
            self._helpClass.close()
        
	# take care of main window
	self._mainFrame.Close()

    def showHelp(self):
        self._startHelpClass()
        self._helpClass.show()

    def startPythonShell(self):
        if self._pythonShell == None:
            self._pythonShell = pythonShell(self.getMainWindow(),
                                            'Main DeVIDE Python Introspection',
                                            self.getApplicationIcon(),
                                            self.getAppDir())
            self._pythonShell.injectLocals({'devideApp' : self})
            self._pythonShell.setStatusBarMessage(
                "'devideApp' is bound to the main app class.")
        else:
            self._pythonShell.show()

    def _startHelpClass(self):
        if self._helpClass == None:
            self._helpClass = helpClass(self)

    def startGraphEditor(self):
        if self._graphEditor == None:
            self._graphEditor = graphEditor(self)
        else:
            self._graphEditor.show()

    def logMessage(self, message, timeStamp=True):
        if timeStamp:
            msg = "%s: %s" % (
                time.strftime("%X", time.localtime(time.time())),
                message)
        else:
            msg = message
                              
        self._mainFrame.messageLogTextCtrl.AppendText(
            msg + '\n')

    def setProgress(self, progress, message, noTime=False):
        # 1. we shouldn't call setProgress whilst busy with setProgress
        # 2. only do something if the message or the progress has changed
        # 3. we only perform an update if a second or more has passed
        #    since the previous update, unless this is the final
        #    (i.e. 100% update) or noTime is True

        # the testandset() method of mutex.mutex is atomic... this will grab
        # the lock and set it if it isn't locked alread and then return true.
        # returns false otherwise

        if self._inProgress.testandset():
            if message != self._currentProgressMsg or \
                   progress != self._currentProgress:
                if abs(progress - 100.0) < 0.01 or noTime or \
                       time.time() - self._previousProgressTime >= 1:
                    self._previousProgressTime = time.time()
                    self._currentProgressMsg = message
                    self._currentProgress = progress
                    self._mainFrame.progressGauge.SetValue(
                        int(round(progress)))
                    self._mainFrame.progressText.SetLabel(message)

                    # we also output an informative message to standard out
                    # in cases where DeVIDE is very busy, this is quite
                    # handy.
                    print "%s: %.2f" % (message, progress)

                    # activate the busy cursor (we're a bit more lenient
                    # on its epsilon)
                    if abs(progress - 100.0) > 1:
                        if not wx.IsBusy():
                            wx.BeginBusyCursor()
                            
                    # or switch it off
                    else:
                        if wx.IsBusy():
                            wx.EndBusyCursor()

                        # let's also show the completion message in the
                        # message log...
                        self.logMessage(message)
                   
                    # bring this window to the top if the user wants it
                    if self._mainFrame.progressRaiseCheckBox.GetValue():
                        self._mainFrame.Raise()

                    # we want wx to update its UI, but it shouldn't accept any
                    # user input, else things can get really crazy. -
                    # we do keep interaction for the main window enabled,
                    # but we disable all menus.
                    menuCount = self._mainFrame.GetMenuBar().GetMenuCount()
                    for menuPos in range(menuCount):
                        self._mainFrame.GetMenuBar().EnableTop(menuPos, False)
                        
                    wx.SafeYield(win=self._mainFrame)

                    for menuPos in range(menuCount):
                        self._mainFrame.GetMenuBar().EnableTop(menuPos, True)

            # unset the mutex thingy
            self._inProgress.unlock()

    def aboutCallback(self, event):
        from resources.python.aboutDialog import aboutDialog

        aboutText = '''
        <html>
        <body>
        <center>
        <h3>DeVIDE v.%s</h3>
        <p>DeVIDE is copyright (c) 2003 Charl P. Botha<br>
        http://cpbotha.net/phd/
        </p>
        <p>Unauthorised use or distribution strictly prohibited.
        See LICENSE.txt in the docs directory for detailed terms of
        use.
        </p>
        <p>
        wxPython %s, Python %s<br>
        VTK %s<br>
        ITK %s
        </p>
        </center>
        </body>
        </html>
        '''

        about = aboutDialog(self._mainFrame, -1, 'dummy')
        pyver = string.split(sys.version)[0]

        # make VTK "official version" + date of nightly (so we know
        # what to checkout)
        vsv = vtk.vtkVersion.GetVTKSourceVersion()
        # VTK source nightly date
        vnd = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', vsv).group(1)
        vvs = '%s (%s: %s)' % (vtk.vtkVersion.GetVTKVersion(), vnd,
                               VTK_VERSION_EXTRA)

        # if applicable, let's make an ITK version string
        ivs = ''
        if self.mainConfig.useInsight:
            # let's hope McMillan doesn't catch this one!
            itk = __import__('fixitk')
            isv = itk.itkVersion.GetITKSourceVersion()
            ind = re.match('.*Date: ([0-9]+/[0-9]+/[0-9]+).*', isv).group(1)
            ivs = '%s (%s: %s)' % (itk.itkVersion.GetITKVersion(), ind,
                                   ITK_VERSION_EXTRA)
        else:
            ivs = 'N/A'

        about.htmlWindow.SetPage(aboutText % (DEVIDE_VERSION,
                                              wx.VERSION_STRING,
                                              pyver,
                                              vvs, ivs))

        ir = about.htmlWindow.GetInternalRepresentation()
        ir.SetIndent(0, wx.html.HTML_INDENT_ALL)
        about.htmlWindow.SetSize((ir.GetWidth(), ir.GetHeight()))

        about.GetSizer().Fit(about)
        about.GetSizer().SetSizeHints(about)
        about.Layout()

        about.CentreOnParent(wx.BOTH)
        about.ShowModal()
        about.Destroy()

    def exitCallback(self, event):
        self.quit()

    def _handlerMenuGraphEditor(self, event):
        self.startGraphEditor()

    def _handlerMenuPythonShell(self, event):
        self.startPythonShell()

    def showMainWindow(self):
        """Make the main window visible and bring it to the front.
        """

        self._mainFrame.Show(True)
        self._mainFrame.Raise()

    def _windowIconizeAllChildren(self):
        children = self._mainFrame.GetChildren()

        for w in children:
            try:
                if w.IsShown() and not w.IsIconized():
                    try:
                        w.Iconize()

                    except wx.PyAssertionError:
                        # we get this if it's not created yet
                        pass

            except AttributeError:
                # it's a panel for instance
                pass
            

    def _windowRestoreAllChildren(self):
        children = self._mainFrame.GetChildren()

        for w in children:
            
                try:
                    # we don't want to attempt to restore things that are
                    # hidden... only iconized
                    if w.IsShown() and w.IsIconized():
                        try:
                            w.Restore()
                            # after a restore, we have to do a show,
                            # or windows go crazy under Weendows.
                            w.Show()

                        except wx.PyAssertionError:
                            # this is usually "not implemented" on gtk, so we
                            # do an ugly work-around: store the window
                            # position, hide it, show it, reposition it -
                            # this even works under KDE
                            p = w.GetPosition() 
                            w.Hide()
                            w.Show()
                            w.SetPosition(p)
                            
                
                except AttributeError:
                    # panels and stuff simply don't have this method
                    pass
            

	
# ---------------------------------------------------------------------------

def postWxInitImports():
    """AFTER we've started the GUI and performed all pre-imports, this method
    makes sure that all other dependencies are imported into the module
    namespace.  We want these imports here, else the pre-imports can't do
    their thing.
    """
    
    global assistants, graphEditor, moduleManager, pythonShell, helpClass
    global vtk, vtkdevide
    
    from assistants import assistants
    from graphEditor import graphEditor
    from moduleManager import moduleManager
    from pythonShell import pythonShell
    from helpClass import helpClass

    import vtk
    import vtkdevide
    
def main():
    devide_app = devide_app_t()
    devide_app.MainLoop()

if __name__ == '__main__':
    main()
    
