
vim-projsync:
=============

Mirror git-projects to a second location, triggering a copy on every save.
I recommend using this alongside something like `lsyncd` to catch/synchronize 
branch changes.

Example:

::

    /src/.git
        /src/project/myfile.txt  -> /dst/project/myfile.txt
    
I like to use vim within linux even while developing for windows. This
script lets me have a quick modify/execute cycle, like I was working
directly in windows.


Usage:
------

After a configuration is created, and ``:ProjSyncEnable`` is run,
all you need to do is save your file. It will be copied automatically
to all configured copypaths.

Other Commands:

.. code-block:: vim

    :ProjSyncEnable    " activates projsync, hooks on file-save will be activated
    :ProjSyncDisable   " disabled projsync, hooks on file-save will be disactivated
    :ProjSyncPushFile  " copy the current file to all configured locations
    :ProjSyncSync      " delete all files in configured locatin, and recopy fresh copies of all files



Configuration
-------------

Configuration is checked for in any subdirectory of a git project, (more specific takes precedence),
falling back on  ``~/.vim/projsync.json`` .


Examples
.........

Example Global Config: `~/.vim/projsync.json`

.. code-block:: json

    {
        "Test Project" :{
            "gitroot" :      "~/dev",
            "hostnames":     ["*"],
            "copy_paths": [
                        { "method":"copy", "path":"/devsync/test" },
                        { "method":"copy", "path":"/devsync/test" }
                    ]
        },
        "WORK scripts" :{
            "gitroot" :      "~/progs/maya/m2014",
            "hostnames":     ["dev-vm-work-*"],
            "copy_paths": [
                        { "method":"copy", "path":"/devsync/work/scripts" }
                    ]
        }
    }



Example Local Config: `/home/dev/work/gui/.projsync.json`

.. code-block::

    {
        "hostnames":  ["dev-vm-work-*"],
        "copy_paths": [
                        { "method":"copy", "path":"/devsync/work/scripts" }
                    ]
    }


Config Keys
...........

* `gitroot`: The root directory of the git project you ar synchronizing.
             (the directory containing your .git/ directory).
              Paths will be recreated from here in your copy_path directories.

              ex:

              ::

                  /home/dev/myproject/.git

                  /home/dev/myproject/ gui/menus/mymenu.py 
                  >> copied to >>
                  /sync_location/ gui/menus/mymenu.py


* `hostnames`:  A list of python fnmatch matches of hostnames.
                The file is only copied if your host matches an entry here.
                See the following link for syntax:
                https://docs.python.org/2/library/fnmatch.html?highlight=fnmatch#module-fnmatch


* `copy_paths`: A list of dictionaries that define how and where to copy the saved
                file to. 2x keys are required:

                    * `method`:  determines how the file is copied. currently only *copy*
                                 is valid.

                    * `path`:    determines where the file is copied to


More Info
----------

There is additional info in the vim-helpfile. See ``:help projsync`` .


