from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanInvalidConfiguration
import os

class TinyAlsaConan(ConanFile):
    name = "tinyalsa"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/tinyalsa/tinyalsa"
    topics = ("conan", "tiny", "alsa", "sound", "audio", "tinyalsa")
    description = "A small library to interface with ALSA in the Linux kernel"
    options = {"shared": [True, False]}
    default_options = {'shared': False}
    settings = "os", "compiler", "build_type", "arch"

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def configure(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("Only Linux supported")
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("{name}-{version}".format(name=self.name, version=self.version), self._source_subfolder)

    def build(self):
        with tools.chdir(self._source_subfolder):
            env_build = AutoToolsBuildEnvironment(self)
            env_build.make()

    def package(self):
        self.copy("NOTICE", dst="licenses", src=self._source_subfolder)

        with tools.chdir(self._source_subfolder):
            env_build = AutoToolsBuildEnvironment(self)
            env_build_vars = env_build.vars
            env_build_vars['PREFIX'] = self.package_folder
            env_build.install(vars=env_build_vars)

        tools.rmdir(os.path.join(self.package_folder, "share"))

        with tools.chdir(os.path.join(self.package_folder, "lib")):
            files = os.listdir()
            for f in files:
                if (self.options.shared and f.endswith(".a")) or (not self.options.shared and not f.endswith(".a")):
                    os.unlink(f)

    def package_info(self):
        self.cpp_info.libs = ["tinyalsa"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.names["cmake_find_package"] = "TinyALSA"
        self.cpp_info.names["cmake_find_package_multi"] = "TinyALSA"
