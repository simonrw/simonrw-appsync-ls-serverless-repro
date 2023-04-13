import json
import os
from invoke import run, task

env = {'PYTHONUNBUFFERED': 'TRUE'}
if os.path.isfile('.env'):
    with open('.env', 'r', encoding="utf8") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if not line.startswith('#'):
                parts = line.split('=')
                if len(parts) == 2:
                    env[parts[0].strip()] = parts[1].strip()


@task
def generatemigrations(_, message):
    if not message:
        raise Exception("Migration message must be defined")
    run('alembic --config lambdas/migrations/alembic.ini revision --autogenerate -m "' + message + '"',
        env=env | {'PYTHONPATH': './:./lambdas'})


@task
def createmigration(_, message):
    if not message:
        raise Exception("Migration message must be defined")
    run('alembic --config lambdas/migrations/alembic.ini revision -m "' + message + '"',
        env=env | {'PYTHONPATH': './:./lambdas'})


@task
def migratedb(_):
    run('alembic --config lambdas/migrations/alembic.ini upgrade head',
     env=env | {'PYTHONPATH': './:./lambdas'}, hide=False)


@task
def downgradedb(_, version):
    run('alembic --config lambdas/migrations/alembic.ini downgrade ' + str(version),
        env=env | {'PYTHONPATH': './:./lambdas'})


@task
def createdb(_):
    payload = {"action": "create", "db_name": "portal", "owner": "portal", "password": "portal"}
    cmd = f"python lambdas/migrations/db_setup.py '{json.dumps(payload)}'"
    run(cmd, env=env | {'PYTHONPATH': './:./lambdas'})


@task
def dropdb(_):
    payload = {"action": "drop-db", "db_name": "portal"}
    cmd = f"python ./lambdas/migrations/db_setup.py '{json.dumps(payload)}'"
    run(cmd, env=env | {'PYTHONPATH': './:./lambdas'})


@task
def unittests(_):
    cmd = 'pytest ./tests/unit'
    run(cmd, env=env | {'PYTHONPATH': './:./lambdas:./tests'})


@task
def integrationtests(_):
    cmd = 'pytest ./tests/integration'
    run(cmd, env=env | {'PYTHONPATH': './:./lambdas:./tests'})


@task(pre=[unittests, integrationtests])
def alltests(_):
    pass
