import sublime, sublime_plugin
import codecs,os,subprocess,threading,json,webbrowser
from subprocess import PIPE

packages_path = sublime.packages_path() + os.sep + 'Lazyphp4'

def fs_reader(path):
    return codecs.open(path, mode='r', encoding='utf8').read()

def show_outpanel(self, name, string, readonly = True):
	self.output_view = self.window.get_output_panel(name)
	self.output_view.run_command('append', {'characters': string, 'force': True, 'scroll_to_end': True})
	if readonly:
		self.output_view.set_read_only(True)
	show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
	if show_panel_on_build:
		self.window.run_command("show_panel", {"panel": "output." + name})

def open_tab(url):
    webbrowser.open_new_tab(url)

class Lazyphp4Command(sublime_plugin.TextCommand):
	def run(self, edit):
		return ''

class get_php_document(Lazyphp4Command, sublime_plugin.TextCommand):
	def run(self, edit):
		region = self.view.sel()[0]
		if region.begin() != region.end():
			function = self.view.substr(region)
			thread = find_comment(function,self.view)
			thread.start()
			ThreadProgress(thread, 'Is excuting', 'query completed')
		else:
			sublime.status_message('must be a word')

class find_comment(threading.Thread):
	def __init__(self,word, view):
		self.word = word
		self.view = view
		threading.Thread.__init__(self)

	def run(self):
		path = packages_path + os.sep + 'php_docs' + os.sep + 'zh' + os.sep
		if self.view.settings().has('php_docs'):
			php_docsets = self.view.settings().get('php_docs')
		else:
			index = json.loads(fs_reader(path + 'functions.json'))
			database = json.loads(fs_reader(path + 'database.json'))
			stats = json.loads(fs_reader(path + 'stats.json'))
			php_docsets = {"index" : index, "database": database, "stats": stats}
			self.view.settings().set('php_docsets', php_docsets)
		if self.word in php_docsets['index'] and self.word in php_docsets['database']:
			current = php_docsets['database'][self.word]
			fun_def_item = self.get_comment(self.word, current)
			self.item = fun_def_item
			self.view.show_popup_menu(fun_def_item, self.choose)
		else:
			sublime.status_message('didn\'t find it')

	def get_comment(self, word, current):
		fun_def_item = []
		tpm = '''%(ret_type)s %(name)s (%(params)s)
%(long_desc)s
Parameters:
%(params_desc)s
> 到php.net 查看'''
		data = {
			'ret_type': current['params'][0]['ret_type'],
			'name':current['name'],
			'params': self.get_params(current['params'][0]['list']),
			'long_desc': current['long_desc'],
			'params_desc': self.get_params_desc(current['params'][0]['list'])
		}
		tpm_out = tpm % data
		fun_def_item = tpm_out.split('\n')
		return fun_def_item

	def get_params(self, params_list):
		items = []
		count = 0
		for i in params_list:
			if count == 0:
				params = '[' + i['type'] + ' ' + i['var'] +' ]' if i['beh'] else i['type'] + ' ' + i['var']
			else:
				params = '[,' + i['type'] + ' ' + i['var'] +' ]' if i['beh'] else ',' + i['type'] + ' ' + i['var']
			items.append(params);
			count += 1
		return ' '.join(items)
	def get_params_desc(self, params_list):
		items = []
		for i in params_list:
			items.append( '- ' + i['desc'])
		return '\n'.join(items)

	def choose(self, flag):
		if flag != -1:
			if flag == len(self.item) - 1:
				open_tab('http://www.php.net/manual/%(lang)s/function.%(function)s.php' % {'lang':'zh', 'function': self.word})
			else:
				sublime.set_clipboard(self.item[flag])


class Lazyphp4(sublime_plugin.EventListener):
	def on_post_save(self, view):
		#检测当前目录下是否有_build.php
		dir = view.window().folders()
		if dir != []:
			build_file = dir[0] + os.sep + '_build.php'
			if os.path.exists(build_file) & view.file_name().startswith(dir[0]) & view.file_name().endswith('Controller.php'):
				command_text = 'php _build.php'
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
		proce = subprocess.Popen(self.command_text, stdout=PIPE, shell=True, cwd=self.cwd)
		data,error = proce.communicate()
		if data != b'':
			data = data.decode('utf-8')
		else:
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
