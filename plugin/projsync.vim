
"" Plugin Init
""
let s:scriptroot=expand('<sfile>:p:h')

if !has('python')
    finish
    echo "Your version of vim does not support python"
else
    " execute 'pyfile ' .   s:scriptroot . '/projsync2.py'
    py import sys
    py import logging
    py logging.basicConfig(lv=20)
    execute 'py if "' . s:scriptroot . '" not in sys.path: sys.path.append("' . s:scriptroot . '")'
    py import projsync2
endif




"" Command Map
""

function! ProjSyncEnable()
    " Enable Automatic ProjSyncPushFile on every file-save
    "
    autocmd BufWritePost * call ProjSyncPushFile()
endfunc
command! ProjSyncEnable call ProjSyncEnable()



function! ProjSyncDisable()
    " Disable Automatic ProjSyncPushFile on every file-save
    " 
    autocmd! BufWritePost * call ProjSyncPushFile()
endfunc
command! ProjSyncDisable call ProjSyncDisable()



function! ProjSyncPushFile()
    " Copy current file to all configured locations
    " 
    py projsync2.sync_file()
endfunc
command! ProjSyncPushFile call ProjSyncPushFile()



function! ProjSyncSync()
    " Delete all files in all configured locations,
    " then recopy fresh copies of all files.
    " ( should be done after a `git checkout` )
    "
    py projsync2.sync_gitroot()
endfunc
command! ProjSyncSync call ProjSyncSync()

