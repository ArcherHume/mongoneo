#!/bin/sh

mongod --replSet mongoneo --fork --logpath=/var/log/mongodb.log
mongo db --eval "rs.initiate()"
mongod --shutdown
mongod --replSet mongoneo --bind_ip 0.0.0.0 --setParameter maxTransactionLockRequestTimeoutMillis=1000
