"!TODO:  user-configure enable 'debug' mode
"!TODO:  functions accept argument 'debug'
"!TODO:  vim-fugitive integration
"!TODO:  system git-checkout hook integration



"" Plugin Init
""
let s:scriptroot=expand('<sfile>:p:h')

if !has('python')
	finish
	echo "Your version of vim does not support python"
else
	execute 'pyfile ' .   s:scriptroot . '/projsync.py'
	py import logging
	py logging.basicConfig(lv=20)
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
	py ProjSync().push_file()
endfunc
command! ProjSyncPushFile call ProjSyncPushFile()



function! ProjSyncSync()
	" Delete all files in all configured locations,
	" then recopy fresh copies of all files.
	" ( should be done after a `git checkout` )
	"
	py ProjSync().sync_all()
endfunc
command! ProjSyncSync call ProjSyncSync()



function! ProjSyncClear()
	" ProjSync stores each file's directory
	" with the filepath to the JSON config, and
	" it's timestamp (so that it is reloaded if changed)
	"
	" If you introduce a new local JSON file, however
	" it will not be read until this command is run
	" or vim is restarted.
	"
	py ProjSync().clear()

endfunc
command! ProjSyncClear call ProjSyncClear()


