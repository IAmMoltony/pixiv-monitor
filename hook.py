import subprocess
import threading
import logging

class Hook:
    def __init__(self, command):
        self.command = command
    
    def run(self, illust):
        threading.Thread(target=self.execute_command, args=(illust,)).start()
    
    def execute_command(self, illust):
        logger = logging.getLogger()
        full_command = self.command + [str(illust.iden), illust.title, illust.caption, illust.get_tag_string(False), str(illust.user.iden), illust.user.name, illust.user.account]
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            logger.info(f"[{str(self)}] {line.rstrip()}")
        process.wait()
        logger.info(f"Hook {str(self)} exited with code {process.returncode}")
    
    def __str__(self):
        return f"Hook({self.command})"