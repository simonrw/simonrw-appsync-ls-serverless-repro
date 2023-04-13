On repository root run
- `yarn`
- `cd backend`
- `python3.9 -m venv lambda_venv`
- `source lambda_venv/bin/activate`
- `pip install --platform=manylinux2014_aarch64 --only-binary=:all: -r requirements.txt --target lambda_venv/lib/python3.9/site-packages`
- `deactivate`
- `python3.9 -m venv venv`
- `source venv/bin/activate`
- `pip install -r requirements.txt`
- `pip install -r requirements_dev.txt`
- `yarn deploy_arm`
- `invoke alltests`

The Docker engine almost halts. The tests never go through. Lambda containers
get created over and over again. Created containers can not be removed.

Only thing that helps is restarting the Docker Desktop / docker daemon.
