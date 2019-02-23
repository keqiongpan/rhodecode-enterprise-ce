# This file defines how to "build" for packaging.

{ pkgs ? import <nixpkgs> {}
, system ? builtins.currentSystem
, doCheck ? false
}:

let
  enterprise_ce = import ./default.nix {
    inherit
      doCheck
      system;

    # disable checkPhase for build
    checkPhase = ''
    '';

  };

in {
  build = enterprise_ce;
}
