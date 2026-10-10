# deps/ - supplemented dependencies

This directory holds the source files this fragment needs in order to compile standalone.
It is ignored by the SITP parser (only top-level *.java files of the fragment are parsed).

- source pool: D:\projects\sitp\sitp-dataset\external\easyexcel-pool
- the dependency closure was resolved with javac -sourcepath (only classes actually needed are included).
- third-party jars: lombok-1.18.43.jar, poi-5.2.5.jar, poi-ooxml-5.2.5.jar, poi-ooxml-lite-5.2.5.jar, xmlbeans-5.2.0.jar, commons-collections4-4.4.jar, commons-compress-1.26.2.jar, curvesapi-1.08.jar, commons-io-2.11.0.jar, log4j-api-2.24.3.jar, slf4j-api-1.7.36.jar, ehcache-3.9.11.jar, easyexcel-support-4.0.3.jar, commons-csv-1.11.0.jar (in deps/lib/, referenced by the build script)

## Build

```bat
build.bat    # Windows
sh build.sh  # Linux/macOS
```

Output goes to the build/ directory.

## Note

This fragment requires no supplemented Java sources: it compiles using only the third-party jars in deps/lib (verified with an empty deps tree). The 298 files from the lombok workaround closure were all confirmed unnecessary by removal testing and removed.
