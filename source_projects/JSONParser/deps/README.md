# deps/ - supplemented dependencies

This directory holds the source files this fragment needs in order to compile standalone.
It is ignored by the SITP parser (only top-level *.java files of the fragment are parsed).

- source pool: D:\projects\sitp\sitp-dataset\external\hutool-pool
- the dependency closure was resolved with `javac -sourcepath` (only classes actually needed are included).
- third-party jars: none

## Build

```bat
build.bat    # Windows
sh build.sh  # Linux/macOS
```

Output goes to the build/ directory.

## Patch note

- `cn/hutool/core/text/StrBuilder.java`: the method `getChars(int,int,char[],int)` return type was changed from `StrBuilder` to `void` so it matches the JDK 9+ `CharSequence.getChars` default method (hutool 5.x targets Java 8; the covariant return breaks compilation on JDK 9+). No callers rely on the return value.
