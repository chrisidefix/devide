#!/usr/bin/env python

# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import re
import getopt
import mutex
import os
import re
import stat
import string
import sys
import time
import traceback
import ConfigParser

# we need to import this explicitly, else the installer builder
# forgets it and the binary has e.g. no help() support.
import site


dev_version = False
try:
    # devide_versions.py is written by johannes during building DeVIDE distribution
    import devide_versions

except ImportError:
    dev_version = True

else:
    # check if devide_version.py comes from the same dir as this devide.py
    dv_path = os.path.abspath(os.path.dirname(devide_versions.__file__))
    d_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    if dv_path != d_path:
        # devide_versions.py is imported from a different dir than this file, so DEV
        dev_version = True

if dev_version:
    # if there's no valid versions.py, we have these defaults
    # DEVIDE_VERSION is usually y.m.d of the release, or y.m.D if
    # development version
    DEVIDE_VERSION = "12.3.D"
    DEVIDE_REVISION_ID = "DEV"
    JOHANNES_REVISION_ID = "DEV"

else:
    DEVIDE_VERSION = devide_versions.DEVIDE_VERSION
    DEVIDE_REVISION_ID = devide_versions.DEVIDE_REVISION_ID
    JOHANNES_REVISION_ID = devide_versions.JOHANNES_REVISION_ID


