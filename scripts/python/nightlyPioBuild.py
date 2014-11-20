import abc
import os
import platform
import sys
import datetime
import subprocess
import shlex
#~# NCAR based imports here
lib_path = os.path.join('scripts/python/contrib/unit_testing')
sys.path.append(lib_path)
from machine_setup import get_machine_name
#import buildPio

""" stand alone python script that is called from a cron job.
   1) makes directory in /scratch/cluster/nightlyPioBuild with the current
      date and time
   2) checks out the repository
   3) checks if this file is up to date
   4) runs tests on specificed compilers
   5) sends test to list of developers
"""

class nightlyBuilder(object):
   __metaclass__ = abc.ABCMeta
   """ deals with builds and running tests every night at midnight
   """

   def runNightly(self):
      """ routine where everything gets kicked off from
      """
      self.platform = get_machine_name()

      self.setup()
      self.svnCO()
      self.runBuild()
      self.reporting()
      self.mailer()
 

   def setup(self):
      """ setup base information
      """
      #self.buildDir='/scratch/cluster/nightlyPioBuild'

      self.dirName=datetime.datetime.now().strftime("%a%b%d%H%M%S")
      self.repoName='pio2_0'

      self.url='http://parallelio.googlecode.com/svn/branches/pio2_0'
      self.machurl = 'https://svn-ccsm-models.cgd.ucar.edu/Machines/trunk/'

      if self.platform == "goldbach":
         self.compilers = ['intel','nag']
         self.subject='Nightly Build: pio 2.0 - '+self.platform
         self.buildDir='/home/jedwards/nightlyPioBuild'
         self.python = '/usr/local/anaconda-2.0.1/bin/python'
      if self.platform == "yellowstone":
         self.compilers = ['intel','pgi','gnu']
         self.subject='Nightly Build: pio 2.0 - '+self.platform
         self.buildDir='/glade/scratch/jedwards/nightlyPioBuild'
         self.python = '/glade/apps/opt/python/2.7.7/gnu-westmere/4.8.2/bin/python'
      os.chdir(self.buildDir)
      os.mkdir(self.dirName)
      os.chdir(self.dirName)
   
      self.halfPath = self.buildDir+'/'+self.dirName+'/'



   def svnCO(self):
      """ deal with checkouts
      """
      #~# check out the pio 2.0 repo
      #~# don't use pysvn since it's not standard
      self.cmd = ['svn','co',self.url]
      proc = subprocess.Popen(self.cmd,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
      out, err = proc.communicate()
      self.svnLog = out + err
      os.chdir(self.repoName)
      # Checkout the machines directory
      self.cmd = ['svn','co',self.machurl, 'Machines']
      proc = subprocess.Popen(self.cmd,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
      out, err = proc.communicate()
      self.svnLog += out + err

   def runBuild(self):
      """ kick of the builds and tests
      """
      #~# couldn't call buildPio as an import and capture stdout
      #~# using subprocess instead
      self.outTest=''
      for comp in self.compilers:
         print os.environ
         args = shlex.split(self.python + ' scripts/python/buildPio.py --compiler '+comp
                     +'  --mach '+self.platform+' --xmlpath Machines --test')
         print(args)
         proc = subprocess.Popen(args,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
         out,err = proc.communicate() 
         if err == None:
            self.outTest += out 
         else:
            self.outTest += out + err


   def reporting(self):
      """ set up messages for email as well as hard copy.
         We want a hard copy in case the mailer fails, then
         at least we'll have something in the test dir
      """

      #~#self.addr='muszala@ucar.edu stefan.muszala@gmail.com jedwards@ucar.edu jayshkrishna@gmail.com'
      self.addr='jedwards@ucar.edu '
      self.messageFoo=self.halfPath+'toSend.txt'

      #~# want to dump file in case mailer fails so we still have a recor
      f = open(self.messageFoo, 'w')
      f.write('Testing Pio 2.0 nightly build\n\n')
      f.write('\n\n === START svn checkout ===\n\n')
      f.write(self.svnLog)
      f.write('\n\n === DONE svn checkout ===\n\n')
      f.write('\n\n === START builds ===\n\n')
      f.write(self.outTest)
      f.write('\n\n === DONE builds ===\n\n')
      f.close()

      f=open(self.messageFoo, 'r')
      self.fullMessage = f.read()
      f.close()


   def mailer(self):
      """
      """
#      self.readBody = subprocess.Popen(["/bin/echo", self.fullMessage],
#                                      stdout=subprocess.PIPE)

#      mail = subprocess.Popen(["/bin/mail", "-s", self.subject, self.addr],
#                              stdin=self.readBody.stdout, stdout=subprocess.PIPE)


def main(argv):
   """ everything starts here
   """
   nb = nightlyBuilder()
   nb.runNightly()

if __name__ == "__main__":
   main(sys.argv[1:]) 