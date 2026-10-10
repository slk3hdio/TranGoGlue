# deps/ - supplemented dependencies

This directory holds the source files this fragment needs in order to compile standalone.
It is ignored by the SITP parser (only top-level *.java files of the fragment are parsed).

- source pool: D:\projects\sitp\sitp-dataset\external\jvm-sandbox-pool
- the dependency closure was resolved with javac -sourcepath (only classes actually needed are included).
- third-party jars: junit-4.13.2.jar, hamcrest-core-1.3.jar, commons-lang3-3.12.0.jar, commons-io-2.11.0.jar, slf4j-api-1.7.36.jar, asm-9.4.jar, asm-commons-9.4.jar, asm-util-9.4.jar, guava-31.1-jre.jar (in deps/lib/, referenced by the build script)

## Build

```bat
build.bat    # Windows
sh build.sh  # Linux/macOS
```

Output goes to the build/ directory.
