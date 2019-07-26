{
  pkgsSrc ? <nixpkgs>,
  pkgs ? import pkgsSrc {},
}:

with pkgs;

let
  # Some of our dependencies are distributed as manylinux1 wheels, but Nix's
  # standard Python environment is not compatible with manylinux1
  # (https://github.com/NixOS/nixpkgs/issues/18484).
  # We can work around this by ensuring the shared libraries that must be
  # provided by the host system as part of the manylinux1 protocol (listed in
  # PEP 513) are made available on LD_LIBRARY_PATH.
  # This is based on the work done in https://github.com/NixOS/nixpkgs/pull/55812.
  manylinux1_lib_map = {
    "libpanelw.so.5" = ncurses5;
    "libncursesw.so.5" = ncurses5;
    "libgcc_s.so.1" = glibc;
    "libstdc++.so.6" = gcc7.cc;
    "libm.so.6" = glibc;
    "libdl.so.2" = glibc;
    "librt.so.1" = glibc;
    "libcrypt.so.1" = glibc;
    "libc.so.6" = glibc;
    "libnsl.so.1" = glibc;
    "libutil.so.1" = glibc;
    "libpthread.so.0" = glibc;
    "libresolv.so.2" = glibc;
    "libX11.so.6" = xorg.libX11;
    "libXext.so.6" = xorg.libXext;
    "libXrender.so.1" = xorg.libXrender;
    "libICE.so.6" = xorg.libICE;
    "libSM.so.6" = xorg.libSM;
    "libGL.so.1" = libGL;
    "libgobject-2.0.so.0" = glib;
    "libgthread-2.0.so.0" = glib;
    "libglib-2.0.so.0" = glib;
  };
  manylinux1_libs = runCommand "manylinux1-libs" {} ''
    mkdir -p $out/lib
    ${lib.concatStringsSep "\n"
      (lib.mapAttrsToList
        (name: pkg: "ln -s ${lib.getOutput "lib" pkg}/lib/${name} $out/lib/${name}")
        manylinux1_lib_map)}
  '';

in stdenv.mkDerivation {
  name = "j5-dev-env";
  buildInputs = [
    gnumake
    graphviz  # for docs
    python3
    python3Packages.poetry
  ];
  LD_LIBRARY_PATH = lib.makeLibraryPath [ manylinux1_libs libusb1 ];
}
