import paramiko


class RemoteHost():
    def __init__(self, remote_host, remote_login, remote_pass):
        self._remote_host = remote_host
        self._remote_login = remote_login
        self._remote_pass = remote_pass

    def closeScreenSession(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self._remote_host, username=self._remote_login, password=self._remote_pass)
        ssh.exec_command("screen -S restore -X quit;rm screenlog.*")

    def openScreenSession(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self._remote_host, username=self._remote_login, password=self._remote_pass)
        ssh.exec_command("screen -d -m -L -S restore")

    def execOnScreenSession(self, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self._remote_host, username=self._remote_login, password=self._remote_pass)
        stdin_, stdout_, stderr_ = ssh.exec_command("screen -d -m -L -S restore " + command)
        lines = stdout_.readlines()
        i = 0
        for line in lines:
            print(i, line)
            i= i+1

    def removeOnScreenLog(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self._remote_host, username=self._remote_login, password=self._remote_pass)
        ssh.exec_command("rm screenlog.*")

    def execOnRemote(self, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self._remote_host, username=self._remote_login, password=self._remote_pass)
        stdin_, stdout_, stderr_ = ssh.exec_command(command)
        lines = stdout_.readlines()
        i = 0
        for line in lines:
            print(i, line)
            i= i+1

    def tailScreenLog(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self._remote_host, username=self._remote_login, password=self._remote_pass)
            stdin_, stdout_, stderr_ =  ssh.exec_command("tail -n 5 screenlog.0")
            lines = stdout_.readlines()
        finally:
            ssh.close()
        megaline = ""
        for line in lines:
            megaline += line

        return megaline