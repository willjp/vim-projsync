
if !has('python')
	finish
	echo "Your version of vim does not support python"
else
	pyfile main.py
	py import logging
	py logging.basicConfig( lv=20 )
endif


function! ProjSync()
	py ProjSync()
endfunc

