#!/usr/bin/env python2
"""
Name :          projsync.py
Created :       July 21 2016
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Configure vim to copy files to other location(s)
					 relative to the project's git-root on file-save 
					 (or whenever else it is useful to you)

					 ex:
						 /home/dev/scripts/.git                        >> /devsync/win32/
						 /home/dev/scripts/ python/animtools/file.py   >> /devsync/win32/ python/animtools/file.py
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
import platform
import fnmatch

#!TODO: ProjSync could be a singleton


logger = logging.getLogger(__name__)
ll     = locals

## make a singleton
class ProjSync( object ):
	##@ __init__                                                                            #{{{
	############################################################################################
	############################################################################################
	def __init__(self, debug=False ):
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


		USE: if you just added a new projsync.json file (that did not exist before)
		"""

		self.proj_configs = {}


	##                                                                                      #}}}
	##@ sync_all                                                                            #{{{
	############################################################################################
	############################################################################################
	def sync_all(self):
		"""
		For the opened file's 'gitroot'
		Removes all files in each 'copy_paths' location,
		then copies all files from gitroot into each 'copy_paths' location.


		USE: Designed to be run every time you switch git-branches.
		"""
	
		## get filepath, and it's gitroot (which identifies it's project)
		filepath = vim.current.buffer.name
		gitroot  = self._find_gitroot( filepath )



		## delete everything under each 'copy_path'
		## (but not the copypath itself, since that is generally a shared folder)
		##
		project_copypaths = self.get_copypaths( gitroot=gitroot, filedir=gitroot )

		for copypath in project_copypaths:
			for filepath in os.listdir( copypath['path'] ):
				cwd = copypath['path']
				copypath_path = '{cwd}/{filepath}'.format(**ll())

				if copypath['method'] == 'copy':
					if self.debug: print('Recursively Deleting path: "%s"' % copypath_path )
					try:
						if os.path.isdir( copypath_path ):
							shutil.rmtree( copypath_path )
						else:
							os.remove( copypath_path )
					except:
						print('error deleting: "%s"' % copypath_path )

				else:
					logger.error('bad config - unknown method: "{method}"'.format(**copypath) )


		## copy all files under each 'copy_path'
		##
		for (cwd, dirs, files) in os.walk( gitroot, topdown=False ):
			project_copypaths = self.get_copypaths( gitroot=gitroot, filedir=cwd )

			for filename in files:
				filepath = '{cwd}/{filename}'.format(**ll())
				for copypath in project_copypaths:
					gitroot_filepath  = filepath.replace( gitroot, '' )
					if copypath['method'] == 'copy':
						self._pushmethod_copy( filepath, gitroot_filepath, copypath )
					else:
						logger.error('bad config - unknown method: "{method}"'.format(**copypath) )



	##                                                                                      #}}}
	##@ push_file                                                                           #{{{
	############################################################################################
	############################################################################################
	def push_file(self, filepath=None, gitroot=None, project_copypaths=None ):
		"""
		Copies the file from active vim buffer 
		to all of it's git-project's
		configured 'copy_paths'.

		All timestamps/file-attrs should be preserved.


		USE: designed to run every time you save a file

		_______________________________________________________________________________________________________________________
		INPUT:
		_______________________________________________________________________________________________________________________
		filepath          | '/home/dev/myfile.py'         | (opt)  | path to the file to be copied. If no file is supplied,
		                  |                               |        | the currently opened filepath in the active vim buffer is used.
		                  |                               |        |
		gitroot           | '/home/dev'                   | 1(opt) | if you already know the gitroot, you can supply it here
		                  |                               |        |
		project_copypaths | ['/devsync/mfw/scripts', ...] | 1(opt) | if you already know the copy_paths,
		                  |                               |        | you may supply it here.
		                  |                               |        |
		"""

		## get filepath, and it's gitroot (which identifies it's project)
		if not filepath:
			filepath = vim.current.buffer.name

		gitroot  = self._find_gitroot( filepath )
		gitroot_filepath  = filepath.replace( gitroot, '' )

		## identify path from gitroot, and all dirs to copy to
		if not project_copypaths:
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
			try:
				os.remove( copypath_path )
			except:
				print('error deleting: "%s"' % copypath_path )


		if self.debug:
			print('copying file "{filepath}" > "{copypath_path}"'.format( **ll() )  )

		try:
			shutil.copy2( filepath, copypath_path )
		except:
			print('Error copying: "{filepath}" > "{copypath_path}"'.format( **ll() ) )


	##                                                                                      #}}}
	##@ _delmethod_copy                                                                     #{{{
	############################################################################################
	############################################################################################
	def _delmethod_copy(self, filepath, gitroot_filepath, config ):
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

		if self.debug:
			print('deleting file "{copypath_path}"'.format( **ll() )  )

		if os.path.isfile( copypath_path ):
			os.remove( copypath_path )


	##                                                                                      #}}}

	## Utilities
	##@ get_copypaths                                                                       #{{{
	############################################################################################
	############################################################################################
	def get_copypaths(self, filepath=None, filedir=None, gitroot=None ):
		"""
		Based on JSON config, and the file's gitroot, 
		retrieves the locations that the file should also be copied to

		_____________________________________________________________________________________
		INPUT:
		_____________________________________________________________________________________
		filepath | '/home/dev/progs/myscript.py' | 1(opt) | path to the file you are operating on.
		         |                               |        |
		filedir  | '/home/dev/progs'             | 2(opt) | path to the directory containing your file
		         |                               |        |
		gitroot  | '/home/dev'                   | 2(opt) | path to your file's gitroot (if you know it)
		         |                               |        |
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
		if not gitroot:
			gitroot = self._find_gitroot( filepath )
			if not gitroot:
				logger.debug('file not in a git-project. ignoring: "%s"' % filepath )
				return


		## identify file's config
		config = self._get_fileconfig( filepath=filepath, filedir=filedir )
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
				if not 'hostnames' in config[ project ]:
					raise RuntimeError('Invalid Project Config. Every project must contain the key "hostnames". project "%s"' % project )

				project_gitroot   = config[ project ]['gitroot'].replace('~',HOME)
				project_hostnames = config[ project ]['hostnames']

				## check if gitroot matches project's gitroot
				if gitroot == project_gitroot:

					## check if hostname matches the projsync config
					host_match = False
					for hostname in project_hostnames:
						if fnmatch.fnmatch( platform.node(), hostname ):
							host_match = True
							break

					if host_match:
						if self.debug: print('Project Identified: %s' % project)
						return config[ project ]['copy_paths']


			if self.debug: 
				print('current gitroot not found in config: gitroot "%s"' % gitroot)


	##                                                                                      #}}}
	##@ _get_fileconfig                                                                     #{{{
	############################################################################################
	############################################################################################
	def _get_fileconfig(self, filepath=None, filedir=None):
		"""
		configs can be stored in 2x locations:
		a) projsync.json  in same directory as file
		c) .projsync.json in same directory as file
		b) ~/.vim/projsync.json


		_____________________________________________________________________________________
		INPUT:
		_____________________________________________________________________________________
		filepath  | '/home/dev/progs/myscript.py' | (opt) | path to the file you are operating on.
		          |                               |       |
		filedir   | '/home/dev/progs'             | (opt) | alternatively, if you are working with an
		          |                               |       | entire directory of files, you may
					 |                               |       | pass the file's directory directly.
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

		if filedir:		cwd = filedir
		else:				cwd = os.path.dirname( filepath )


		def save_new_config( config_path=None, cwd=None ):
			""" 
			reads a config_file, 
			saves contents under current-working-directory 
			with last-mod-date for future reference  

			____________________________________________________________
			INPUT:
			____________________________________________________________
			config_path | '/path/to/projsync.json' | 1(opt) | the path to the config (including the config)
			            |                          |        |
			cwd         | '/path/to'               | 1(opt) | the path to the config
			            |                          |        |
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

		existing_project = False
		if self.proj_configs:
			if cwd in self.proj_configs:
				existing_project = True


		## If this directory's config has already been read,
		## Check if config has changed since last read (reload if changed)
		if existing_project:
			config_path   = self.proj_configs[ cwd ]['config_path']
			last_mtime    = self.proj_configs[ cwd ]['mtime']
			if self.debug: print('reusing existing config: "%s"' % config_path )

			if os.path.getmtime( config_path ) > last_mtime:
				return save_new_config( cwd=config_path )

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


