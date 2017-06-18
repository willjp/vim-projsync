
vim-projsync:
=============

Configure vim so that whenever you save a file, it copies that file
preserving it's relative filepath to your project-root, to a variable
number of configurable locations.

Example:

::

    project/src/myfile.txt >> /mnt/myproject_copy/src/myfile.txt
                           >> /var/tmp/myproject_other/src/myfile.txt
    

Recommendation:
---------------

I use this in alongside with `lsyncd` . lsyncd does a 
good job of catching branch-changes, but is a little slow
to catch file changes if you are in a quick modify-run cycle.

Running it in addition to lsyncd means you never need to run
``:ProjSyncSync`` when you change your git branch.



___________

|
|

.. contents:: Table Of Contents

|
|

___________




The Problem:
------------

Summary:
````````

Using git-projects in VirtualBox SharedFolders (or NetworkShares) is slow.  

This is a simple script that allows you to work locally, 
and push changes to a network-shared directory on file-save.


Why I Wrote This:
`````````````````

Unfortunately, the majority of my work is for the Windows platform.
The lack of effective shortcuts, window-management, and the awful
non-resizable, non-multiplexed cmd.exe feels clumsy, and aggravating.

After experimenting for a few years with various combinations of
the following *amazing* projects, 

* AutoHotkey
* cygwin
* msys
* msys2
* git-bash
* ConEmu
* clink
* bugn
* gVim
* lsyncd


I eventually settled on using a VirtualMachine for development.
It was wonderful. No platform-specific issues or build constraints, 
completely identical setups everywhere, and quickly reproducible 
(see *vagrant* and *saltstack*).

To pass information back and forth, I decided to share my 
git source-dirs with the Windows Host using VirtualBox SharedFolders.
That way everything can still be run/compiled etc on the windows host 
itself, in the actual production environment.


.. But then ..

The performance of git when working within the shared folder was totally
crippled. It was completely unusable.

This plugin is my workaround. I now work locally, and keep various
shared folders in `/mnt/`. If I am in a project that has configured
projsync folder(s), every time that I save the file gets pushed to
the shared folder right away.

    ex:
    `/home/dev/myproj/.git`              >>  `/mnt/devsync/my_proj/`
    `/home/dev/myproj/ docs/README.rst`  >>  `/mnt/devsync/my_proj/ docs/README.rst`






Dependencies:
-------------

vim compiled with:

::
    +python


programs

::
    git




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

The core idea is that you configure projsync to watch for specific
git-projects. Every time that a file is saved, it's path is searched
for it's git project's root. 

If the file's git project matches one of your configured paths,
after the file is saved, it the file will be copied to each of the configured
locations.



Config Locations
................

The config attempting to be a middleground between git, and vim.
There are 2x places that the projsync config will be searched for:

Global configuration:
`````````````````````

Your main config: ``~/.vim/projsync.json``


Local configuration:
````````````````````

If you're just testing things out, or need
special behaviour under a subdirectory of a git
project.


.. code-block:: bash

    /path/to/myfile/myfile.py        ## your file
    /path/to/projsync.json           ## local projsync config
    /path/to/.projsync.json          ## local projsync config (hidden)







Config Format
.............

There are 2x types of configs, global and local.
You can use either configuration type, or both.
The main difference is:

- global configs defines project-names/git-projects to match against.

- local configs assume you are in the correct project, there are no
  projectname or gitroot fields.



Examples
````````

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


Configuration Keys
``````````````````

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


