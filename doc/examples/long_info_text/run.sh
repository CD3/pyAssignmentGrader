rm results.yml
poetry run pygrader setup-grading-files config.yml
poetry run pygrader run-checks config.yml
