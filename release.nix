# This file defines how to "build" for packaging.

{ pkgs ? import <nixpkgs> {}
, doCheck ? false
}:

let
  enterprise_ce = import ./default.nix {
    inherit
      doCheck
      pkgs;

    # disable checkPhase for build
    checkPhase = ''
    '';

  };

in {
  build = enterprise_ce;
}
