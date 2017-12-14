import datetime
import os
import threading
import time

#https://github.com/cmheisel/pywatch
class Watcher(object):
    def __init__(self, files=None, cmds=None):
        self.files = []
        self.cmds = []
        self.mtimes = {}
        self._monitor_continously = False
        self._monitor_thread = None

        if files: self.add_files(*files)
        if cmds: self.add_cmds(*cmds)

    def monitor(self):
        #We only want one thread, dear god
        self.stop_monitor()

        self._monitor_continously = True
        self._monitor_thread = threading.Thread(target=self._monitor_till_stopped)
        self._monitor_thread.start()

    def run_monitor(self):
        """Called by main thread methods like __main__ so Ctrl-C works"""
        self.monitor()
        try:
            while self._monitor_continously:
                time.sleep(.02)
        except KeyboardInterrupt:
            self.stop_monitor()

    def stop_monitor(self):
        if self._monitor_thread and self._monitor_thread.isAlive():
            self._monitor_continously = False
            self._monitor_thread.join(0.05)

    def _monitor_till_stopped(self):
        while self._monitor_continously:
            self.monitor_once()
            time.sleep(1)

    def monitor_once(self, execute=True):
        for f in self.files:
            try:
                mtime = os.stat(f).st_mtime
            except OSError:
                time.sleep(1)
                mtime = os.stat(f).st_mtime

            if f not in self.mtimes.keys():
                self.mtimes[f] = mtime
                continue

            if mtime > self.mtimes[f]:
                self.mtimes[f] = mtime
                if execute:
                    map(os.system, self.cmds)
                    break

    def walk_dirs(self, dirnames):
        dir_files = []
        for dirname in dirnames:
            for path, dirs, files in os.walk(dirname):
                files = [ os.path.join(path, f) for f in files ]
                dir_files.extend(files)
                dir_files.extend(self.walk_dirs(dirs))
        return dir_files

    def add_files(self, *files):
        dirs = [ os.path.realpath(f) for f in files if os.path.isdir(f) ]
        files = [ os.path.realpath(f) for f in files if os.path.isfile(f) ]

        dir_files = self.walk_dirs(dirs)
        files.extend(dir_files)

        valid_files = [ os.path.realpath(f) for f in files if os.path.exists(f) and os.path.isfile(f) ]
        unique_files = [ f for f in valid_files if f not in self.files ]
        self.files = self.files + unique_files
        self.monitor_once(execute=False)

    def add_cmds(self, *cmds):
        unique_cmds = [ c for c in cmds if c not in self.cmds ]
        self.cmds = self.cmds + unique_cmds

if __name__ == '__main__':
    w = Watcher(['watcher.py'], ['less watcher.py'])
    w.run_monitor() 