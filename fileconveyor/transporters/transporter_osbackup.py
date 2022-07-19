from .transporter import *
from .osbackup import OSBackup
import os
import pathlib
from django.conf import settings
#from django.core.files.storage import FileSystemStorage
#from storages.backends.symlinkorcopy import SymlinkOrCopyStorage


TRANSPORTER_CLASS = "TransporterOSBackup"

class TransporterOSBackup(Transporter):


    name              = 'OSBackup'
    valid_settings    = frozenset(["location", "url", "symlinkWithin"])
    required_settings = frozenset(["location"])


    def __init__(self, settings, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, settings, callback, error_callback, parent_logger)

         
        self.xsaver = OSBackup( OSBackup.ALGORITHM.MTIME )
        self.xsaver.set_algorithm( OSBackup.ALGORITHM.MTIME ) 
    
    def run(self):
    
    
        while not self.die:
            # Sleep a little bit if there's no work.
            if self.queue.qsize() == 0:
                time.sleep(0.5)
            else:
                self.lock.acquire()
                (src, dst, action, callback, error_callback) = self.queue.get()
                self.lock.release()

                     
                self.logger.debug("Running the transporter '%s' to sync '%s'." % (self.name, src))
                try:
                    # Sync the file 
                        
                    spath = pathlib.Path( src ) 
                    dpath = pathlib.Path( self.settings['location'] ).joinpath( dst ) 
                    
                    print( f'>>> backup {spath} to {dpath} '  
                    self.xsaver.backup_file( action,spath, dpath ) 
                    
                    #if action == Transporter.ADD_MODIFY:
                    #    url = dpath.as_uri()
                    #else :
                    #    url = None 

                    self.logger.debug("The transporter '%s' has synced '%s'." % (self.name, src))

                    # Call the callback function. Use the callback function
                    # defined for this Transporter (self.callback), unless
                    # an alternative one was defined for this file (callback).
                    if not callback is None:
                        callback(src, dst, url, action)
                    else:
                        self.callback(src, dst, url, action)

                except Exception as e:
                    self.logger.error("The transporter '%s' has failed while transporting the file '%s' (action: %d). Error: '%s'." % (self.name, src, action, e))

                    # Call the error_callback function. Use the error_callback
                    # function defined for this Transporter
                    # (self.error_callback), unless an alternative one was
                    # defined for this file (error_callback).
                    if not callback is None:
                        error_callback(src, dst, action)
                    else:
                        self.error_callback(src, dst, action)



