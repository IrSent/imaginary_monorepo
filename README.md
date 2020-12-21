
## Install Pants:

```
curl -L -o ./pants https://pantsbuild.github.io/setup/pants && \
chmod +x ./pants
```

## Usage examples:

```
$ ./pants run src/python/carwatch:bot

$ ./pants run src/python/carwatch:admin_manage

$ ./pants run src/python/carwatch:admin -- \
    carwatch.admin.app.asgi:application \
    --bind 127.0.0.1:8000 \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -
```

## Useful snippets for development:

### Postgres dev db setup

Pass the local path to psql binary for the initial db setup.

```
$ ./pants run src/python/carwatch:admin_manage -- create_dev_db /Applications/Postgres.app/Contents/Versions/latest/bin/psql
```

## Application and development hints

### Arguments for targets

Pass arguments to the target after "--"
Example:
```
$ ./pants run some/target -- arg1 arg2
```

### Application configs

From now on in my applications I use yaml files as configs.
Set or export CONFIG envvar to override default path to the yaml config file
Example:

```
$ CONFIG=/path/to/config.yaml ./pants run some/target
$ export CONFIG=/path/to/config.yaml
$ ./pants run some/target
```

### Django migrations

By this time I couldn't find a way to save migration files from makemigrations.
But we can do a dry-run with verbosity 3.
It will log migrations to stdout and we can manually make appropriate steps to deal with migrations.

```
$ ./pants run src/python/carwatch:admin_manage -- makemigrations --dry-run --verbosity 3
$ ./pants run src/python/carwatch:admin_manage -- migrate
```
