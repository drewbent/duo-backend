# For creating backups. This should be run locally, and
# not from Heroku

# Fail fast if error or missing var
set -eu
set -o pipefail

# Download backup from heroku & gzip
heroku pg:backups:download --output=~/Downloads/pg_backup.dump --app $APP_NAME