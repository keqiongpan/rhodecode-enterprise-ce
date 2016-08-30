# Backported buildBowerComponents so that we can also use it with the version
# 16.03 which is the current stable at the time of this writing.
#
# This file can be removed once building with 16.03 is not needed anymore.

{ pkgs }:

{ buildInputs ? [], generated, ... } @ attrs:

let
  fetchbower = import ./backport-16.03-fetchbower.nix {
    inherit (pkgs) stdenv lib;
    inherit (pkgs.nodePackages) bower2nix;
  };

  # Fetches the bower packages. `generated` should be the result of a
  # `bower2nix` command.
  bowerPackages = import generated {
    inherit (pkgs) buildEnv;
    inherit fetchbower;
  };

in pkgs.stdenv.mkDerivation (
  attrs
  //
  {
    name = "bower_components-" + attrs.name;

    inherit bowerPackages;

    builder = builtins.toFile "builder.sh" ''
      source $stdenv/setup

      # The project's bower.json is required
      cp $src/bower.json .

      # Dereference symlinks -- bower doesn't like them
      cp  --recursive --reflink=auto       \
          --dereference --no-preserve=mode \
          $bowerPackages bc

      # Bower install in offline mode -- links together the fetched
      # bower packages.
      HOME=$PWD bower \
          --config.storage.packages=bc/packages \
          --config.storage.registry=bc/registry \
          --offline install

      # Sets up a single bower_components directory within
      # the output derivation.
      mkdir -p $out
      mv bower_components $out
    '';

    buildInputs = buildInputs ++ [
      pkgs.git
      pkgs.nodePackages.bower
    ];
  }
)
