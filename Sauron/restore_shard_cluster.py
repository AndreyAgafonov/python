import configparser as configparser
import time
import paramiko
from RemoteHost import RemoteHost
from ConfigPlusRouter import ConfigPlusRouter
from Shard import Shard


print("Restore BackUp - Task: 1 Configuration")
parser = configparser.ConfigParser()
parser.read('conf/properties.ini')
sections = parser.sections()

remoteHostShards = {}
remoteHostConfig = None
renameReplicaSets = {}

for i, section in enumerate(sections):
    if section == "general":
        __user_login = parser[section]['user_login']
        __user_pass = parser[section]['user_pass']
        __backup_mark = parser[section]['backup_mark']
        __mongodb_user = parser[section]['mongodb_user']
        __mongodb_pass = parser[section]['mongodb_pass']
        __mongodb_database = parser[section]['mongodb_database']
        __mongodb_auth_database = parser[section]['mongodb_auth_database']

    else:
        if section == "config":
            remoteHostConfig = ConfigPlusRouter(parser[section]['remote_host'], parser[section]['remote_port'], parser[section]['remote_path'])
            remoteHostConfig.setLoginInfo(__user_login,__user_pass)
            remoteHostConfig.setMongoDBInfo(__mongodb_user,__mongodb_pass,__mongodb_auth_database,"config",__mongodb_database,__backup_mark)
            remoteHostConfig.setName(section)
            renameReplicaSets[section] = parser[section]['replicasetname_new']
        else:
            __shard = Shard(parser[section]['remote_host'], parser[section]['remote_port'], parser[section]['remote_path'], section)
            __shard.setLoginInfo(__user_login,__user_pass)
            __shard.setMongoDBInfo(__mongodb_user,__mongodb_pass,__mongodb_auth_database,__mongodb_database,__backup_mark)
            __shard.setName(section)
            remoteHostShards[section] = __shard
            __shard = None
            renameReplicaSets[section] = parser[section]['replicasetname_new']


if remoteHostConfig is None:
    print("Error in configuration: Config Replica Set")
    exit(-1)
    remoteHostConfig.setReplicaMapping(renameReplicaSets)
if remoteHostShards.__len__() == 0:
    print("Error in configuration: Zero Shards Replica Sets")
    exit(-1)

print("Restore BackUp - Task: 2 Drop database: %s" % __mongodb_database)
remoteHostConfig.dropMongodbDatabase()
time.sleep(10)

print("Restore BackUp - Task: 3 Stop Balancer:mongos")
remoteHostConfig.stopMongoRouter()

print("Restore BackUp - Task: 4 Replace mongod config and Restart Config as Standalone")
remoteHostConfig.replaceMongodConfigAndRestart("standalone")

print("Restore BackUp - Task: 5 Restore Config")
remoteHostConfig.restoreConfigDB()
while True:
    status = remoteHostConfig.checkStatusRestoreConfigDB()
    if status == 1:
        break
    elif status == 0:
        continue
    else:
        print("Error while restoring config database\nexit")
        exit(-1)
    time.sleep(1)

print("Restore BackUp - Task: 6 Reconfigure Config Database")
remoteHostConfig.reconfigureConfigDB()

print("Restore BackUp - Task: 7 Replace mongod config and Restart Config")
remoteHostConfig.replaceMongodConfigAndRestart("bak")

print("Restore BackUp - Task: 8 Restore Shards ")
for shardName, remoteHostShard in remoteHostShards.items():
    remoteHostShard.restoreMongoDB()

shards_restoring = list(remoteHostShards.keys())
error_appeared = False
while True:
    statusPerShard = {}
    for shardName in shards_restoring:
        statusPerShard[shardName] = remoteHostShards[shardName].checkStatusRestoreDB()

    for shardName, status in statusPerShard.items():
        if status == -1:
            print("Error while restoring shard " + shardName)
            error_appeared = True
            shards_restoring.remove(shardName)
        elif status == 1:
            shards_restoring.remove(shardName)

    if not shards_restoring:
        break
    time.sleep(600)

if error_appeared:
    print("Restore Shards Task ended with errors\nexit")
    exit(-1)

print("Restore BackUp - Task: 9 Restart Shards")
for shardName, remoteHostShard in remoteHostShards.items():
    remoteHostShard.restartMongoShard()

print("Restore BackUp - Task: 10 Start Balancer:mongos")
remoteHostConfig.startMongoRouter()





