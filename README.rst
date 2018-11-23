
vim-projsync:
=============

Configures vim to mirror saves to other locations. I use this to allow me to
work within a linux VM while writing code targeting windows. Duplicating files 
immediately on save helps keep modify/execute cycles fast enough to be practical.

I highly recommend supplementing this with something like lsyncd_ to catch branch
changes. 

.. _lsyncd: https://github.com/axkibe/lsyncd


Install:
--------

.. code-block:: vim

    " Using Vundle,
    :Plugin 'https://github.com/willjp/vim-projsync'
    :PluginUpdate



Usage:
------

After configuring your settings using a `projsync.json` file

* ``:ProjSyncEnable`` to activate mirroring for this vim session
* save a file within one of your configured projects. 


Commands:

.. code-block:: vim

    :ProjSyncEnable    " activates file-save hook
    :ProjSyncDisable   " disables file-save hook
    :ProjSyncPushFile  " copy current vim buffer to configured paths
    :ProjSyncSync      " copy entire git-repo above vm buffer to configured paths


Requires:
---------

Your vim must be compiled with python. Check for ``+python`` in the output of command ``vim --version`` .


Configuration
-------------

Global configuration is read from ``~/.vim/projsync.json`` . You can also drop a
``.projsync.json`` file any where in your target-file's parent hierarchy. The configuration
is cumulative.


Example Global Config: `~/.vim/projsync.json`

.. code-block:: javascript

    {
        "Test Project": {
            "gitroot" :   "~/dev",                          // root of your git-project (copy files relative to here)
            "hostnames":  ["*-work", "*-dev"],              // hostname matches
            "copy_paths": ["/devsync/test", "/mnt/backup"]  // where to mirror saves to
        },
        "WORK scripts": {
            "gitroot" :   "~/progs/maya2014",
            "hostnames":  ["dev-vm-work-*"],
            "copy_paths": ["/devsync/m2014"]
        }
    }


Example Local Config: `/home/dev/work/gui/.projsync.json`


.. code-block:: javascript

    // local configs do not require ``gitroot` key. 
    // (gitroot is determined by checking parent directories)

    {
        "project C": {
            "hostnames":  ["*-work", "*-dev"],              // hostname matches
            "copy_paths": ["/devsync/test", "/mnt/backup"]  // where to mirror saves to
        }
    }



More Info
----------

There is additional info in the vim-helpfile. See ``:help projsync`` .


