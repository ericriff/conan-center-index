from conans import ConanFile, CMake, tools
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package", "pkg_config"

    def build(self):
        cmake = CMake(self)
        if self.options["aws-kvs-c-producer"].with_common_curl:
            cmake.definitions["TEST_COMMON_CURL"] = True
        if self.options["aws-kvs-c-producer"].with_common_lws:
            cmake.definitions["TEST_COMMON_LWS"] = True
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self):
            bin_path = os.path.join("bin", "test_package")
            self.run(bin_path, run_environment=True)
