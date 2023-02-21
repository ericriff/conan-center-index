from conan import ConanFile
from conan.tools.files import load, save,  get, copy, download, check_sha256, replace_in_file, chdir
from conan.tools.files.symlinks import absolute_to_relative_symlinks,remove_broken_symlinks,remove_external_symlinks

import os
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

        # Handle absolute and broken symlinks
        absolute_to_relative_symlinks(self, self.package_folder)
        remove_external_symlinks(self, self.package_folder)
        remove_broken_symlinks(self, self.package_folder)

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
