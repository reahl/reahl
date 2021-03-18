# If using PostgreSQL:
docker-compose exec -T -e PGPASSWORD=reahl app /app/venv/bin/reahl createdbuser -U developer /etc/app-reahl
docker-compose exec -T -e PGPASSWORD=reahl app /app/venv/bin/reahl createdb -U developer /etc/app-reahl
docker-compose exec -T app /app/venv/bin/reahl createdbtables  /etc/app-reahl

# If using MySQL:
#docker-compose exec -T -e MYSQL_PWD=reahl app /app/venv/bin/reahl createdbuser -U root /etc/app-reahl
#docker-compose exec -T -e MYSQL_PWD=reahl app /app/venv/bin/reahl createdb -U root /etc/app-reahl
#docker-compose exec -T app /app/venv/bin/reahl createdbtables  /etc/app-reahl
