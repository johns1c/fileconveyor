from fileconveyor.transporters import *
import os
from django.conf import settings
#from django.core.files.storage import FileSystemStorage
#from storages.backends.symlinkorcopy import SymlinkOrCopyStorage


TRANSPORTER_CLASS = "TransporterSymlinkOrCopy"

#from storages.compat import FileSystemStorage
__doc__ = """
I needed to efficiently create a mirror of a directory tree (so that
"origin pull" CDNs can automatically pull files). The trick was that
some files could be modified, and some could be identical to the original.
Of course it doesn't make sense to store the exact same data twice on the
file system. So I created SymlinkOrCopyStorage.

SymlinkOrCopyStorage allows you to symlink a file when it's identical to
the original file and to copy the file if it's modified.
Of course, it's impossible to know if a file is modified just by looking
at the file, without knowing what the original file was.
That's what the symlinkWithin parameter is for. It accepts one or more paths
(if multiple, they should be concatenated using a colon (:)).
Files that will be saved using SymlinkOrCopyStorage are then checked on their
location: if they are within one of the symlink_within directories,
they will be symlinked, otherwise they will be copied.

The rationale is that unmodified files will exist in their original location,
e.g. /htdocs/example.com/image.jpg and modified files will be stored in
a temporary directory, e.g. /tmp/image.jpg.
"""

import shutil
import os

class OSCopyStorage():   # was FileSystemStorage):
    """Stores symlinks to files instead of actual files whenever possible

    When a file that's being saved is currently stored in the symlink_within
    directory, then symlink the file. Otherwise, copy the file.
    """

    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL,
            overwrite=settings.overwrite):
            
        self.overwrite = True if overwrite else False 

    def _save(self, name, content):
        """ mimics django.core.files.storage _save
            using shutil.copy2 
            
            this version ignores directory permissions
            but may need use original approach
            
            overwrite=False may not work since delete in caller
        """
        full_path = self.path(name)
        directory = os.path.dirname(full_path)
        
        if pathlib( full_path ).exists() and not self.overwrite :
            raise FileExistsError( "%s exists and overwrite not specified." % full_path )

        # Create any intermediate directories that do not exist.
        # see https://stackoverflow.com/questions/600268
        
        try:
            import pathlib
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True) 
        except FileExistsError:
            raise FileExistsError("%s exists and is not a directory." % directory)
            
        shutil.copy2( content.path , full_path ) 
        # Ensure the saved path is always relative to the storage root.
        
        return full_path.replace( "\\" , "/" )
        
        #name = os.path.relpath(full_path, self.location)
        # Store filenames with forward slashes, even on Windows.
        #return str(name).replace("\\", "/")




class TransporterOSCopy(Transporter):


    name              = 'OSCOPY'
    valid_settings    = frozenset(["location", "url", "symlinkWithin", "overwrite" ])
    required_settings = frozenset(["location", "url", "symlinkWithin"])


    def __init__(self, settings, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, settings, callback, error_callback, parent_logger)

        # Map the settings to the format expected by SymlinkStorage.
        if "overwrite" not in self.settings :
            import pdb
            pdb.set_trace()
            #self.settings( "overwrite" ) = False 
            
        self.storage = OSCopyStorage(self.settings["location"],
                                     self.settings["url"],
                                     self.settings["overwrite"]
                                     
                                            )

