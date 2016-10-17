{ pkgs ? (import <nixpkgs> {})
, vcsserverPath ? "./../rhodecode-vcsserver"
, vcsserverNix ? "shell.nix"
, doCheck ? true
}:

let

  # Convert vcsserverPath to absolute path.
  vcsserverAbsPath =
    if pkgs.lib.strings.hasPrefix "/" vcsserverPath then
      builtins.toPath "${vcsserverPath}"
    else
      builtins.toPath ("${builtins.getEnv "PWD"}/${vcsserverPath}");

  # Import vcsserver if nix file exists, otherwise set it to null.
  vcsserver =
    let
      nixFile = "${vcsserverAbsPath}/${vcsserverNix}";
    in
      if pkgs.lib.pathExists "${nixFile}" then
        builtins.trace
          "Using local vcsserver from ${nixFile}"
          import "${nixFile}" {inherit pkgs;}
      else
          null;

  hasVcsserver = !isNull vcsserver;

  enterprise-ce = import ./default.nix {
    inherit pkgs doCheck;
  };

  ce-pythonPackages = enterprise-ce.pythonPackages;

in enterprise-ce.override (attrs: {
  # Avoid that we dump any sources into the store when entering the shell and
  # make development a little bit more convenient.
  src = null;

  buildInputs =
    attrs.buildInputs ++
    pkgs.lib.optionals (hasVcsserver) vcsserver.propagatedNativeBuildInputs ++
    (with ce-pythonPackages; [
      bumpversion
      invoke
      ipdb
    ]);

  # Somewhat snappier setup of the development environment
  # TODO: think of supporting a stable path again, so that multiple shells
  #       can share it.
  postShellHook = ''
    # Custom prompt to distinguish from other dev envs.
    export PS1="\n\[\033[1;32m\][CE-shell:\w]$\[\033[0m\] "

    tmp_path=$(mktemp -d)
    export PATH="$tmp_path/bin:$PATH"
    export PYTHONPATH="$tmp_path/${ce-pythonPackages.python.sitePackages}:$PYTHONPATH"
    mkdir -p $tmp_path/${ce-pythonPackages.python.sitePackages}
    python setup.py develop --prefix $tmp_path --allow-hosts ""
    '' + enterprise-ce.linkNodeAndBowerPackages +
    pkgs.lib.strings.optionalString (hasVcsserver) ''
      # Setup the vcsserver development egg.
      pushd ${vcsserverAbsPath}
      python setup.py develop --prefix $tmp_path --allow-hosts ""
      popd
    '';

})
