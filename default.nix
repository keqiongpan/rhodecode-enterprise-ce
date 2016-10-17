# Nix environment for the community edition
#
# This shall be as lean as possible, just producing the Enterprise
# derivation. For advanced tweaks to pimp up the development environment we use
# "shell.nix" so that it does not have to clutter this file.

args@
{ pythonPackages ? "python27Packages"
, pythonExternalOverrides ? self: super: {}
, doCheck ? true
, ...
}:

let

  # Use nixpkgs from args or import them. We use this indirect approach
  # through args to be able to use the name `pkgs` for our customized packages.
  # Otherwise we will end up with an infinite recursion.
  nixpkgs = args.pkgs or (import <nixpkgs> { });

  # johbo: Interim bridge which allows us to build with the upcoming
  # nixos.16.09 branch (unstable at the moment of writing this note) and the
  # current stable nixos-16.03.
  backwardsCompatibleFetchgit = { ... }@args:
    let
      origSources = nixpkgs.fetchgit args;
    in
    nixpkgs.lib.overrideDerivation origSources (oldAttrs: {
      NIX_PREFETCH_GIT_CHECKOUT_HOOK = ''
        find $out -name '.git*' -print0 | xargs -0 rm -rf
      '';
    });

  # Create a customized version of nixpkgs which should be used throughout the
  # rest of this file.
  pkgs = nixpkgs.overridePackages (self: super: {
    fetchgit = backwardsCompatibleFetchgit;
  });

  # Evaluates to the last segment of a file system path.
  basename = path: with pkgs.lib; last (splitString "/" path);

  # source code filter used as arugment to builtins.filterSource.
  src-filter = path: type: with pkgs.lib;
    let
      ext = last (splitString "." path);
    in
      !builtins.elem (basename path) [
        ".git" ".hg" "__pycache__" ".eggs"
        "bower_components" "node_modules"
        "build" "data" "result" "tmp"] &&
      !builtins.elem ext ["egg-info" "pyc"] &&
      # TODO: johbo: This check is wrong, since "path" contains an absolute path,
      # it would still be good to restore it since we want to ignore "result-*".
      !hasPrefix "result" path;

  basePythonPackages = with builtins; if isAttrs pythonPackages
    then pythonPackages
    else getAttr pythonPackages pkgs;

  buildBowerComponents =
    pkgs.buildBowerComponents or
    (import ./pkgs/backport-16.03-build-bower-components.nix { inherit pkgs; });

  sources = pkgs.config.rc.sources or {};
  version = builtins.readFile ./rhodecode/VERSION;
  rhodecode-enterprise-ce-src = builtins.filterSource src-filter ./.;

  nodeEnv = import ./pkgs/node-default.nix {
    inherit pkgs;
  };
  nodeDependencies = nodeEnv.shell.nodeDependencies;

  bowerComponents = buildBowerComponents {
    name = "enterprise-ce-${version}";
    generated = ./pkgs/bower-packages.nix;
    src = rhodecode-enterprise-ce-src;
  };

  pythonGeneratedPackages = self: basePythonPackages.override (a: {
    inherit self;
  })
  // (scopedImport {
    self = self;
    super = basePythonPackages;
    inherit pkgs;
    inherit (pkgs) fetchurl fetchgit;
  } ./pkgs/python-packages.nix);

  pythonOverrides = import ./pkgs/python-packages-overrides.nix {
    inherit
      basePythonPackages
      pkgs;
  };

  pythonLocalOverrides = self: super: {
    rhodecode-enterprise-ce =
      let
        linkNodeAndBowerPackages = ''
          echo "Export RhodeCode CE path"
          export RHODECODE_CE_PATH=${rhodecode-enterprise-ce-src}
          echo "Link node packages"
          rm -fr node_modules
          mkdir node_modules
          # johbo: Linking individual packages allows us to run "npm install"
          # inside of a shell to try things out. Re-entering the shell will
          # restore a clean environment.
          ln -s ${nodeDependencies}/lib/node_modules/* node_modules/

          echo "DONE: Link node packages"

          echo "Link bower packages"
          rm -fr bower_components
          mkdir bower_components

          ln -s ${bowerComponents}/bower_components/* bower_components/
          echo "DONE: Link bower packages"
        '';
      in super.rhodecode-enterprise-ce.override (attrs: {

      inherit
        doCheck
        version;
      name = "rhodecode-enterprise-ce-${version}";
      releaseName = "RhodeCodeEnterpriseCE-${version}";
      src = rhodecode-enterprise-ce-src;

      buildInputs =
        attrs.buildInputs ++
        (with self; [
          pkgs.nodePackages.bower
          pkgs.nodePackages.grunt-cli
          pkgs.subversion
          pytest-catchlog
          rhodecode-testdata
        ]);

      propagatedBuildInputs = attrs.propagatedBuildInputs ++ (with self; [
        rhodecode-tools
      ]);

      # TODO: johbo: Make a nicer way to expose the parts. Maybe
      # pkgs/default.nix?
      passthru = {
        inherit
          bowerComponents
          linkNodeAndBowerPackages
          myPythonPackagesUnfix
          pythonLocalOverrides;
        pythonPackages = self;
      };

      LC_ALL = "en_US.UTF-8";
      LOCALE_ARCHIVE =
        if pkgs.stdenv ? glibc
        then "${pkgs.glibcLocales}/lib/locale/locale-archive"
        else "";

      preCheck = ''
        export PATH="$out/bin:$PATH"
      '';

      postCheck = ''
        rm -rf $out/lib/${self.python.libPrefix}/site-packages/pytest_pylons
        rm -rf $out/lib/${self.python.libPrefix}/site-packages/rhodecode/tests
      '';

      preBuild = linkNodeAndBowerPackages + ''
        grunt
        rm -fr node_modules
      '';

      postInstall = ''
        # python based programs need to be wrapped
        ln -s ${self.supervisor}/bin/supervisor* $out/bin/
        ln -s ${self.gunicorn}/bin/gunicorn $out/bin/
        ln -s ${self.PasteScript}/bin/paster $out/bin/
        ln -s ${self.channelstream}/bin/channelstream $out/bin/
        ln -s ${self.pyramid}/bin/* $out/bin/  #*/

        # rhodecode-tools
        # TODO: johbo: re-think this. Do the tools import anything from enterprise?
        ln -s ${self.rhodecode-tools}/bin/rhodecode-* $out/bin/

        # note that condition should be restricted when adding further tools
        for file in $out/bin/*; do  #*/
          wrapProgram $file \
              --prefix PYTHONPATH : $PYTHONPATH \
              --prefix PATH : $PATH \
              --set PYTHONHASHSEED random
        done

        mkdir $out/etc
        cp configs/production.ini $out/etc

        echo "Writing meta information for rccontrol to nix-support/rccontrol"
        mkdir -p $out/nix-support/rccontrol
        cp -v rhodecode/VERSION $out/nix-support/rccontrol/version
        echo "DONE: Meta information for rccontrol written"

        # TODO: johbo: Make part of ac-tests
        if [ ! -f rhodecode/public/js/scripts.js ]; then
          echo "Missing scripts.js"
          exit 1
        fi
        if [ ! -f rhodecode/public/css/style.css ]; then
          echo "Missing style.css"
          exit 1
        fi
      '';

    });

    rhodecode-testdata = import "${rhodecode-testdata-src}/default.nix" {
    inherit
      doCheck
      pkgs
      pythonPackages;
    };

  };

  rhodecode-testdata-src = sources.rhodecode-testdata or (
    pkgs.fetchhg {
      url = "https://code.rhodecode.com/upstream/rc_testdata";
      rev = "v0.9.0";
      sha256 = "0k0ccb7cncd6mmzwckfbr6l7fsymcympwcm948qc3i0f0m6bbg1y";
  });

  # Apply all overrides and fix the final package set
  myPythonPackagesUnfix = with pkgs.lib;
    (extends pythonExternalOverrides
    (extends pythonLocalOverrides
    (extends pythonOverrides
             pythonGeneratedPackages)));
  myPythonPackages = (pkgs.lib.fix myPythonPackagesUnfix);

in myPythonPackages.rhodecode-enterprise-ce
