from conans import ConanFile, CMake, tools
import os

required_conan_version = ">=1.33.0"

class AwsKVScProducer(ConanFile):
    name = "aws-kvs-c-producer"
    description = "Secure Video Ingestion for Analysis & Storage."
    topics = ("conan", "aws", "amazon", "cloud", )
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/awslabs/aws-c-auth"
    license = "Apache-2.0",
    exports_sources = ["CMakeLists.txt", "patches/**"]
    generators = "cmake", "cmake_find_package", "pkg_config"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_common_lws": [True, False],
        "with_common_curl": [True, False],
        "with_crypto": ["openssl", "mbedtls"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_common_lws": False,
        "with_common_curl": True,
        "with_crypto": "openssl"
    }

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    def build_requirements(self):
        self.build_requires("pkgconf/1.7.4")

    def requirements(self):
        self.requires("aws-kvs-pic/cci.20210705")
        if self.options.with_crypto == "openssl":
            self.requires("openssl/1.1.1k")
        else:
            self.requires("mbedtls/2.25.0")
        if self.options.with_common_curl:
            self.requires("libcurl/7.77.0")
        if self.options.with_common_lws:
            self.requires("libwebsockets/4.2.0")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
            destination=self._source_subfolder, strip_root=True)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["BUILD_COMMON_LWS"] = self.options.with_common_lws
        self._cmake.definitions["BUILD_COMMON_CURL"] = self.options.with_common_curl
        self._cmake.definitions["BUILD_DEPENDENCIES"] = False
        self._cmake.definitions["BUILD_TESTING"] = False
        self._cmake.definitions["BUILD_STATIC"] = not self.options.shared
        if self.options.with_crypto == "openssl":
            self._cmake.definitions["USE_OPENSSL"] = True
            self._cmake.definitions["USE_MBEDTLS"] = False
        else:
            self._cmake.definitions["USE_OPENSSL"] = False
            self._cmake.definitions["USE_MBEDTLS"] = True

        self._cmake.configure()
        return self._cmake

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

        # libwebsocket's .pc filename changes if the lib is static
        if self.options.with_common_lws and not self.options["libwebsockets"].shared:
            tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                          "pkg_check_modules(LIBWEBSOCKETS REQUIRED libwebsockets)",
                          "pkg_check_modules(LIBWEBSOCKETS REQUIRED libwebsockets_static)")

        # Do not enforce STATIC on kvsCommonLws and kvsCommonCurl
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "add_library(kvsCommonLws STATIC",
                              "add_library(kvsCommonLws")
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "add_library(kvsCommonCurl STATIC",
                              "add_library(kvsCommonCurl")

        # Let conan handle fPIC
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -fPIC\")",
                              "")

        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        if self.options.with_crypto == "openssl":
            cryptoLibs = ["openssl::crypto", "openssl::ssl"]
        else:
            # FIXME, there are no components support on MbedTLS yet
            # ["MbedTLS", "MbedCrypto"]
            cryptoLibs = ["mbedtls::mbedtls"]

        if self.options.with_common_curl:
            self.cpp_info.components["kvs-common-curl"].libs = ["kvsCommonCurl"]
            self.cpp_info.components["kvs-common-curl"].requires = cryptoLibs
            self.cpp_info.components["kvs-common-curl"].requires.extend(["aws-kvs-pic::kvspicUtils", "libcurl::libcurl"])
            self.cpp_info.components["kvs-common-curl"].names["pkg_config"] = "libkvsCommonCurl"
            self.cpp_info.components["kvs-common-curl"].names["cmake_find_package"] = "kvsCommonCurl"

            self.cpp_info.components["kvs-c-producer"].libs = ["cproducer"]
            self.cpp_info.components["kvs-c-producer"].requires = ["kvs-common-curl", "aws-kvs-pic::kvspic"]
            self.cpp_info.components["kvs-c-producer"].names["pkg_config"] = "libcproducer"
            self.cpp_info.components["kvs-c-producer"].names["cmake_find_package"] = "cproducer"

        if self.options.with_common_lws:
            self.cpp_info.components["kvs-common-lws"].libs = ["kvsCommonLws"]
            self.cpp_info.components["kvs-common-lws"].requires = cryptoLibs
            self.cpp_info.components["kvs-common-lws"].requires.extend(["libwebsockets::libwebsockets", "aws-kvs-pic::kvspicUtils"])
            self.cpp_info.components["kvs-common-lws"].names["pkg_config"] = "libkvsCommonLws"
            self.cpp_info.components["kvs-common-lws"].names["cmake_find_package"]  = "kvsCommonLws"
