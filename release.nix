# This file defines how to "build" for packaging.

{ doCheck ? false
}:

let
  enterprise_ce = import ./default.nix {
    inherit
      doCheck;

    # disable checkPhase for build
    checkPhase = ''
    '';

  };

in {
  build = enterprise_ce;
}
