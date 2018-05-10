#!/bin/bash -ev

git config --global user.email $EMAIL
git config --global user.name "$DEBFULLNAME"

GIT_HOOKS=$(git rev-parse --git-dir)/hooks

cat > $GIT_HOOKS/pre-commit <<"EOF"
#!/bin/sh

if [ "$USER" = "vagrant" ] 
then
        echo "Please don't commit as the vagrant user...rather commit from your own machine as yourself."
        exit 1
else
        exit 0
fi

EOF

chmod u+x $GIT_HOOKS/pre-commit

