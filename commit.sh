#!/bin/bash

# Check if commit message was supplied
if [ $# -eq 0 ]
  then
    echo "No commit message supplied, using a default message"
    COMMIT_MSG="Automated commit"
  else
    COMMIT_MSG=$1
fi

# Add all changed files to git
git add .

# Commit the changes
git commit -m "$COMMIT_MSG"

# Push the changes
git push origin main

echo "Changes pushed to origin main"
