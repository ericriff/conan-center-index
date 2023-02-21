from conan import ConanFile
from conan.tools.files import get, copy, download, check_sha256

import os
import shutil
import subprocess

class Pkg(ConanFile):
    name = "sdk"
    settings = "arch"
    build_policy = "missing"
    upload_policy = "skip"

    @property
    def _filenale(self):
        return 'sdk.sh'

    @property
    def _triplet(self):
        return 'aarch64-tdx-linux'

    def build_requirements(self):
        self.tool_requires("sdk-base/0.1")

    def package(self):
        # Whatever modification, customization, RPATHs, symlinks, etc
        pkg_folder = self.dependencies.build["sdk-base"].package_folder
        shutil.copytree(src=pkg_folder, dst=self.package_folder, dirs_exist_ok=True, ignore_dangling_symlinks=True)
        self.output.info(f'Relocating SDk package')

        # Run the relocation script, telling it where to relocate to with the "PACKAGE_FOLDER" environment variable.
        p = subprocess.Popen([os.path.join(self.package_folder, 'relocate_sdk.sh')],
                             env=dict(os.environ, PACKAGE_FOLDER=self.package_folder),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdo, stde = p.communicate()

        if stde.decode() != "":
            self.output.error(stde)
            raise RuntimeError(f'Relocation of SDKbrewst in {self.package_folder} failed')

    def package_info(self):
        # Should this be here or in the wrapper 'sdk' recipe?
        bin_path = os.path.join(self.package_folder, "sysroots", "x86_64-tdxsdk-linux", "usr", "bin", self._triplet)
        sysroot = os.path.join(self.package_folder, "sysroots", "cortexa72-cortexa53-tdx-linux")

        self.cpp_info.bindirs.append(bin_path)

        self.buildenv_info.CC = f"{self._triplet}-gcc"
        self.buildenv_info.CXX = f"{self._triplet}-g++"
        self.buildenv_info.CPP = f"{self._triplet}-gcc -E"
        self.buildenv_info.AS = f"{self._triplet}-as"
        self.buildenv_info.LD = f"{self._triplet}-ld"
        self.buildenv_info.GDB = f"{self._triplet}-gdb"
        self.buildenv_info.STRIP = f"{self._triplet}-strip"
        self.buildenv_info.RANLIB = f"{self._triplet}-ranlib"
        self.buildenv_info.OBJCOPY = f"{self._triplet}-objcopy"
        self.buildenv_info.OBJDUMP = f"{self._triplet}-objdump"
        self.buildenv_info.READELF = f"{self._triplet}-readelf"
        self.buildenv_info.AR = f"{self._triplet}-ar"
        self.buildenv_info.NM = f"{self._triplet}-nm"
        self.buildenv_info.M4 = "m4"
        self.buildenv_info.SYSROOT = sysroot

        self.buildenv_info.CFLAGS = f"--sysroot={sysroot}"
        self.buildenv_info.CPPFLAGS = f"--sysroot={sysroot}"
        self.buildenv_info.CXXFLAGS = f"--sysroot={sysroot}"
        self.buildenv_info.LDFLAGS = f"--sysroot={sysroot}"
