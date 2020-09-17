from conans import ConanFile, tools, CMake
import os
import glob


class DockingPanesConan(ConanFile):
    name = "dockingpanes"
    license = "GPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/KestrelRadarSensors/dockingpanes"
    topics = ("docking", "panes", "plugin", "Qt5", "Qt")
    description = " is a library for Qt Widgets that implements docking windows that have the look and feel of Visual Studio.\
                    It provides a simple API which allows an application to make use of docking windows with a few calls"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {'shared': False, 'fPIC': True}
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
            self._cmake.definitions["BUILD_EXAMPLES"] = False
            self._cmake.configure(source_folder=self._source_subfolder)
        return self._cmake

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = glob.glob("dockingpanes-*")[0]
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["dockingpanes"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.names["cmake_find_package"] = "DockingPanes"
        self.cpp_info.names["cmake_find_package_multi"] = "DockingPanes"
