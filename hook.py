import subprocess

class Hook:
    def __init__(self, command):
        self.command = command
    
    def run(self, illust):
        full_command = self.command + [str(illust.iden), illust.title, illust.caption, illust.get_tag_string(False), str(illust.user.iden), illust.user.name, illust.user.account]
        subprocess.Popen(full_command)
    
    def __str__(self):
        return f"Hook({self.command})"