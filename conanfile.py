import os
import shutil
import sysconfig
from os.path import join
from conan import ConanFile
from conan.tools.env import Environment
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import replace_in_file, download, unzip, patch, copy
from conan.errors import ConanException, ConanInvalidConfiguration

PTHREADS_WIN32 = "https://github.com/tango-controls/Pthread_WIN32/releases/download/2.9.1/pthreads-win32-2.9.1_{0}.zip"

tango_release='10.1.1'

class CppTangoConan(ConanFile):
    name = "cpptango"
    version = tango_release
    license = "LGPL-3.0"
    author = "Marius Elvert marius.elvert@softwareschneiderei.de"
    url = "https://github.com/softwareschneiderei/conan-cpptango"
    description = "Tango Control System C++ Libraries"
    topics = ("control-system",)
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps"
    options = {
        "shared": [True, False],
        "pthread_windows": [True, False]
    }
    default_options = {
        "shared": False,
        "pthread_windows": False
    }
    file_prefix = "{0}-{1}".format(name, version)
    source_archive = "{0}.tar.gz".format(file_prefix)

    def _download_windows_pthreads(self):
        if self.settings.arch == "x86_64":
            arch = "x64"
        elif self.settings.arch == "x86":
            arch = "win32"
        else:
            raise ConanInvalidConfiguration("Can only build for x86 or x86_64")
        # VS 2019 is ABI compatible to VS 2017, fortunately
        visual_studio_version = min(int(str(self.settings.compiler.version)), 15)
        suffix = "{0}-msvc{1}".format(arch, visual_studio_version)
        url = PTHREADS_WIN32.format(suffix)
        self.output.info("Downloading from {0}".format(url))
        zip_file = "pthreads-win32.zip"
        download(self, url, zip_file)
        unzip(self, zip_file, "pthreads-win32")
        os.unlink(zip_file)

    def requirements(self):
        self.requires("zlib/1.2.11")
        self.requires("libjpeg/9f")
        self.requires("zeromq/4.3.5")
        self.requires("cppzmq/4.11.0", transitive_headers=True)
        self.requires("omniorb/4.3.4", transitive_headers=True)
        self.requires("tango-idl/6.0.2")

    def validate(self):
        check_min_cppstd(self, 17)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        os.makedirs("cppTango", exist_ok=True)
        cpp_tango = Git(self, folder="cppTango")
        cpp_tango.fetch_commit("https://gitlab.com/tango-controls/cppTango.git", f"refs/tags/{tango_release}")

        patch(self, base_path="cppTango", patch_file="patches/001-use-transitive-compile-definitions.patch")
        # Move patches to the cppTango folder
        # for patch_file in PATCHES:
        #     copy(self, patch_file, src=self.recipe_folder, dst=self.source_folder)

    def _idl_compiler(self):
        omniorb_package = self.dependencies["omniorb"].package_folder.replace("\\", "/")
        if self.settings.os == "Windows":
            return f"{omniorb_package}/bin/x86_win32/omniidl.exe"
        return f"{omniorb_package}/bin/omniidl"

    def generate(self):
        self.output.info(f"Using omniORB from {self.dependencies['omniorb'].package_folder}")
        env_and_vars = self._env_and_vars()
        cmake = CMakeToolchain(self)
        defs = {
            'IDL_BASE': join(self.build_folder, "tango-idl").replace("\\", "/"),
            'CMAKE_INSTALL_COMPONENT': "dynamic" if self.options.shared else "static",
            'BUILD_TESTING': 'OFF',
            'TANGO_GIT_REVISION': tango_release,
            'TANGO_USE_TELEMETRY': 'OFF',
            'OMNIIDL': self._idl_compiler(),
            'TANGO_USE_JPEG': 'OFF', # FIXME: currently does not compile on windows, need to patch
        }
        if self.settings.os == "Windows" and self.options.pthread_windows:
            defs["PTHREAD_WIN"] = join(self.build_folder, "pthreads-win32").replace("\\", "/")
        if self.settings.os == "Windows":
            defs["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = "ON" if self.options.shared else "OFF"
            defs["OMNIORB_PKG_LIBRARIES"] = ';'.join(self.dependencies["omniorb"].cpp_info.libs)
            defs["ZMQ_PKG_LIBRARIES"] = ';'.join(self.dependencies["zeromq"].cpp_info.libs)
            defs["PTHREAD_WIN_PKG_LIBRARIES"] = ""
            defs["CMAKE_BUILD_TYPE"] = str(self.settings.build_type).upper()
            defs["TANGO_INSTALL_DEPENDENCIES"] = "OFF"

        defs.update(env_and_vars)
        for key, value in defs.items():
            cmake.variables[key] = value

        cmake.generate()

        # Needs to be the python installation with the .dll, as that is later loaded by omniidl
        python_base = sysconfig.get_config_var('installed_base')

        env = Environment()
        env.append_path("PATH", python_base)
        for key, value in env_and_vars.items():
            env.define(key, value)

        envvars = env.vars(self)
        envvars.save_script("setenv")

    def configure(self):
        if self.settings.os == "Linux" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("Conan needs the setting 'compiler.libcxx' to be 'libstdc++11' on linux")

        self.options["omniorb"].shared = self.options.shared
        self.options["zeromq"].shared = self.options.shared

    def config_options(self):
        if self.settings.os != "Windows":
            del self.options.pthread_windows

    def _env_and_vars(self):
        return {
            "OMNI_BASE": self.dependencies["omniorb"].package_folder.replace("\\", "/"),
            "ZMQ_BASE": self.dependencies["zeromq"].package_folder.replace("\\", "/"),
            "CPPZMQ_BASE": self.dependencies["cppzmq"].package_folder.replace("\\", "/"),
        }

    def _cmake_comment_out(self, file, content):
        replace_in_file(self, file, content, "# " + content)

    def build(self):
        if self.settings.os == "Windows" and self.options.pthread_windows:
            self._download_windows_pthreads()

        source_location = join(self.source_folder, "cppTango")

        # tango seems to only support in-source builds right now
        shutil.copytree(source_location, self.build_folder, ignore=shutil.ignore_patterns(".git"), dirs_exist_ok=True)

        # Disable documentation build via Doxygen
        self._cmake_comment_out("src/CMakeLists.txt", "add_subdirectory(doxygen)",)

        replace_in_file(self, join(self.build_folder, "configure/CMakeLists.txt"), search="cppzmq::cppzmq", replace="cppzmq")

        replace_in_file(self, join(self.build_folder, "configure/functions.cmake"), search="cppzmq::cppzmq", replace="cppzmq")

        target = "tango" # This works for linux and windows/shared
        if self.settings.os == "Linux":
            pass

        cmake = CMake(self)
        cmake.configure(build_script_folder=self.build_folder,cli_args=["--debug-trycompile"])
        cmake.build(target=target)

    def package(self):
        self.output.info(f"Build folder: {self.build_folder}")
        prefix = self.package_folder
        library_component = "dynamic" if self.options.shared else "static"
        for component in [library_component, "headers", "Unspecified"]:
            script = join(self.build_folder, "cmake_install.cmake")
            cmd = f"cmake -DCMAKE_INSTALL_PREFIX={prefix} -DCMAKE_INSTALL_COMPONENT={component} -DCMAKE_INSTALL_CONFIG_NAME={self.settings.build_type} -P {script}"
            self.run(command=cmd, cwd=self.package_folder)

    def package_info(self):
        if self.settings.os == "Windows":
            debug_suffix = "d" if self.settings.build_type == "Debug" else ""
            library_prefix = "lib" if not self.options.shared else ""
            tango_library = library_prefix + "tango" + debug_suffix
            self.cpp_info.libs = [tango_library]
            # Need this for InitCommonControls
            self.cpp_info.system_libs = ["Comctl32"]
        else:
            self.cpp_info.libs = ["tango"]
            self.cpp_info.system_libs = ["dl"]
        self.cpp_info.includedirs = ["include", "include/tango"]