############################################################################
class MainConfigClass(object):

    def __init__(self, appdir):

        # first need to parse command-line to get possible --config-profile
        # we store all parsing results in pcl_data structure
        ##############################################################
        pcl_data = self._parseCommandLine()

        config_defaults = {
                'nokits': '', 
                'interface' : 'wx',
                'scheduler' : 'hybrid',
                'extra_module_paths' : '',
                'streaming_pieces' : 5,
                'streaming_memory' : 100000}

        cp = ConfigParser.ConfigParser(config_defaults)
        cp.read(os.path.join(appdir, 'devide.cfg'))
        CSEC = pcl_data.config_profile

        # then apply configuration file and defaults #################
        ##############################################################
        nokits = [i.strip() for i in cp.get(CSEC, \
                'nokits').split(',')]
        # get rid of empty strings (this is not as critical here as it
        # is for emps later, but we like to be consistent)
        self.nokits = [i for i in nokits if i]

        self.streaming_pieces = cp.getint(CSEC, 'streaming_pieces')
        self.streaming_memory = cp.getint(CSEC, 'streaming_memory')

        self.interface = cp.get(CSEC, 'interface') 

        self.scheduler = cp.get(CSEC, 'scheduler')

        emps = [i.strip() for i in cp.get(CSEC, \
                'extra_module_paths').split(',')]
        # ''.split(',') will yield [''], which we have to get rid of
        self.extra_module_paths = [i for i in emps if i]

        # finally apply command line switches ############################
        ##################################################################

        # these ones can be specified in config file or parameters, so
        # we have to check first if parameter has been specified, in
        # which case it overrides config file specs
        if pcl_data.nokits:
            self.nokits = pcl_data.nokits

        if pcl_data.scheduler:
            self.scheduler = pcl_data.scheduler

        if pcl_data.extra_module_paths:
            self.extra_module_paths = pcl_data.extra_module_paths

        # command-line only, defaults set in PCLData ctor
        # so we DON'T have to check if config file has already set
        # them
        self.interface = pcl_data.interface
        self.stereo = pcl_data.stereo
        self.test = pcl_data.test
        self.script = pcl_data.script
        self.script_params = pcl_data.script_params
        self.load_network = pcl_data.load_network
        self.hide_devide_ui = pcl_data.hide_devide_ui

        # now sanitise some options
        if type(self.nokits) != type([]):
            self.nokits = []

    def dispUsage(self):
        self.disp_version()
        print ""
        print "-h or --help          : Display this message."
        print "-v or --version       : Display DeVIDE version."
        print "--version-more        : Display more DeVIDE version info."
        print "--config-profile name : Use config profile with name."
        print "--no-kits kit1,kit2   : Don't load the specified kits."
        print "--kits kit1,kit2      : Load the specified kits."
        print "--scheduler hybrid|event"
        print "                      : Select scheduler (def: hybrid)"
        print "--extra-module-paths path1,path2"
        print "                      : Specify extra module paths."
        print "--interface wx|script"
        print "                      : Load 'wx' or 'script' interface."
        print "--stereo              : Allocate stereo visuals."
        print "--test                : Perform built-in unit testing."
        print "--script              : Run specified .py in script mode."
        print "--load-network        : Load specified DVN after startup."
        print "--hide-devide-ui      : Hide the DeVIDE UI at startup."

    def disp_version(self):
        print "DeVIDE v%s" % (DEVIDE_VERSION,)

    def disp_more_version_info(self):
        print "DeVIDE rID:", DEVIDE_REVISION_ID 
        print "Constructed by johannes:", JOHANNES_REVISION_ID

    def _parseCommandLine(self):
        """Parse command-line, return all parsed parameters in
        PCLData class.
        """

        class PCLData:
            def __init__(self):
                self.config_profile = 'DEFAULT'
                self.nokits = None
                self.interface = None
                self.scheduler = None
                self.extra_module_paths = None
                self.stereo = False
                self.test = False
                self.script = None
                self.script_params = None
                self.load_network = None
                self.hide_devide_ui = None

        pcl_data = PCLData()

        try:
            # 'p:' means -p with something after
            optlist, args = getopt.getopt(
                sys.argv[1:], 'hv',
                ['help', 'version', 'version-more', 'no-kits=', 'kits=', 'stereo', 'interface=', 'test',
                 'script=', 'script-params=', 'config-profile=',
                 'scheduler=', 'extra-module-paths=', 'load-network='])
            
        except getopt.GetoptError,e:
            self.dispUsage()
            sys.exit(1)

        for o, a in optlist:
            if o in ('-h', '--help'):
                self.dispUsage()
                sys.exit(0)

            elif o in ('-v', '--version'):
                self.disp_version()
                sys.exit(0)

            elif o in ('--version-more',):
                self.disp_more_version_info()
                sys.exit(0)

            elif o in ('--config-profile',):
                pcl_data.config_profile = a

            elif o in ('--no-kits',):
                pcl_data.nokits = [i.strip() for i in a.split(',')]

            elif o in ('--kits',):
                # this actually removes the listed kits from the nokits list
                kits = [i.strip() for i in a.split(',')]
                for kit in kits:
                    try:
                        del pcl_data.nokits[pcl_data.nokits.index(kit)]
                    except ValueError:
                        pass

            elif o in ('--interface',):
                if a == 'pyro':
                    pcl_data.interface = 'pyro'
                elif a == 'xmlrpc':
                    pcl_data.interface = 'xmlrpc'
                elif a == 'script':
                    pcl_data.interface = 'script'
                else:
                    pcl_data.interface = 'wx'

            elif o in ('--scheduler',):
                if a == 'event':
                    pcl_data.scheduler = 'event'
                else:
                    pcl_data.scheduler = 'hybrid'

            elif o in ('--extra-module-paths',):
                emps = [i.strip() for i in a.split(',')]
                # get rid of empty paths
                pcl_data.extra_module_paths = [i for i in emps if i]

            elif o in ('--stereo',):
                pcl_data.stereo = True

            elif o in ('--test',):
                pcl_data.test = True

            elif o in ('--script',):
                pcl_data.script = a

            elif o in ('--script-params',):
                pcl_data.script_params = a

            elif o in ('--load-network',):
                pcl_data.load_network = a

            elif o in ('--hide-devide-ui',):
                pcl_data.hide_devide_ui = a

        return pcl_data

