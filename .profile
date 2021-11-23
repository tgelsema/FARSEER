# Bash script that is run on application startup to set proper paths for SQL drivers
export PATH=$PATH:/home/vcap/deps/0/apt/opt/mssql-tools/bin/
export ODBCSYSINI=$HOME/app/odbc-cfg/