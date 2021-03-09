from conans import ConanFile, tools
import os
from textwrap import dedent

class QwtConan(ConanFile):
    name = "qwt"
    license = "LGPL"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://qwt.sourceforge.io/"
    topics = "qt", "GUI", "plot", "scale", "dial", "slider"
    description = "The Qwt library contains GUI Components and utility classes which are " \
                    "primarily useful for programs with a technical background. Beside a " \
                    "framework for 2D plots it provides scales, sliders, dials, compasses, " \
                    "thermometers, wheels and knobs to control or display values, arrays, or " \
                    "ranges of type double."
    options = {
        "shared": [True, False],
        "plot": [True, False],
        "widgets": [True, False],
        "svg": [True, False],
        "opengl": [True, False],
        "mathml": [True, False],
        "designer": [True, False],
        "playground": [True, False]
    }
    default_options = {
        "shared": False,
        "plot": True,
        "widgets": True,
        "svg": True,
        "opengl": True,
        "mathml": False,
        "designer": False,
        "playground": False
    }

    generators = "qmake"
    settings = "os", "compiler", "build_type", "arch"

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        self.requires("qt/5.15.2")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        tools.replace_in_file(os.path.join(self._source_subfolder, "qwt.pro"),
                            "CONFIG   += ordered",
                            dedent('''\
                            CONFIG   += ordered
                            CONFIG += conan_basic_setup
                            include($$OUT_PWD/../conanbuildinfo.pri)
                            ''')
                            )

        qwt_config_file = os.path.join(self._source_subfolder, "qwtconfig.pri" )
        if not self.options.shared:
            tools.replace_in_file(qwt_config_file, "QWT_CONFIG           += QwtDll", "#QWT_CONFIG           += QwtDll")
        if not self.options.plot:
            tools.replace_in_file(qwt_config_file, "QWT_CONFIG       += QwtPlot", "#QWT_CONFIG       += QwtPlot")
        if not self.options.widgets:
            tools.replace_in_file(qwt_config_file, "QWT_CONFIG     += QwtWidgets", "#QWT_CONFIG     += QwtWidgets")
        if not self.options.widgets:
            tools.replace_in_file(qwt_config_file, "QWT_CONFIG     += QwtSvg", "#QWT_CONFIG     += QwtSvg")
        if not self.options.opengl:
            tools.replace_in_file(qwt_config_file, "QWT_CONFIG     += QwtOpenGL", "#QWT_CONFIG     += QwtOpenGL")
        if self.options.mathml:
            tools.replace_in_file(qwt_config_file, "#QWT_CONFIG     += QwtMathML", "QWT_CONFIG     += QwtMathML")
        if not self.options.designer:
            tools.replace_in_file(qwt_config_file, "QWT_CONFIG     += QwtDesigner", "#QWT_CONFIG     += QwtDesigner")
        if self.options.playground:
            tools.replace_in_file(qwt_config_file, "#QWT_CONFIG     += QwtPlayground", "QWT_CONFIG     += QwtPlayground")

        tools.replace_in_file(qwt_config_file, "    QWT_INSTALL_PREFIX    = /usr/local/qwt-$$QWT_VERSION",
                                               "    QWT_INSTALL_PREFIX    = {}".format(self.package_folder))

        qwt_build_file = os.path.join(self._source_subfolder, "qwtbuild.pri" )
        if self.settings.build_type == "Debug":
            tools.replace_in_file(qwt_build_file, "+= release", "+= debug")

        with tools.chdir(self._source_subfolder):
            self.run("qmake -r qwt.pro")
            self.run("make -j{}".format(tools.cpu_count()))

    def package(self):
        with tools.chdir(self._source_subfolder):
            self.run("make install")
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        tools.rmdir(os.path.join(self.package_folder, "doc"))
        tools.rmdir(os.path.join(self.package_folder, "features"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.names["cmake_find_package"] = "Qwt"
        self.cpp_info.names["cmake_find_package_multi"] = "Qwt"
