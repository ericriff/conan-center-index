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
        # Get the self exracting SDK. The regular `get` method doesn't work
        # since this is not a tarball. This method also fails to infer the filename
        # so we give it a generic 'sdk.sh' name.
        url = self.conan_data["sources"][self.version]["url"]
        sha256 = self.conan_data["sources"][self.version]["sha256"]
        download(self, url, self._filenale)
        check_sha256(self, 'sdk.sh', sha256)

    def package(self):
        # chmod +x
        st = os.stat(self._filenale)
        os.chmod(self._filenale, st.st_mode | stat.S_IEXEC)

        # Extract the SDK, without relocating and keeping the reloc scripts.
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

        # Replace absolute symlinks with relative ones to make the package relocatable
        with chdir(self, os.path.join(self.package_folder, "sysroots", "x86_64-tdxsdk-linux")):
            self._make_absolute_symlinks_relative()

        # Remove broken symlinks, they cause problems further down the road
        with chdir(self, self.package_folder):
            self._broken_symlinks_remover()

        # The "new path" for the toolchain gets hardcoded into relocate_sdk.sh at the time of
        # extracting the SDK. That path will only make sense on the PC where this package was created
        # but we want to relocate on the PC that consumes the package, so we replace it with an env variable.
        replace_in_file(self,
                        os.path.join(self.package_folder, "relocate_sdk.sh"),
                        self.package_folder,
                        "${PACKAGE_FOLDER:?PACKAGE_FOLDER is required}")
        # We also need to convert all single quotes to double quotes so that the shell
        # expands this variable.
        replace_in_file(self,
                        os.path.join(self.package_folder, "relocate_sdk.sh"),
                        "'",
                        '"')
