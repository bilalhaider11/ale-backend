FROM postgres:17.2-bookworm

ADD dbVersion.sql /docker-entrypoint-initdb.d
ADD postgresql.conf /etc/postgresql/
