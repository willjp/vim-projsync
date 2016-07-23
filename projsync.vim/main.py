#!/usr/bin/env python2
"""
Name :          mfw_osTest.py
Created :       February 28 2015
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Git-projects can configured to have an action performed
                on their files 
                
________________________________________________________________________________
"""


import vim

import os
import sys
import shlex
import subprocess
import shutil
import json
import logging

logger = logging.getLogger(__name__)


class ProjSync( object ):
	##@ __init__                                                                            #{{{
	############################################################################################
	############################################################################################
	def __init__(self):
		"""
		"""
		self.cfg_main   = None
		self.cfg_local  = None

	##                                                                                      #}}}
	##@ _find_gitroot                                                                       #{{{
	############################################################################################
	############################################################################################
	def _find_gitroot( self, filepath ):
		"""
		Returns git's project root
		"""

		filedir  = os.path.dirname( filepath )
		print( 'finding git-root from: "%s"' % filedir )
		pipe = subprocess.Popen( 
				shlex.split( 'git rev-parse --show-toplevel' ),
				cwd    = filedir,
				stdout = subprocess.PIPE,
				stderr = subprocess.PIPE,
			)
		pipe.wait()

		if pipe.returncode != 0:
			logger.error( 'returncode: %s' % pipe.returncode )
			for line in pipe.stderr:
				print( line )
			raise RuntimeError( 'Error finding gitroot' )

		else:
			gitroot = pipe.stdout.getline()
			print( gitroot )
			return gitroot


	##                                                                                      #}}}
	##@ _get_proj_copypaths                                                                 #{{{
	############################################################################################
	############################################################################################
	def _get_proj_copypaths(self, gitroot):
		"""
		Based on JSON config, and the file's gitroot, 
		retrieves the locations that the file should also be copied to
		"""

		for project in self.config:
			if self.config[ project ]['path'] == 'gitroot'
				return self.config[ project ]['copy_paths']
	
		logger.debug('git-root not configured. ignoring: "%s"' gitroot )

	##                                                                                      #}}}
	##@ projsync                                                                            #{{{
	############################################################################################
	############################################################################################
	def copy_to_copypaths(self):
		"""
		Copies the currently selected file to all of it's git-project's
		'copy_paths'.

		All timestamps/file-attrs should be preserved.
		"""
		filepath = vim.current.buffer.name
		gitroot  = self._find_gitroot( filepath )

		gitroot_filepath  = filepath.replace( gitroot, '' )
		project_copypaths = self._get_proj_copypaths( gitroot )

		for project in project_copypaths:
			for copypath in project_copypaths[ project ]:

				if project_copypaths[ project ][ copypath ]['method'] == 'copy':
					shutil.copy2( filepath, '{copypath}/{gitroot_filepath}' )
				else:
					logger.error('bad config - unknown method: "%s"' % project_copypaths[ project ][ copypath ]['method']

	##                                                                                      #}}}
	##@ reload_config                                                                       #{{{
	############################################################################################
	############################################################################################
	def reload_config(self, filepath):
		"""
		configs can be stored in 2x locations:
		a) .projsync.json in the same directory as the file
		b) ~/.vim/projsync.json
		"""


		cwd = os.path.dirname( filepath )

		cfg_local = '{cwd}/.projsync.json'.format(**ll())
		cfg_main  = '{HOME}/.vim/projsync.json'.format(**ll())


		if os.path.isfile( cfg_local ):
			with open( cfg_local, 'r' ) as ff:
				self.cfg_main  = json.load( ff )

		elif os.path.isfile( cfg_main ):
			with open( cfg_main, 'r' ) as ff:
				self.cfg_local = json.load( ff )

		## otherwise, no config	

	##                                                                                      #}}}






