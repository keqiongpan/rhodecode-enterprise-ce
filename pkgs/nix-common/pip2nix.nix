{ pkgs
, pythonPackages
}:

rec {
  pip2nix-src = pkgs.fetchzip {
    url = https://github.com/johbo/pip2nix/archive/51e6fdae34d0e8ded9efeef7a8601730249687a6.tar.gz;
    sha256 = "02a4jjgi7lsvf8mhrxsd56s9a3yg20081rl9bgc2m84w60v2gbz2";
  };

  pip2nix = import pip2nix-src {
    inherit
      pkgs
      pythonPackages;
  };

}
