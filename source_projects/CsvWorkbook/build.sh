#!/bin/sh
set -e
cd "$(dirname "$0")"
mkdir -p build
find deps -name '*.java' > .filelist.txt
ls *.java >> .filelist.txt
javac -encoding UTF-8 -cp "deps/lib/*" -processorpath "deps/lib/lombok-1.18.43.jar" -d build @.filelist.txt
echo BUILD OK
