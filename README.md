# conan-cpptango

[![Build status](https://ci.appveyor.com/api/projects/status/fqphnawa29a7prv5/branch/master?svg=true)](https://ci.appveyor.com/project/softwareschneiderei/conan-cpptango/branch/master)

Conan recipe for Tango Control Systems

To use this, add our remote like this:
```
conan remote add schneide https://api.bintray.com/conan/softwareschneiderei/conan
```

Then add the following requirement to your project:
```
cpptango/9.3.3@softwareschneiderei/stable
```

This is currently tested on Win10/VS2019 and some Debian Linux variants (9 and 10). We supply binary packages for some of the variants.
