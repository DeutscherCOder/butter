#!/bin/bash

cd $(dirname "${BASH_SOURCE[0]}")/..

butter_timestamp=$(git show -s --format=%ct)
butter_commit="$(git show -s --format="%H %s")"

echo "Cloning current cutter.re"

git clone --depth 1 git@github.com:rizinorg/cutter.re.git || exit 1

echo "Updating docs"

rm -rf cutter.re/docs
cp -a docs/build/html cutter.re/docs || exit 1

echo "Committing new changes"

cd cutter.re || exit 1
docs_timestamp=$(git show -s --format=%ct)
if [ $docs_timestamp -ge $butter_timestamp ]; then
	echo "Last commit on cutter.re is newer than this commit on butter. Skipping."
	exit 0
fi

git add . || exit 1
git diff --cached --quiet && echo "No changes." && exit 0
printf "Update docs from rizinorg/cutter\n\nOriginal Commit:\n$butter_commit" | git commit -F -
git push origin master || exit 1

