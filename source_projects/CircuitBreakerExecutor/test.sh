#!/bin/sh
set -e
cd "$(dirname "$0")"
./build.sh
mkdir -p tests/build
find tests -name '*.java' > .testfilelist.txt
javac -encoding UTF-8 -cp "build:deps/lib/*:tests/lib/*" -d tests/build @.testfilelist.txt
CLASSES=$(find tests -name '*Test.java' | sed -e 's#^tests/##' -e 's#/#.#g' -e 's#\.java$##')
java -cp "tests/build:build:deps/lib/*:tests/lib/*" org.junit.runner.JUnitCore $CLASSES
rm -f .testfilelist.txt
