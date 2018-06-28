# This file defines how to "build" for packaging.

{ pkgs ? import <nixpkgs> {}
, doCheck ? true
}:

let
  enterprise_ce = import ./default.nix {
    inherit
      doCheck
      pkgs;
  };

in {
  build = enterprise_ce;
}
