import sublime, sublime_plugin
import os,subprocess,threading
from subprocess import PIPE

packages_path = sublime.packages_path() + os.sep + 'Lazyphp4'

def show_outpanel(self, name, string, readonly = True):
	self.output_view = self.window.get_output_panel(name)
	self.output_view.run_command('append', {'characters': string, 'force': True, 'scroll_to_end': True})
	if readonly:
		self.output_view.set_read_only(True)
	show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
	if show_panel_on_build:
		self.window.run_command("show_panel", {"panel": "output." + name})

class Lazyphp4Command(sublime_plugin.TextCommand):
	def run(self, edit):
		return ''

class Lazyphp4(sublime_plugin.EventListener):
	def on_post_save(self, view):
		#检测当前目录下是否有_build.php
		dir = view.window().folders()
		if dir != []:
			build_file = dir[0] + os.sep + '_build.php'
			if os.path.exists(build_file) & view.file_name().startswith(dir[0]) & view.file_name().endswith('Controller.php'):
				command_text = 'php ' + build_file
				thread = build(command_text, view.window(), dir[0])
				thread.start()
				ThreadProgress(thread, 'Is build', 'build done')

class build(threading.Thread):
	def __init__(self, command_text, window, cwd):
		self.command_text = command_text
		self.cwd = cwd
		self.window = window
		threading.Thread.__init__(self)

	def run(self):
		cloums = os.popen(self.command_text)
		data = cloums.read()
		if data == '':
			data = 'build done!'
		show_outpanel(self, 'Lazyphp4-building', data)

class ThreadProgress():
	"""
	Animates an indicator, [=   ], in the status area while a thread runs

	:param thread:
		The thread to track for activity

	:param message:
		The message to display next to the activity indicator

	:param success_message:
		The message to display once the thread is complete
	"""

	def __init__(self, thread, message, success_message):
		self.thread = thread
		self.message = message
		self.success_message = success_message
		self.addend = 1
		self.size = 8
		sublime.set_timeout(lambda: self.run(0), 100)

	def run(self, i):
		if not self.thread.is_alive():
			if hasattr(self.thread, 'result') and not self.thread.result:
				sublime.status_message('')
				return
			sublime.status_message(self.success_message)
			return

		before = i % self.size
		after = (self.size - 1) - before

		sublime.status_message('%s [%s=%s]' % (self.message, ' ' * before, ' ' * after))

		if not after:
			self.addend = -1
		if not before:
			self.addend = 1
		i += self.addend

		sublime.set_timeout(lambda: self.run(i), 100)
