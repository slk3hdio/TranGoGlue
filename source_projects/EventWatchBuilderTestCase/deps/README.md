# deps/ - supplemented dependencies

This directory holds the source files this fragment needs in order to compile standalone.
It is ignored by the SITP parser (only top-level *.java files of the fragment are parsed).

- source pool: D:\projects\sitp\sitp-dataset\external\jvm-sandbox-pool
- the dependency closure was resolved with javac -sourcepath (only classes actually needed are included).
- third-party jars: junit-4.13.2.jar, hamcrest-core-1.3.jar (in deps/lib/, referenced by the build script)

## Build

```bat
build.bat    # Windows
sh build.sh  # Linux/macOS
```

Output goes to the build/ directory.
