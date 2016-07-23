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
import time

logger = logging.getLogger(__name__)
ll     = locals

## make a singleton
class ProjSync( object ):
	##@ __init__                                                                            #{{{
	############################################################################################
	############################################################################################
	def __init__(self, debug=True ):
		"""
		"""
		self.debug = debug
		self.proj_configs = {}		## { gitroot : {(json file contents)} }
											#  stores main config, and every encountered localconfig 


	##                                                                                      #}}}

	##@ clear                                                                               #{{{
	############################################################################################
	############################################################################################
	def clear(self):
		"""
		Clears all cached information about config-files.

		expalanation:
		-------------
			In order to save on processing-time when you are saving the same file repeatedly,
			ProjSync stores the path, modified-time, and contents of the config that was used.
	
			This means that with repeated use of the 'push()' command, new config files will not
			be detected if they did not exist at the time of the first 'push()' command during
			this vim session.
	
			This largely has to do with my own personal use-case. I'm using this on a machine
			whose disk is being violently thrashed, I want to keep disk access to an absolute
			minimum.
		"""

		self.proj_configs = {}


	##                                                                                      #}}}
	##@ pushall                                                                             #{{{
	############################################################################################
	############################################################################################
	def push_all(self):
		"""
		For the opened file's 'gitroot'
		Removes all files in each 'copy_paths' location,
		then copies all files from gitroot into each 'copy_paths' location.
		"""
	
		## get filepath, and it's gitroot (which identifies it's project)
		filepath = vim.current.buffer.name
		gitroot  = self._find_gitroot( filepath )


		## delete everything under each 'copy_path'
		for (cwd, files, dirs) in os.walk( gitroot ):


			## identify path from gitroot, and all dirs to copy to
			## (
			for file in files:
				project_copypaths = self.get_copypaths( filepath )

				if copypath['method'] == 'copy'


	##                                                                                      #}}}
	##@ push                                                                                #{{{
	############################################################################################
	############################################################################################
	def push(self):
		"""
		Copies the file from active vim buffer 
		to all of it's git-project's
		configured 'copy_paths'.

		All timestamps/file-attrs should be preserved.
		"""

		## get filepath, and it's gitroot (which identifies it's project)
		filepath = vim.current.buffer.name
		gitroot  = self._find_gitroot( filepath )

		## identify path from gitroot, and all dirs to copy to
		gitroot_filepath  = filepath.replace( gitroot, '' )
		project_copypaths = self.get_copypaths( filepath )

		## for each copypath, handle it's method
		## (currently copy only, but potential for scp, rsync, ...)
		if not project_copypaths:
			if self.debug:
				print('No copy_paths configured')
			return

		for copypath in project_copypaths:

			if copypath['method'] == 'copy':
				self._pushmethod_copy( filepath, gitroot_filepath, copypath )
			else:
				logger.error('bad config - unknown method: "{method}"'.format(**copypath) )


	##                                                                                      #}}}
	##@ _find_gitroot                                                                       #{{{
	############################################################################################
	############################################################################################
	def _find_gitroot( self, filepath ):
		"""
		Inspects a filepath, and returns it's 
		git project-root (location containing .git dir)
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

			if self.debug:
				print( 'Searching for gitroot from: {filedir}'.format( **ll() ) )
				for line in pipe.stderr:
					print( line )
				raise RuntimeError( 'Error finding gitroot' )

		else:
			gitroot = pipe.stdout.readline()
			if self.debug:
				print( 'Using gitroot: {gitroot}'.format(**ll()) )
			return gitroot.strip()


	##                                                                                      #}}}
	##@ _pushmethod_copy                                                                    #{{{
	############################################################################################
	############################################################################################
	def _pushmethod_copy(self, filepath, gitroot_filepath, config ):
		"""
		Copies 'filepath' to ['copy_paths']['path'],
			* using file-attributes from 'filepath' (including last-modified)

		( handler for 'copy_paths' keys using method 'copy' )
		"""
		HOME = os.environ['HOME']

		copypath_path = config['path']
		copypath_path.replace('~', HOME)
		copypath_path = '{copypath_path}/{gitroot_filepath}'.format(**ll())

		if not os.path.isdir( os.path.dirname( copypath_path ) ):
			os.makedirs( os.path.dirname( copypath_path ) )

		if os.path.isfile( copypath_path ):
			os.remove( copypath_path )

		if self.debug:
			print('copying file "{filepath}" > "{copypath_path}"'.format( **ll() )  )

		shutil.copy2( filepath, copypath_path )

	##                                                                                      #}}}

	## Utilities
	##@ get_copypaths                                                                       #{{{
	############################################################################################
	############################################################################################
	def get_copypaths(self, filepath ):
		"""
		Based on JSON config, and the file's gitroot, 
		retrieves the locations that the file should also be copied to

		_____________________________________________________________________________________
		INPUT:
		_____________________________________________________________________________________
		filepath | '/home/dev/progs/myscript.py' |  | path to the file you are operating on.
		         |                               |  |
		_____________________________________________________________________________________
		OUTPUT:
		_____________________________________________________________________________________
			the contents of the 'copy_paths' key for the relevant json file:
			ex:
				[
					{ "method":"copy", "path":"/devsync/test" },
					{ "method":"copy", "path":"/devsync/test2" },
				]
		"""
		HOME = os.environ['HOME']


		## identify gitroot
		gitroot = self._find_gitroot( filepath )
		if not gitroot:
			logger.debug('file not in a git-project. ignoring: "%s"' % filepath )
			return


		## identify file's config
		config = self._get_fileconfig( filepath )
		if not config:
			logger.debug('no JSON config detected for filepath: "%s"' % filepath )
			return


		## return copy_paths

		## in local json files, the gitroot project is implied
		## they only need to contain the key 'copy_paths', and it's contents
		if 'copy_paths' in config:
			return config['copy_paths']

		## if we are using the central ~/.vim/projsync.json, then
		## we need to find if our current gitroot exists in there
		else:
			for project in config:
				if not 'gitroot' in config[ project ]:
					raise RuntimeError('Invalid Project Config. Every project must contain the key "gitroot". project "%s"' % project )
				if not 'copy_paths' in config[ project ]:
					raise RuntimeError('Invalid Project Config. Every project must contain the key "copy_paths". project "%s"' % project )

				project_gitroot = config[ project ]['gitroot'].replace('~',HOME)
				if gitroot == project_gitroot:
					if self.debug: print('Project Identified: %s' % project)

					return config[ project ]['copy_paths']


			if self.debug: 
				print('current gitroot not found in config: gitroot "%s"' % gitroot)


	##                                                                                      #}}}
	##@ _get_fileconfig                                                                     #{{{
	############################################################################################
	############################################################################################
	def _get_fileconfig(self, filepath):
		"""
		configs can be stored in 2x locations:
		a) projsync.json  in same directory as file
		c) .projsync.json in same directory as file
		b) ~/.vim/projsync.json


		_____________________________________________________________________________________
		INPUT:
		_____________________________________________________________________________________
		filepath | '/home/dev/progs/myscript.py' |  | path to the file you are operating on.
		         |                               |  |
		_____________________________________________________________________________________
		OUTPUT:
		_____________________________________________________________________________________
			the entire contents of the JSON file that applies to your file.
			ex:
					{
						"testproj" :{
							"path" :      "/home/vagrant/dev",
							"copy_paths": [
										{ "method":"copy", "path":"/devsync/test" },
										{ "method":"copy", "path":"/devsync/test" },
									]
						}
					}
		"""

		HOME = os.environ['HOME']
		cwd  = os.path.dirname( filepath )

		def save_new_config( config_path ):
			""" 
			reads a config_file, 
			saves contents under current-working-directory 
			with last-mod-date for future reference  
			"""
			if self.debug: print('using config from: "{config_path}"'.format( **ll() ) )
			with open( config_path, 'r' ) as ff:
				config  = json.load( ff )
			self.proj_configs[ cwd ] = {	'config_path' : cwd,
													'mtime'       : os.path.getmtime( config_path ),
													'conts'       : config,
												}
			return config




		json_paths = [
					'{cwd}/projsync.json'.format(**ll()),
					'{cwd}/.projsync.json'.format(**ll()),
					'{HOME}/.vim/projsync.json'.format(**ll()),
					]


		## If this directory's config has already been read,
		## Check if config has changed since last read (reload if changed)
		if cwd in self.proj_configs:
			config_path   = self.proj_configs['config_path']
			last_mtime    = self.proj_configs['mtime']

			if os.path.getmtime( config_path ) > last_mtime:
				return save_new_config( config_path )

		## Otherwise, figure out which json-config to use for this
		## file, load & save
		else:
			if self.debug: print('No config stored for cwd: {cwd}'.format(**ll()) )
			for path in json_paths:
				if os.path.isfile( path ):
					return save_new_config( path )
				elif self.debug: print('No config found at: {path}'.format(**ll()) )




		## otherwise, (no config for project, or filepath)
		return False

	##                                                                                      #}}}


