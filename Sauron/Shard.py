from RemoteHost import RemoteHost
from os.path import join

class Shard():
    def __init__(self, remote_host, remote_port, remote_path,shardname):
        self._remote_host = remote_host
        self._remote_port = remote_port
        self._remote_path = remote_path
        self._shard_name = shardname

    def setName(self, name):
        self._shard_name = name

    def getName(self):
        return self._shard_name

    def setLoginInfo(self, login, password):
        self._user_login = login
        self._user_pass = password

    def setMongoDBInfo(self, __mongodb_user, __mongodb_pass, __mongodb_auth_database, __mongodb_database,
                       __backup_mark):
        self._mongodb_user = __mongodb_user
        self._mongodb_pass = __mongodb_pass
        self._mongodb_auth_database = __mongodb_auth_database
        self._mongodb_database = __mongodb_database
        self._backup_mark = __backup_mark

    def restartMongoShard(self):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        remoteHost.execOnRemote("bash ./restartMongoD.sh")

    def restoreMongoDB(self):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        remoteHost.removeOnScreenLog()
        mongodbcommand = "mongorestore --host %s --port %s --gzip --drop --username %s --password %s --authenticationDatabase %s --db %s " %\
                         (self._remote_host,self._remote_port,self._mongodb_user,self._mongodb_pass,self._mongodb_auth_database,self._mongodb_database) +\
                         join(self._remote_path, self._shard_name, self._backup_mark, self._mongodb_database)
        remoteHost.execOnScreenSession(mongodbcommand)

    def checkStatusRestoreDB(self):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        log = remoteHost.tailScreenLog()
        if "    done" in log:
            print(self._shard_name + ':\n' + log)
            remoteHost.closeScreenSession()
            return 1
        elif "    Failed" in log:
            print(self._shard_name + ':\n' + log)
            remoteHost.closeScreenSession()
            return -1
        else:
            return 0