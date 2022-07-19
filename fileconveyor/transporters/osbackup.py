import pathlib
import shutil
import filecmp 
class OSBackup():

    """ uses os copies to back up file changes to an os accesable 
        directory.  we start off with the actions required for a 
        single file.  

        eventually  this class will be generalised to support 
        different types of file storage 

        encryption is  NOT applied 
        
        The following algorithms can be applied:- 
        
        1) for new or changed source files (addmodify)
        
        LAST  copies name.ext to name.ext overwriting if necessary
        FIRST ditto but errors if file exists
        other 
            renames any existing backup file according to algorithm 
            performs the copy
            purges the old copies 
            
            
        2) deleted file in source

        LAST  deletes file in dest 
        FIRST leaves any file 
        other renames any existing file according to algorithm 

        3) if the destination directory does not exist we attempt
        to create it (this can fail if a file with that name exists)
        
        4) Presently action for Symlinks is not  specified 
           but copies will specify that they  are not to be followed
           
        5) A variety of purge algorithms will be developed
           e.g. last n, monthly, weekly, daily, snapshots etc
           
        
    """

    class ACTIONS :
        ADD_MODIFY = 0x00000001
        DELETE     = 0x00000002
        ALL = ( ADD_MODIFY, DELETE)
    
    
    class ALGORITHM:
        FIRST  =  "FIRST" 
        LAST   =  "LAST" 
        MTIME  =  "MTIME" 
        MD5    =  "MD5" 
        RANDOM =  "RAND"  
        ANY = [FIRST, LAST, MTIME, MD5, RANDOM]
        PATTERN = { MTIME : '.*@[\d]{10}\.{0,1}[.]*', RANDOM : '.*@[\d]{7}\.{0,1}[.]*' }
        
    USEP='@' 
        

    def __init__(self,algorithm) :
    
        self.algorithm = self.ALGORITHM.MTIME
        
        self.set_algorithm( algorithm )
        
        
        # xxx.not_exists() always seems to read better than not xxx.exists() 
        not_exists = lambda self: not self.exists()
        pathlib.Path.not_exists = not_exists
    
    def set_algorithm( self,algorithm ) :
    
        if algorithm is None :
            pass
        elif algorithm in self.ALGORITHM.ANY:
            self.algorithm = algorithm
        else :
            raise ValueError( 'Invalid algorithm passed to backup {algorithm}' ) 
    
    def resolve(self, path) :
        # replaces path - perhaps we should test for a tilda and wild cards also
        path = pathlib.Path(path).resolve() 
        return path
        
    def backup(self,action,source,destination,algorithm=None):
    
        # source is a file
        #    if dest is a directory - append name
        #    backup_file
        # 
        # source is a directory 
        #    check that dest is a directory
        #    check options
        #    process dir
        raise NotImplementedError
   
    
    
    def backup_dir( self, source, destination, algorithm=None, with_deletes=False ) :
           
        
        # FIRST   - does adds but not mods or delete
        # LAST    = does adds, mods and deletes 
        # other   - does adds, mods and deletes but retains old copies 
        #  perhaps we need to deal with funny files - say to report them 
        
             
        source = self.resolve(source) 
        destination = self.resolve(destination) 
        self.set_algorithm( algorithm )     

           
        comparison = filecmp.dircmp( source , destination ) 
     
        action = self.ACTIONS.ADD_MODIFY
        for new in comparison.left_only :
            source_file = source.joinpath(new) 
            destination_file = destination.joinpath(new) 
            self.backup_file(action,source_file,destination_file)
            
        if self.algorithm != self.ALGORITHM.FIRST :
            return 
        
        action = self.ACTIONS.ADD_MODIFY
        for mod in comparison.diffs :
            source_file = source.joinpath(mod) 
            destination_file = destination.joinpath(mod) 
            self.backup_file(action,source_file,destination_file)
            
        action = self.ACTIONS.DELETE
        for name in comparison.right_only  :
            source_file = source.joinpath(name) 
            destination_file = destination.joinpath(name) 
            self.backup_file(action,source_file,destination_file)
            
        
    def backup_file(self,action,source,destination,algorithm=None):
    
        # deal with existing file
        # create dir if it does not exist
        # perform file action
        
        if action not in self.ACTIONS.ALL :
             raise ValueError( 'Invalid action passed to backup {algorithm}' ) 
             
        source = self.resolve(source) 
        destination = self.resolve(destination) 
        self.set_algorithm( algorithm )     
       
        
        # deal with existing file
        
        if   (action == self.ACTIONS.ADD_MODIFY ) and  (not destination.exists() ):
            pass # continue to copy
        elif (action==self.ACTIONS.DELETE ) and ( not destination.exists() ):
            return None # no action required
        elif (action==self.ACTIONS.DELETE ) and ( self.algorithm==self.ALGORITHM.FIRST):
            return None # leave the first
        elif (self.algorithm==self.ALGORITHM.FIRST):
            message = "File {} exists and copy only FIRST specified".format(destination)
            raise FileExistsError(message) 
        elif (self.algorithm==self.ALGORITHM.LAST):
            pass # continue to copy
        else :
            self.rename(destination,self.algorithm)  
                
        # create dir if it does not exist

        location = destination.parent
        
        if location.is_dir() :
            pass 
        elif location.exists():
            message = f'Destination {location} exists and is not a directory'
            raise FileExistsError( message )
        else :
            location.mkdir(parents=True, exist_ok=True) 
            
        assert location.is_dir()
        
        # now copy / delete the file 
        if   (action == self.ACTIONS.ADD_MODIFY ) :
            shutil.copy2( source, destination, follow_symlinks=False ) 
        else :
            destination.unlink()
        
        # purge excessive backup versions

        #self.purge() :
        
    
    def rename(self,destination,convention) :
    
        replace = True 
        
        if convention==self.ALGORITHM.MTIME :
            
            mtime = destination.lstat().st_mtime
            mpart = str(int(mtime))
            
        elif  convention==self.ALGORITHM.MD5 :
        
            mpart = self.md5( destination )
            
        elif  convention==self.ALGORITHM.MD5 :
        
            mpart = self.rand( )

        
        mname = destination.stem + self.USEP + str(int(mtime)) + destination.suffix 
        new_destination = destination.with_name( mname ) 
        
        try:
            result = destination.rename( new_destination )
        except FileNotFoundError :
            message = f'FileNotFoundError renaming {destination} to {new_destination}'
            raise FileExistsError( message )
        except FileExistsError:
        
            # this should prevent deleting the 'from' file 
            if destination.samefile( new_destination ) :
                message = f'FileExistsError renaming {destination} to {new_destination} they are same file'
                raise FileExistsError( message )
                
            elif replace or filecmp.cmp( destination , new_destination  , shallow=False ) :
                result = destination.replace( new_destination )
                
            else:
                message = f'FileExistsError renaming {destination} to {new_destination}'
                raise FileExistsError( message )
   
        
    
    def purge(self):
        pass

    def rand(self) :
        import uuid
        ustr = uuid.uuid4() 
        return  ustr[-7:] 
    
    def md5( self, filename ):
        """compute the md5 hash of the specified file"""
        m = hashlib.md5()
        try:
            f = open(filename, "rb")
        except IOError:
            raise FileIOError("Unable to open the file in readmode: %s" % (filename))

        line = f.readline()
        while line:
            m.update(line)
            line = f.readline()
        f.close()
        return m.hexdigest()

    def sha1(self, filepath):
        hasher = hashlib.sha1()
        with open(filepath, 'rb') as f:
            buf = f.read(1048576)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(1048576)
        return hasher.hexdigest()

if __name__ == "__main__" :

    import time

    # first test using local disk 
    saver = OSBackup( OSBackup.ALGORITHM.MTIME )
    saver.set_algorithm( saver.ALGORITHM.MTIME ) 
    
    sdir = "c:\\users\\Chris Johnson\\temp\\" 
    ddir =  "c:\\users\\Chris Johnson\\btemp\\" 
    
    testname = "ruggish.dat"
    
    spath = pathlib.Path(sdir).joinpath(testname) 
    dpath = pathlib.Path(ddir).joinpath(testname)
    
    spath.write_text( 'initial test data ' ) 
    
    
    saver.backup_file( saver.ACTIONS.ADD_MODIFY,spath, dpath ) 
    
    time.sleep(3)
    
    spath.write_text( 'modified  test data ' ) 
    
    
    for f in dpath.parent.glob('*')  :
        print( f ) 

    
    saver.backup_file( saver.ACTIONS.ADD_MODIFY,spath, dpath ) 
    
    input( 'continue with dir backup ' ) 
    saver.backup_dir( sdir , ddir ) 



