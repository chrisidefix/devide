"""InsightToolkit support module to help load its packages."""
import sys,os

# Get the path to the directory containing this script.  It may be
# used to set pkgdir below, depending on how this script is
# configured.
if __name__ == '__main__':
    selfpath = os.path.abspath(sys.path[0] or os.curdir)
else:
    selfpath = os.path.abspath(os.path.dirname(__file__))

# The directory containing the binary ITK python wrapper libraries.
pkgdir = '/home/cpbotha/DoNotBackup/build/Insight-gcc/bin'

# Python "help(sys.setdlopenflags)" states:
#
# setdlopenflags(...)
#     setdlopenflags(n) -> None
#     
#     Set the flags that will be used for dlopen() calls. Among other
#     things, this will enable a lazy resolving of symbols when
#     importing a module, if called as sys.setdlopenflags(0) To share
#     symbols across extension modules, call as
#
#     sys.setdlopenflags(dl.RTLD_NOW|dl.RTLD_GLOBAL)
#
# GCC 3.x depends on proper merging of symbols for RTTI:
#   http://gcc.gnu.org/faq.html#dso
#

def preimport():
  """Called by InsightToolkit packages before loading a C module."""
  # Save the current dlopen flags and set the ones we need.
  try:
    import dl
    flags = sys.getdlopenflags()
    sys.setdlopenflags(dl.RTLD_NOW|dl.RTLD_GLOBAL)
  except:
    flags = None
  # Save the current working directory and change to that containing
  # the python wrapper libraries.  They have '.' in their rpaths, so
  # they will find the libraries on which they depend.
  cwd = os.getcwd()
  os.chdir(pkgdir)
  # Add the binary package directory to the python module search path.
  sys.path.insert(1, pkgdir)
  return [cwd, flags]

def postimport(data):
  """Called by InsightToolkit packages after loading a C module."""
  # Remove the binary package directory to the python module search path.
  sys.path.remove(pkgdir)
  # Restore the original working directory.
  os.chdir(data[0])
  # Restore the original dlopen flags.
  try:
    sys.setdlopenflags(data[1])
  except:
    pass
