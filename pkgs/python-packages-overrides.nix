# Overrides for the generated python-packages.nix
#
# This function is intended to be used as an extension to the generated file
# python-packages.nix. The main objective is to add needed dependencies of C
# libraries and tweak the build instructions where needed.

{ pkgs
, basePythonPackages
}:

let
  sed = "sed -i";

  localLicenses = {
    repoze = {
      fullName = "Repoze License";
      url =  http://www.repoze.org/LICENSE.txt;
    };
  };

in

self: super: {

  "appenlight-client" = super."appenlight-client".override (attrs: {
    meta = {
      license = [ pkgs.lib.licenses.bsdOriginal ];
    };
  });

  "beaker" = super."beaker".override (attrs: {
    patches = [
      ./patch_beaker/patch-beaker-lock-func-debug.diff
      ./patch_beaker/patch-beaker-metadata-reuse.diff
    ];
  });

  "future" = super."future".override (attrs: {
    meta = {
      license = [ pkgs.lib.licenses.mit ];
    };
  });

  "testpath" = super."testpath".override (attrs: {
    meta = {
      license = [ pkgs.lib.licenses.mit ];
    };
  });

  "gnureadline" = super."gnureadline".override (attrs: {
    buildInputs = [
      pkgs.ncurses
    ];
    patchPhase = ''
      substituteInPlace setup.py --replace "/bin/bash" "${pkgs.bash}/bin/bash"
    '';
  });

  "gunicorn" = super."gunicorn".override (attrs: {
    propagatedBuildInputs = [
      # johbo: futures is needed as long as we are on Python 2, otherwise
      # gunicorn explodes if used with multiple threads per worker.
      self."futures"
    ];
  });

 "nbconvert" = super."nbconvert".override (attrs: {
    propagatedBuildInputs = attrs.propagatedBuildInputs ++ [
      # marcink: plug in jupyter-client for notebook rendering
      self."jupyter-client"
    ];
  });

  "ipython" = super."ipython".override (attrs: {
    propagatedBuildInputs = attrs.propagatedBuildInputs ++ [
      self."gnureadline"
    ];
  });

  "lxml" = super."lxml".override (attrs: {
    buildInputs = [
      pkgs.libxml2
      pkgs.libxslt
    ];
    propagatedBuildInputs = [
      # Needed, so that "setup.py bdist_wheel" does work
      self."wheel"
    ];
  });

  "mysql-python" = super."mysql-python".override (attrs: {
    buildInputs = [
      pkgs.openssl
    ];
    propagatedBuildInputs = [
      pkgs.libmysql
      pkgs.zlib
    ];
  });

  "psycopg2" = super."psycopg2".override (attrs: {
    propagatedBuildInputs = [
      pkgs.postgresql
    ];
    meta = {
      license = pkgs.lib.licenses.lgpl3Plus;
    };
  });

  "pycurl" = super."pycurl".override (attrs: {
    propagatedBuildInputs = [
      pkgs.curl
      pkgs.openssl
    ];
    preConfigure = ''
      substituteInPlace setup.py --replace '--static-libs' '--libs'
      export PYCURL_SSL_LIBRARY=openssl
    '';
    meta = {
      license = pkgs.lib.licenses.mit;
    };
  });

  "pyramid" = super."pyramid".override (attrs: {
    meta = {
      license = localLicenses.repoze;
    };
  });

  "pyramid-debugtoolbar" = super."pyramid-debugtoolbar".override (attrs: {
    meta = {
      license = [ pkgs.lib.licenses.bsdOriginal localLicenses.repoze ];
    };
  });

  "pysqlite" = super."pysqlite".override (attrs: {
    propagatedBuildInputs = [
      pkgs.sqlite
    ];
    meta = {
      license = [ pkgs.lib.licenses.zlib pkgs.lib.licenses.libpng ];
    };
  });

  "pytest-runner" = super."pytest-runner".override (attrs: {
    propagatedBuildInputs = [
      self."setuptools-scm"
    ];
  });

  "python-ldap" = super."python-ldap".override (attrs: {
    propagatedBuildInputs = attrs.propagatedBuildInputs ++ [
      pkgs.openldap
      pkgs.cyrus_sasl
      pkgs.openssl
    ];
  });

  "python-pam" = super."python-pam".override (attrs: {
    propagatedBuildInputs = [
        pkgs.pam
    ];
    # TODO: johbo: Check if this can be avoided, or transform into
    # a real patch
    patchPhase = ''
      substituteInPlace pam.py \
        --replace 'find_library("pam")' '"${pkgs.pam}/lib/libpam.so.0"'
    '';
    });

  "pyzmq" = super."pyzmq".override (attrs: {
    buildInputs = [
      pkgs.czmq
    ];
  });

  "urlobject" = super."urlobject".override (attrs: {
    meta = {
      license = {
        spdxId = "Unlicense";
        fullName = "The Unlicense";
        url = http://unlicense.org/;
      };
    };
  });

  "docutils" = super."docutils".override (attrs: {
    meta = {
      license = pkgs.lib.licenses.bsd2;
    };
  });

  "colander" = super."colander".override (attrs: {
    meta = {
      license = localLicenses.repoze;
    };
  });

  "pyramid-beaker"  = super."pyramid-beaker".override (attrs: {
    meta = {
      license = localLicenses.repoze;
    };
  });

  "pyramid-mako" = super."pyramid-mako".override (attrs: {
    meta = {
      license = localLicenses.repoze;
    };
  });

  "repoze.lru" = super."repoze.lru".override (attrs: {
    meta = {
      license = localLicenses.repoze;
    };
  });

  "python-editor" = super."python-editor".override (attrs: {
    meta = {
      license = pkgs.lib.licenses.asl20;
    };
  });

  "translationstring" = super."translationstring".override (attrs: {
    meta = {
      license = localLicenses.repoze;
    };
  });

  "venusian" = super."venusian".override (attrs: {
    meta = {
      license = localLicenses.repoze;
    };
  });

  # Avoid that base packages screw up the build process
  inherit (basePythonPackages)
    setuptools;

}
