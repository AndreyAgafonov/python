from RemoteHost import RemoteHost
import pymongo
from pymongo import MongoClient
from os.path import join

class ConfigPlusRouter():
    def __init__(self, remote_host, remote_port, remote_path):
        self._remote_host = remote_host
        self._remote_port = remote_port
        self._remote_path = remote_path

    def setName(self, name):
        self._replica_name = name

    def getName(self):
        return self._replica_name

    def setLoginInfo(self, login, password):
        self._user_login = login
        self._user_pass = password

    def setReplicaMapping(self,replica_name_mapping):
        self._replica_name_mapping = replica_name_mapping

    def setMongoDBInfo(self, __mongodb_user, __mongodb_pass, __mongodb_auth_database, __mongodb_config_database, __mongodb_database,
                       __backup_mark):
        self._mongodb_user = __mongodb_user
        self._mongodb_pass = __mongodb_pass
        self._mongodb_auth_database = __mongodb_auth_database
        self._mongodb_config_database = __mongodb_config_database
        self._mongodb_database = __mongodb_database
        self._backup_mark = __backup_mark

    def dropMongodbDatabase(self):
        client = MongoClient('mongodb://%s:%s@%s:27017/%s' % (self._mongodb_user, self._mongodb_pass, self._remote_host, self._mongodb_auth_database))
        client.drop_database(self._mongodb_database)

    def stopMongoRouter(self):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        remoteHost.execOnRemote("bash ./stopMongoS.sh")

    def startMongoRouter(self):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        remoteHost.execOnRemote("bash ./startMongoS.sh")

    def replaceMongodConfigAndRestart(self, replacement_config_extension):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        remoteHost.execOnRemote("sudo /bin/cp /etc/mongoc.conf.%s /etc/mongoc.conf; bash ./restartMongoC.sh"
                                % replacement_config_extension)
# Добавил строку с исключение восстановления систем сессий
    def restoreConfigDB(self):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        mongodbcommand = "mongorestore --host %s --port %s --gzip --nsExclude 'config.*log' --nsExclude 'system.sessions'  --drop --username %s --password %s --authenticationDatabase %s --db %s " %\
                         (self._remote_host,self._remote_port,self._mongodb_user,self._mongodb_pass,self._mongodb_auth_database,self._mongodb_config_database) +\
                         join(self._remote_path, self._replica_name, self._backup_mark, "config")
        remoteHost.execOnScreenSession(mongodbcommand)

    def checkStatusRestoreConfigDB(self):
        remoteHost = RemoteHost(self._remote_host,self._user_login,self._user_pass)
        log = remoteHost.tailScreenLog()
        if "    done" in log:
            print(log)
            remoteHost.closeScreenSession()
            return 1
        elif "    Failed" in log:
            print(log)
            remoteHost.closeScreenSession()
            return -1
        else:
            return 0

    def reconfigureConfigDB(self):
        client = MongoClient('mongodb://%s:%s@%s:%s/%s' % (self._mongodb_user, self._mongodb_pass, self._remote_host, self._remote_port, self._mongodb_auth_database))
        db = client['config']
        db.databases.update_many({"primary": "replicaSetName"}, {"$set": {"primary": "apple"}})
        

        db.shards.delete_many({})
        db.shards.insert_one({"_id":"replicaSetName","host":"apple/mdb-:27017"})
        
        db.chunks.update_many({"shard": "replicaSetName"}, {"$set": {"shard":"apple"}})
       
        #########После перехода на 4 версию##########
        db.tags.update_many({"tag": "replicaSetName"}, {"$set": {"tag":"apple"}})
       

        #### delete field  history from all documents
        db.chunks.update_many({}, {"$unset": {"history": ""}})

