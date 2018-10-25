# Nix environment for the community edition
#
# This shall be as lean as possible, just producing the enterprise-ce
# derivation. For advanced tweaks to pimp up the development environment we use
# "shell.nix" so that it does not have to clutter this file.
#
# Configuration, set values in "~/.nixpkgs/config.nix".
# example
#  {
#    # Thoughts on how to configure the dev environment
#    rc = {
#      codeInternalUrl = "https://usr:token@internal-code.rhodecode.com";
#      sources = {
#        rhodecode-vcsserver = "/home/user/work/rhodecode-vcsserver";
#        rhodecode-enterprise-ce = "/home/user/work/rhodecode-enterprise-ce";
#        rhodecode-enterprise-ee = "/home/user/work/rhodecode-enterprise-ee";
#      };
#    };
#  }

args@
{ pythonPackages ? "python27Packages"
, pythonExternalOverrides ? self: super: {}
, doCheck ? false
, ...
}:
let pkgs_ = (import <nixpkgs> {}); in

let
  # Use nixpkgs from args or import them. We use this indirect approach
  # through args to be able to use the name `pkgs` for our customized packages.
  # Otherwise we will end up with an infinite recursion.
  pkgs = args.pkgs or (import <nixpkgs> {
    overlays = [
      (import ./pkgs/overlays.nix)
    ];
    inherit
      (pkgs_)
      system;
  });

  # Works with the new python-packages, still can fallback to the old
  # variant.
  basePythonPackagesUnfix = basePythonPackages.__unfix__ or (
    self: basePythonPackages.override (a: { inherit self; }));

  # Evaluates to the last segment of a file system path.
  basename = path: with pkgs.lib; last (splitString "/" path);

  # source code filter used as arugment to builtins.filterSource.
  src-filter = path: type: with pkgs.lib;
    let
      ext = last (splitString "." path);
    in
      !builtins.elem (basename path) [
        ".git" ".hg" "__pycache__" ".eggs" ".idea" ".dev"
        "bower_components" "node_modules" "node_binaries"
        "build" "data" "result" "tmp"] &&
      !builtins.elem ext ["egg-info" "pyc"] &&
      # TODO: johbo: This check is wrong, since "path" contains an absolute path,
      # it would still be good to restore it since we want to ignore "result-*".
      !hasPrefix "result" path;

  sources =
    let
      inherit
        (pkgs.lib)
        all
        isString
        attrValues;
      sourcesConfig = pkgs.config.rc.sources or {};
    in
      # Ensure that sources are configured as strings. Using a path
      # would result in a copy into the nix store.
      assert all isString (attrValues sourcesConfig);
      sourcesConfig;

  version = builtins.readFile "${rhodecode-enterprise-ce-src}/rhodecode/VERSION";
  rhodecode-enterprise-ce-src = builtins.filterSource src-filter ./.;

  buildBowerComponents = pkgs.buildBowerComponents;
  nodeEnv = import ./pkgs/node-default.nix {
    inherit
      pkgs;
  };
  nodeDependencies = nodeEnv.shell.nodeDependencies;

  bowerComponents = buildBowerComponents {
    name = "enterprise-ce-${version}";
    generated = ./pkgs/bower-packages.nix;
    src = rhodecode-enterprise-ce-src;
  };

  rhodecode-testdata-src = sources.rhodecode-testdata or (
    pkgs.fetchhg {
      url = "https://code.rhodecode.com/upstream/rc_testdata";
      rev = "v0.10.0";
      sha256 = "0zn9swwvx4vgw4qn8q3ri26vvzgrxn15x6xnjrysi1bwmz01qjl0";
  });

  rhodecode-testdata = import "${rhodecode-testdata-src}/default.nix" {
  inherit
    doCheck
    pkgs
    pythonPackages;
  };

  pythonLocalOverrides = self: super: {
    rhodecode-enterprise-ce =
      let
        linkNodeAndBowerPackages = ''
          export RHODECODE_CE_PATH=${rhodecode-enterprise-ce-src}

          echo "[BEGIN]: Link node packages and binaries"
          # johbo: Linking individual packages allows us to run "npm install"
          # inside of a shell to try things out. Re-entering the shell will
          # restore a clean environment.
          rm -fr node_modules
          mkdir node_modules
          ln -s ${nodeDependencies}/lib/node_modules/* node_modules/
          export NODE_PATH=./node_modules

          rm -fr node_binaries
          mkdir node_binaries
          ln -s ${nodeDependencies}/bin/* node_binaries/
          echo "[DONE ]: Link node packages and binaries"

          echo "[BEGIN]: Link bower packages"
          rm -fr bower_components
          mkdir bower_components
          ln -s ${bowerComponents}/bower_components/* bower_components/
          echo "[DONE ]: Link bower packages"
        '';

        releaseName = "RhodeCodeEnterpriseCE-${version}";
      in super.rhodecode-enterprise-ce.override (attrs: {
      inherit
        doCheck
        version;

      name = "rhodecode-enterprise-ce-${version}";
      releaseName = releaseName;
      src = rhodecode-enterprise-ce-src;
      dontStrip = true; # prevent strip, we don't need it.

      # expose following attributed outside
      passthru = {
        inherit
          rhodecode-testdata
          bowerComponents
          linkNodeAndBowerPackages
          myPythonPackagesUnfix
          pythonLocalOverrides
          pythonCommunityOverrides;

        pythonPackages = self;
      };

      buildInputs =
        attrs.buildInputs or [] ++ [
          rhodecode-testdata
        ];

      #NOTE: option to inject additional propagatedBuildInputs
      propagatedBuildInputs =
        attrs.propagatedBuildInputs or [] ++ [

        ];

      LC_ALL = "en_US.UTF-8";
      LOCALE_ARCHIVE =
        if pkgs.stdenv.isLinux
        then "${pkgs.glibcLocales}/lib/locale/locale-archive"
        else "";

      # Add bin directory to path so that tests can find 'rhodecode'.
      preCheck = ''
        export PATH="$out/bin:$PATH"
      '';

      # custom check phase for testing
      checkPhase = ''
        runHook preCheck
        PYTHONHASHSEED=random py.test -vv -p no:sugar -r xw --cov-config=.coveragerc --cov=rhodecode --cov-report=term-missing rhodecode
        runHook postCheck
      '';

      postCheck = ''
        echo "Cleanup of rhodecode/tests"
        rm -rf $out/lib/${self.python.libPrefix}/site-packages/rhodecode/tests
      '';

      preBuild = ''
        echo "[BEGIN]: Building frontend assets"
        ${linkNodeAndBowerPackages}
        make web-build
        rm -fr node_modules
        rm -fr node_binaries
        echo "[DONE ]: Building frontend assets"
      '';

      postInstall = ''
        # check required files
        if [ ! -f rhodecode/public/js/scripts.js ]; then
          echo "Missing scripts.js"
          exit 1
        fi
        if [ ! -f rhodecode/public/css/style.css ]; then
          echo "Missing style.css"
          exit 1
        fi

        echo "Writing enterprise-ce meta information for rccontrol to nix-support/rccontrol"
        mkdir -p $out/nix-support/rccontrol
        cp -v rhodecode/VERSION $out/nix-support/rccontrol/version
        echo "[DONE ]: enterprise-ce meta information for rccontrol written"

        mkdir -p $out/etc
        cp configs/production.ini $out/etc
        echo "[DONE ]: saved enterprise-ce production.ini into $out/etc"

        cp -r rhodecode/config/rcextensions $out/etc/rcextensions.tmpl
        echo "[DONE ]: saved enterprise-ce rcextensions into $out/etc/rcextensions.tmpl"

        # python based programs need to be wrapped
        mkdir -p $out/bin

        # required binaries from dependencies
        ln -s ${self.supervisor}/bin/supervisorctl $out/bin/
        ln -s ${self.supervisor}/bin/supervisord $out/bin/
        ln -s ${self.pastescript}/bin/paster $out/bin/
        ln -s ${self.channelstream}/bin/channelstream $out/bin/
        ln -s ${self.celery}/bin/celery $out/bin/
        ln -s ${self.gunicorn}/bin/gunicorn $out/bin/
        ln -s ${self.pyramid}/bin/prequest $out/bin/
        ln -s ${self.pyramid}/bin/pserve $out/bin/

        echo "[DONE ]: created symlinks into $out/bin"
        DEPS="$out/bin/supervisorctl \
              $out/bin/supervisord \
              $out/bin/paster \
              $out/bin/channelstream \
              $out/bin/celery \
              $out/bin/gunicorn \
              $out/bin/prequest \
              $out/bin/pserve"

        # wrap only dependency scripts, they require to have full PYTHONPATH set
        # to be able to import all packages
        for file in $DEPS;
        do
          wrapProgram $file \
            --prefix PATH : $PATH \
            --prefix PYTHONPATH : $PYTHONPATH \
            --set PYTHONHASHSEED random
        done

        echo "[DONE ]: enterprise-ce binary wrapping"

        # rhodecode-tools don't need wrapping
        ln -s ${self.rhodecode-tools}/bin/rhodecode-* $out/bin/

      '';
    });

  };

  basePythonPackages = with builtins;
    if isAttrs pythonPackages then
      pythonPackages
    else
      getAttr pythonPackages pkgs;

  pythonGeneratedPackages = import ./pkgs/python-packages.nix {
    inherit
      pkgs;
    inherit
      (pkgs)
      fetchurl
      fetchgit
      fetchhg;
  };

  pythonCommunityOverrides = import ./pkgs/python-packages-overrides.nix {
    inherit pkgs basePythonPackages;
  };

  # Apply all overrides and fix the final package set
  myPythonPackagesUnfix = with pkgs.lib;
    (extends pythonExternalOverrides
    (extends pythonLocalOverrides
    (extends pythonCommunityOverrides
    (extends pythonGeneratedPackages
             basePythonPackagesUnfix))));

  myPythonPackages = (pkgs.lib.fix myPythonPackagesUnfix);

in myPythonPackages.rhodecode-enterprise-ce
