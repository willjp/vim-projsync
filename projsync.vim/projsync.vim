
if !has('python')
	finish
	echo "Your version of vim does not support python"
else
	pyfile ~/progs/vim/projsync.vim/main.py
	py import logging
	py logging.basicConfig( lv=20 )
endif



"" Command Map
""

function! ProjSyncPush()
	py ProjSync().push()
endfunc

function! ProjSyncPushAll()
	py ProjSync().push_all()
endfunc

function! ProjSyncClear()
	py ProjSync().clear()
endfunc


