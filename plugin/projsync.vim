

let s:scriptroot=expand('<sfile>:p:h')

if !has('python')
	finish
	echo "Your version of vim does not support python"
else
	execute 'pyfile ' .   s:scriptroot . '/projsync.py'
	py import logging
	py logging.basicConfig( lv=20 )
endif



"" Command Map
""

function! ProjSyncPushFile()
	py ProjSync().push_file()
endfunc

function! ProjSyncSync()
	py ProjSync().sync_all()
endfunc

function! ProjSyncClear()
	py ProjSync().clear()
endfunc


