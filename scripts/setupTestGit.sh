#!/bin/sh -ev

echo "Email: $EMAIL"
echo "Name: $DEBFULLNAME"

git config --global user.email $EMAIL
git config --global user.name "$DEBFULLNAME"

if git rev-parse --git-dir > /dev/null 2>&1 ; then 
    GIT_HOOKS=$(git rev-parse --git-dir)/hooks

    if [ -w $GIT_HOOKS/pre-commit ]; then
      cat > $GIT_HOOKS/pre-commit <<"EOF"
#!/bin/sh

if [ "$USER" = "$REAHL_USER" ] 
then
        echo "Please don't commit as the $REAHL_USER user...rather commit from your own machine as yourself."
        exit 1
else
        exit 0
fi

EOF

      chmod u+x $GIT_HOOKS/pre-commit
    fi
fi
