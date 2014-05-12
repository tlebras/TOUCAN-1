#!/bin/bash
# Script to publish documentation to gh-pages hosted site.
# Make changes to the doc files on master branch and build and test locally first,
# then commit before running this script to commit changes to gh-pages branch

# NB Doesn't push changes to github, do that manually to avoid mistakes

set -e

DOC_DIR=Mermaid2_doc

# Checkout clean version of gh-pages
cd ../
git checkout gh-pages

# Checkout the changes we made in master
git checkout master ${DOC_DIR}/build
git reset HEAD # Unstage

# Move webpages to top directory
cp -ra ${DOC_DIR}/build/html/* ./
rm -rf ${DOC_DIR}

# Commit to gh-pages
# Reference the most recent commit from master branch in this commit message
git add -A
git commit -m "`git log master --pretty=format:'Publish commit %h to gh-pages:%n
  Author: %an %ae
  Date: %ad
  %s' -n 1`"

# Switch back to master
git checkout master
git reset HEAD
