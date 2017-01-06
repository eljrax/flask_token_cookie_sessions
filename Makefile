all:
	@echo "Run \`make test\` to execute tests"
tests test:
	@/usr/bin/test `docker-compose ps | egrep -c "(se_memcached|session_example).*Up"` == 2  || (echo "Application not running - starting.." && docker-compose up -d) 
	docker-compose exec session_example /bin/bash -c "cd /app ; python -m unittest discover -s tests/"
