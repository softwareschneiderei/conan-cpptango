import os
import shutil
from os.path import join
from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.scm import Git


class CppTangoConan(ConanFile):
    name = "tango-idl"
    version = "6.0.2"
    license = "LGPL-3.0"
    author = "Mihael Koep mihael.koep@softwareschneiderei.de"
    url = "https://gitlab.com/tango-controls/tango-idl"
    description = "Tango Control System IDL"
    topics = ("control-system",)
    settings = "os", "compiler", "build_type", "arch"
    file_prefix = "{0}-{1}".format(name, version)
    source_archive = "{0}.tar.gz".format(file_prefix)

    def requirements(self):
        pass

    def layout(self):
        cmake_layout(self, src_folder="src/tango-idl")

    def source(self):
        os.makedirs("tango-idl", exist_ok=True)
        idl = Git(self, folder="tango-idl")
        idl.fetch_commit("https://gitlab.com/tango-controls/tango-idl.git", "refs/tags/6.0.2")

    def generate(self):
        cmake = CMakeToolchain(self)
        cmake.generate()

    def configure(self):
        pass

    def _configured_cmake(self):
        cmake = CMake(self)
        cmake.configure()
        return cmake

    def build(self):
        cmake = self._configured_cmake()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tangoidl")