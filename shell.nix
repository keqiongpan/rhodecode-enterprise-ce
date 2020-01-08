# This file contains the adjustments which are desired for a development
# environment.

{ pkgs ? (import <nixpkgs> {})
, pythonPackages ? "python27Packages"
, doCheck ? false
, sourcesOverrides ? {}
, doDevelopInstall ? true
, doReleaseInstall ? false
}:

let
  # Get sources from config and update them with overrides.
  sources = (pkgs.config.rc.sources or {}) // sourcesOverrides;

  enterprise-ce = import ./default.nix {
    inherit
      pythonPackages
      doCheck;
  };

  ce-pythonPackages = enterprise-ce.pythonPackages;

  # This method looks up a path from `pkgs.config.rc.sources` and returns a
  # shell script which does a `python setup.py develop` installation of it. If
  # no path is found it will return an empty string.
  optionalDevelopInstall = attributeName:
    let
      path = pkgs.lib.attrByPath [attributeName] null sources;
      doIt = doDevelopInstall && path != null;

    in
      # do develop installation with empty hosts to skip any package duplicates to
      # be replaced. This only pushes the package to be locally available
      pkgs.lib.optionalString doIt (''
        echo "[BEGIN] Develop install of '${attributeName}' from '${path}'"
        pushd ${path}
        python setup.py develop --prefix $tmp_path --allow-hosts ""
        popd
        echo "[DONE] Develop install of '${attributeName}' from '${path}'"
        echo ""
      '');

  # This method looks up a path from `pkgs.config.rc.sources` and imports the
  # default.nix file if it exists. It returns the list of build inputs. If no
  # path is found it will return an empty list.
  optionalDevelopInstallBuildInputs = attributeName:
    let
      path = pkgs.lib.attrByPath [attributeName] null sources;
      doIt = doDevelopInstall && path != null && pkgs.lib.pathExists "${nixFile}";
      nixFile = "${path}/default.nix";

      derivate = import "${nixFile}" {
        inherit
          doCheck
          pythonPackages;
      };
    in
      pkgs.lib.lists.optionals doIt (
        derivate.propagatedBuildInputs
      );

  developInstalls = [ "rhodecode-vcsserver" ];

in enterprise-ce.override (attrs: {
  # Avoid that we dump any sources into the store when entering the shell and
  # make development a little bit more convenient.
  src = null;

  # Add dependencies which are useful for the development environment.
  buildInputs =
    attrs.buildInputs ++
    (with ce-pythonPackages;
      [ ipdb ]
      ++ pkgs.lib.lists.optionals doReleaseInstall (
        [invoke bumpversion]
      )
    );

  # place to inject some required libs from develop installs
  propagatedBuildInputs =
    attrs.propagatedBuildInputs ++
    pkgs.lib.lists.concatMap optionalDevelopInstallBuildInputs developInstalls;


  # Make sure we execute both hooks
  shellHook = ''
    runHook preShellHook
    runHook postShellHook
  '';

  preShellHook = ''
    echo "Entering CE-Shell"

    # Custom prompt to distinguish from other dev envs.
    export PS1="\n\[\033[1;32m\][CE-shell:\w]$\[\033[0m\] "

    echo "Building frontend assets"
    ${enterprise-ce.linkNodePackages}

    # Setup a temporary directory.
    tmp_path=$(mktemp -d)
    export PATH="$tmp_path/bin:$PATH"
    export PYTHONPATH="$tmp_path/${ce-pythonPackages.python.sitePackages}:$PYTHONPATH"
    mkdir -p $tmp_path/${ce-pythonPackages.python.sitePackages}

    # Develop installation
    echo "[BEGIN]: develop install of rhodecode-enterprise-ce"
    python setup.py develop --prefix $tmp_path --allow-hosts ""
  '';

  postShellHook = ''
    echo "** Additional develop installs **"
    '' +
    pkgs.lib.strings.concatMapStrings optionalDevelopInstall developInstalls
    + ''
  '';

})
