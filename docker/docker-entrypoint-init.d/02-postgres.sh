#!/bin/bash
if [ "$DATABASE_TYPE" == "psql-local" ]; then
    echo "Waiting for Postgres to start up..."
    until psql -U "$POSTGRES_USER" -c '\q'; do
        echo "Postgres is unavailable - sleeping"
        sleep 10
    done
    echo "Checking if the $DATABASE_NAME exists (pqsl-local)..."
    racedb=$(psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DATABASE_NAME'")
    if [ "$racedb" != "1" ]; then
        echo "Creating $DATABASE_NAME database..."
        # POSTGRES_USER is the same as the postgres database name
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
        CREATE USER $DATABASE_USER;
        CREATE DATABASE $DATABASE_NAME;
EOSQL
    else
        echo "RaceDB DB already exists. Not creating."
    fi
    
	echo "Granting all user permissions (pqsl-local).."
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    ALTER DATABASE $DATABASE_NAME OWNER TO $DATABASE_USER;
	GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DATABASE_USER;
	GRANT ALL ON SCHEMA public TO $DATABASE_USER;
    GRANT ALL ON SCHEMA public TO public;
EOSQL

elif [ "$DATABASE_TYPE" == "psql" ]; then
    PG_PASSWORD="$DATABASE_PASSWORD"
    echo "Waiting for remote Postgres to start up..."
    until psql -U "$POSTGRES_USER" -h "$DATABASE_HOST" -c '\q'; do
        echo "Postgres is unavailable - sleeping"
        sleep 10
    done
    echo "Checking if the $DATABASE_NAME exists ( (pqsl)..."
    racedb=$(psql -U "$POSTGRES_USER" -h "$DATABASE_HOST"  -tAc "SELECT 1 FROM pg_database WHERE datname='$DATABASE_NAME'")
    if [ "$racedb" != "1" ]; then
        echo "Creating $DATABASE_NAME database..."
        psql -v ON_ERROR_STOP=1 -h "$DATABASE_HOST" --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
        CREATE USER $DATABASE_USER;
        CREATE DATABASE $DATABASE_NAME;
EOSQL
    else
        echo "RaceDB DB already exists on remote server. Not creating."
    fi
    
	echo "Granting all user permissions (pqsl*)..."
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    ALTER DATABASE $DATABASE_NAME OWNER TO $DATABASE_USER;
	GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DATABASE_USER;
	GRANT ALL ON SCHEMA public TO $DATABASE_USER;
    GRANT ALL ON SCHEMA public TO public;
EOSQL

else
    echo "Ignoring Postgres startup on non-postgres database"
fi
