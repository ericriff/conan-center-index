import os
from conan import ConanFile
from conan.tools.cmake import cmake_layout

class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        # We don't want to use Conan's built in cmake support here as it adds in stuff from the host
        # profile (x86_64_gcc8) that we don't want.  Our "host profile" is x86_64_gcc8 as we are
        # building a package that runs on the build machine...
        self.run(f'cmake -S {self.recipe_folder} -B . -D CONAN_DISABLE_CHECK_COMPILER:BOOL=ON')
        self.run('cmake --build . -v')

    def test(self):
        print("== About to run an executable compiled for an embedded architecture. You'll see some errors. ==")
        cmd = "./bin/test_package"
        # Ensure it fails
        try:
            self.run(cmd)
        except:
            pass
        else:
            raise Exception("Cross building failed!")
