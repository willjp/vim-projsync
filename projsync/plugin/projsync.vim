
if !has('python')
	finish
	echo "Your version of vim does not support python"
else
	pyfile ~/progs/vim/projsync.vim/projsync.py
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


