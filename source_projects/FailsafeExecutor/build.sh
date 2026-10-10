#!/bin/sh
set -e
cd "$(dirname "$0")"
mkdir -p build
find deps -name '*.java' > .filelist.txt
ls *.java >> .filelist.txt
javac -encoding UTF-8   -d build @.filelist.txt
echo BUILD OK
