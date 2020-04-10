import os

from conans import ConanFile, CMake, tools


class TangoTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.dylib*", dst="bin", src="lib")
        self.copy('*.so*', dst='bin', src='lib')

    def test(self):
        if self.settings.os == "Windows" or not tools.cross_building(self.settings):
            os.chdir("bin")
            self.run(".%stango_package_test" % os.sep)
