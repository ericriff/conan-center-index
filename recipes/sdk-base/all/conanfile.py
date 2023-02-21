from conan import ConanFile
from conan.tools.files import load, save,  get, copy, download, check_sha256, replace_in_file, chdir

import os
import re
import stat

class Pkg(ConanFile):
    name = "sdk-base"
    settings = "arch"

    @property
    def _filenale(self):
        return 'sdk.sh'

    @property
    def _triplet(self):
        return 'aarch64-tdx-linux'

    def _make_absolute_symlinks_relative(self):
        '''Transform the absolute symlinks into relative ones'''
        fixedLinks = []
        topdir = os.getcwd()
        self.output.info("Looking for absolute symlinks in {}".format(topdir))
        for root, dirs, files in os.walk(topdir):
            for filename in files:
                linkPath = os.path.join(root, filename)
                if os.path.islink(linkPath):
                    pointedPath = os.readlink(linkPath)
                    if not pointedPath.startswith("/home"):
                        continue
                    relativePath = os.path.relpath(os.path.dirname(pointedPath), os.path.dirname(linkPath))
                    if relativePath == ".":
                        relativePath = ""
                    os.unlink(linkPath)
                    newPointedPath = os.path.join(relativePath, os.path.basename(pointedPath))
                    os.symlink(newPointedPath, linkPath)
                    self.output.info("Replaced symlink to: {} located in: {} with: {}".format(pointedPath, os.path.dirname(linkPath), newPointedPath))
                    fixedLinks.append(os.path.basename(pointedPath))
        self.output.info("{} absolute symlink(s) found (and fixed): ".format(len(fixedLinks)))
        self.output.info(fixedLinks)

    def _broken_symlinks_remover(self):
        '''Remove every broken symlink in the current directory'''
        self.output.info("Looking for broken symlinks in {}".format(os.getcwd()))
        links = []
        broken = []
        for root, dirs, files in os.walk('.'):
            if root.startswith('./.git'):
                # Ignore the .git directory.
                continue
            for filename in files:
                path = os.path.join(root,filename)
                if os.path.islink(path):
                    target_path = os.readlink(path)
                    # Resolve relative symlinks
                    if not os.path.isabs(target_path):
                        target_path = os.path.join(os.path.dirname(path),target_path)
                    if not os.path.exists(target_path):
                        links.append(path)
                        broken.append(path)
                    else:
                        links.append(path)
                else:
                    # If it's not a symlink we're not interested.
                    continue
        self.output.info(str(len(links)) + ' symlinks found...')
        self.output.info("broken symlink(s) found (and removed):")
        for link in broken:
            self.output.info(link)
            os.unlink(link)

    def source(self):
        # Get the self exracting SDK
        url = self.conan_data["sources"][self.version]["url"]
        sha256 = self.conan_data["sources"][self.version]["sha256"]
        download(self, url, self._filenale)
        check_sha256(self, 'sdk.sh', sha256)

    def package(self):
        #chmod +x
        st = os.stat(self._filenale)
        os.chmod(self._filenale, st.st_mode | stat.S_IEXEC)

        # "  -y         Automatic yes to all prompts"
        # "  -d <dir>   Install the SDK to <dir>"
        # "======== Extensible SDK only options ============"
        # "  -n         Do not prepare the build system"
        # "  -p         Publish mode (implies -n)"
        # "======== Advanced DEBUGGING ONLY OPTIONS ========"
        # "  -S         Save relocation scripts"
        # "  -R         Do not relocate executables"
        # "  -D         use set -x to see what is going on"
        # "  -l         list files that will be extracted"
        cmd = f"./{self._filenale} -y -d {self.package_folder} -S -R"
        self.run(cmd)


        # Fix absolute symlinks that make the package non-relocatable
        with chdir(self, os.path.join(self.package_folder, "sysroots", "x86_64-tdxsdk-linux")):
            self._make_absolute_symlinks_relative()

        # Conan doesn't allow broken symlinks on packages.
        with chdir(self, self.package_folder):
            self._broken_symlinks_remover()

        # Replace the current hardcoded absolute path in the relocation script with a variable
        # expansion.
        replace_in_file(self,
                        os.path.join(self.package_folder, "relocate_sdk.sh"),
                        self.package_folder,
                        "${PACKAGE_FOLDER:?PACKAGE_FOLDER is required}")
        # We also need to convert all single quotes to double quotes so that the shell
        # will expand this variable.
        replace_in_file(self,
                        os.path.join(self.package_folder, "relocate_sdk.sh"),
                        "'",
                        '"')

#        # We also need to patch 'relocate_sdk.py` as it knows the "old_prefix" and will only change
#        # required paths in some places if they match that.  So if we want to relocate a second time
#        # (which we will do in practice), we need to tell it the current prefix so that it can patch
#        # it again.
#        #
#        # We are looking for a line in the file that looks like this and trying to extract
#        # /path/we/care/about:
#        #
#        # old_prefix = re.compile(b("/path/we/care/about"))
#        relocate_sdk_py_contents = load(self, os.path.join(self.package_folder, 'relocate_sdk.py'))
#        old_prefix_str = re.search(r'^old_prefix[ ]*=[^"]*("[^"]+").*$', relocate_sdk_py_contents, re.MULTILINE)[1]
#
#        # Write a file with the old_prefix_str as supplied by the downloaded package indicating that
#        # we have not relocated this package yet - note that we strip the double quotes.
#        save(self, os.path.join(self.package_folder, 'current_relocated_path.txt'), old_prefix_str.strip('"'))

#    def package_info(self):
#        # Should this be here or in the wrapper 'sdk' recipe?
#        bin_path = os.path.join(self.package_folder, "sysroots", "x86_64-tdxsdk-linux", "usr", "bin", self._triplet)
#        sysroot = os.path.join(self.package_folder, "sysroots", "cortexa72-cortexa53-tdx-linux")
#
#        self.cpp_info.bindirs.append(bin_path)
#
#        self.buildenv_info.CC = f"{self._triplet}-gcc"
#        self.buildenv_info.CXX = f"{self._triplet}-g++"
#        self.buildenv_info.CPP = f"{self._triplet}-gcc -E"
#        self.buildenv_info.AS = f"{self._triplet}-as"
#        self.buildenv_info.LD = f"{self._triplet}-ld"
#        self.buildenv_info.GDB = f"{self._triplet}-gdb"
#        self.buildenv_info.STRIP = f"{self._triplet}-strip"
#        self.buildenv_info.RANLIB = f"{self._triplet}-ranlib"
#        self.buildenv_info.OBJCOPY = f"{self._triplet}-objcopy"
#        self.buildenv_info.OBJDUMP = f"{self._triplet}-objdump"
#        self.buildenv_info.READELF = f"{self._triplet}-readelf"
#        self.buildenv_info.AR = f"{self._triplet}-ar"
#        self.buildenv_info.NM = f"{self._triplet}-nm"
#        self.buildenv_info.M4 = "m4"
#        self.buildenv_info.SYSROOT = sysroot
#
#        self.buildenv_info.CFLAGS = f"--sysroot={sysroot}"
#        self.buildenv_info.CPPFLAGS = f"--sysroot={sysroot}"
#        self.buildenv_info.CXXFLAGS = f"--sysroot={sysroot}"
#        self.buildenv_info.LDFLAGS = f"--sysroot={sysroot}"