############################################################################
class DeVIDEApp:
    """Main devide application class.

    This instantiates the necessary main loop class (wx or headless pyro) and
    acts as communications hub for the rest of DeVIDE.  It also instantiates
    and owns the major components: Scheduler, ModuleManager, etc.
    """
    
    def __init__(self):
        """Construct DeVIDEApp.

        Parse command-line arguments, read configuration.  Instantiate and
        configure relevant main-loop / interface class.
        """
        
        
        self._inProgress = mutex.mutex()
        self._previousProgressTime = 0
        self._currentProgress = -1
        self._currentProgressMsg = ''
        
        #self._appdir, exe = os.path.split(sys.executable)
        if hasattr(sys, 'frozen') and sys.frozen:
            self._appdir, exe = os.path.split(sys.executable)
        else:
            dirname = os.path.dirname(sys.argv[0])
            if dirname and dirname != os.curdir:
                self._appdir = os.path.abspath(dirname)
            else:
                self._appdir = os.getcwd()

        sys.path.insert(0, self._appdir) # for cx_Freeze

        # before this is instantiated, we need to have the paths
        self.main_config = MainConfigClass(self._appdir)

        ####
        # startup relevant interface instance
        if self.main_config.interface == 'pyro':
            from interfaces.pyro_interface import PyroInterface
            self._interface = PyroInterface(self)
            # this is a GUI-less interface, so wx_kit has to go
            self.main_config.nokits.append('wx_kit')

        elif self.main_config.interface == 'xmlrpc':
            from interfaces.xmlrpc_interface import XMLRPCInterface
            self._interface = XMLRPCInterface(self)
            # this is a GUI-less interface, so wx_kit has to go
            self.main_config.nokits.append('wx_kit')

        elif self.main_config.interface == 'script':
            from interfaces.script_interface import ScriptInterface
            self._interface = ScriptInterface(self)
            self.main_config.nokits.append('wx_kit')
            
        else:
            from interfaces.wx_interface import WXInterface
            self._interface = WXInterface(self)

        if 'wx_kit' in self.main_config.nokits:
            self.view_mode = False
        else:
            self.view_mode = True
                             

        ####
        # now startup module manager

        try:
            # load up the ModuleManager; we do that here as the ModuleManager
            # needs to give feedback via the GUI (when it's available)
            global module_manager
            import module_manager
            self.module_manager = module_manager.ModuleManager(self)

        except Exception, e:
            es = 'Unable to startup the ModuleManager: %s.  Terminating.' % \
                 (str(e),)
            self.log_error_with_exception(es)

            # this is a critical error: if the ModuleManager raised an
            # exception during construction, we have no ModuleManager
            # return False, thus terminating the application
            return False

        ####
        # start network manager
        import network_manager
        self.network_manager = network_manager.NetworkManager(self)

        ####
        # start scheduler
        import scheduler
        self.scheduler = scheduler.SchedulerProxy(self)
        if self.main_config.scheduler == 'event':
            self.scheduler.mode = \
                    scheduler.SchedulerProxy.EVENT_DRIVEN_MODE
            self.log_info('Selected event-driven scheduler.')

        else:
            self.scheduler.mode = \
                    scheduler.SchedulerProxy.HYBRID_MODE
            self.log_info('Selected hybrid scheduler.')

        ####
        # call post-module manager interface hook

        self._interface.handler_post_app_init()

        self.setProgress(100, 'Started up')

    def close(self):
        """Quit application.
        """

        self._interface.close()
        self.network_manager.close()
        self.module_manager.close()

        # and make 100% we're done
        sys.exit()

    def get_devide_version(self):
        return DEVIDE_VERSION

    def get_module_manager(self):
        return self.module_manager

    def log_error(self, msg):
        """Report error.

        In general this will be brought to the user's attention immediately.
        """
        self._interface.log_error(msg)

    def log_error_list(self, msgs):
        self._interface.log_error_list(msgs)

    def log_error_with_exception(self, msg):
        """Can be used by DeVIDE components to log an error message along
        with all information about current exception.

        """
        
        import gen_utils
        emsgs = gen_utils.exceptionToMsgs()
        self.log_error_list(emsgs + [msg])

    def log_info(self, message, timeStamp=True):
        """Log informative message to the log file or log window.
        """
        
        self._interface.log_info(message, timeStamp)

    def log_message(self, message, timeStamp=True):
        """Log a message that will also be brought to the user's attention,
        for example in a dialog box.
        """
        
        self._interface.log_message(message, timeStamp)

    def log_warning(self, message, timeStamp=True):
        """Log warning message.

        This is not as serious as an error condition, but it should also be
        brought to the user's attention.
        """
        
        self._interface.log_warning(message, timeStamp)

    def get_progress(self):
        return self._currentProgress

    def set_progress(self, progress, message, noTime=False):
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

                    self._interface.set_progress(progress, message, noTime)

            # unset the mutex thingy
            self._inProgress.unlock()

    setProgress = set_progress
        
    def start_main_loop(self):
        """Start the main execution loop.

        This will thunk through to the contained interface object.
        """

        self._interface.start_main_loop()

    def get_appdir(self):
        """Return directory from which DeVIDE has been invoked.
        """
        
        return self._appdir

    def get_interface(self):
        """Return binding to the current interface.
        """
        
        return self._interface
    

############################################################################
def main():
    devide_app = DeVIDEApp()
    devide_app.start_main_loop()
    

if __name__ == '__main__':
    main()
    
