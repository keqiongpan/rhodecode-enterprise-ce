{ system ? builtins.currentSystem
}:

let

  pkgs = import <nixpkgs> { inherit system; };

  inherit (pkgs) fetchurl fetchgit;

  buildPythonPackage = pkgs.python27Packages.buildPythonPackage;
  python = pkgs.python27Packages.python;

  Jinja2 = buildPythonPackage rec {
    name = "Jinja2-2.9.6";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [MarkupSafe];
    src = fetchurl {
      url = "https://pypi.python.org/packages/90/61/f820ff0076a2599dd39406dcb858ecb239438c02ce706c8e91131ab9c7f1/Jinja2-2.9.6.tar.gz";
      md5 = "6411537324b4dba0956aaa8109f3c77b";
    };
  };

  MarkupSafe = buildPythonPackage rec {
    name = "MarkupSafe-1.0";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/4d/de/32d741db316d8fdb7680822dd37001ef7a448255de9699ab4bfcbdf4172b/MarkupSafe-1.0.tar.gz";
      md5 = "2fcedc9284d50e577b5192e8e3578355";
    };
  };

  Pygments = buildPythonPackage {
    name = "Pygments-2.2.0";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/71/2a/2e4e77803a8bd6408a2903340ac498cb0a2181811af7c9ec92cb70b0308a/Pygments-2.2.0.tar.gz";
      md5 = "13037baca42f16917cbd5ad2fab50844";
    };
  };

  Sphinx = buildPythonPackage (rec {
    name = "Sphinx-1.6.5";
    src = fetchurl {
      url = "https://pypi.python.org/packages/8b/7e/b188d9a3b9c938e736e02a74c1363c2888e095d770df2c72b4c312f9fdcb/Sphinx-1.6.5.tar.gz";
      md5 = "cd73118c21ec610432e63e6421ec54f1";
    };
    propagatedBuildInputs = [
        six
        Jinja2
        Pygments
        docutils
        snowballstemmer
        babel
        alabaster
        imagesize
        requests
        setuptools
        sphinxcontrib-websupport
        typing

        # special cases
        pytz
        sphinx_rtd_theme

    ];
  });

  alabaster = buildPythonPackage rec {
    name = "alabaster-0.7.10";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/d0/a5/e3a9ad3ee86aceeff71908ae562580643b955ea1b1d4f08ed6f7e8396bd7/alabaster-0.7.10.tar.gz";
      md5 = "7934dccf38801faa105f6e7b4784f493";
    };
  };

  babel = buildPythonPackage {
    name = "babel-2.5.1";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [pytz];
    src = fetchurl {
      url = "https://pypi.python.org/packages/5a/22/63f1dbb8514bb7e0d0c8a85cc9b14506599a075e231985f98afd70430e1f/Babel-2.5.1.tar.gz";
      md5 = "60228b3ce93a203357158b909afe8ae1";
    };
  };

  certifi = buildPythonPackage {
    name = "certifi-2017.11.5";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/23/3f/8be01c50ed24a4bd6b8da799839066ce0288f66f5e11f0367323467f0cbc/certifi-2017.11.5.tar.gz";
      md5 = "c15ac46ed1fe4b607ff3405928f9a992";
    };
  };

  chardet = buildPythonPackage {
    name = "chardet-3.0.4";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/fc/bb/a5768c230f9ddb03acc9ef3f0d4a3cf93462473795d18e9535498c8f929d/chardet-3.0.4.tar.gz";
      md5 = "7dd1ba7f9c77e32351b0a0cfacf4055c";
    };
  };

  docutils = buildPythonPackage {
    name = "docutils-0.14";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/84/f4/5771e41fdf52aabebbadecc9381d11dea0fa34e4759b4071244fa094804c/docutils-0.14.tar.gz";
      md5 = "c53768d63db3873b7d452833553469de";
    };
  };

  idna = buildPythonPackage {
    name = "idna-2.6";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/f4/bd/0467d62790828c23c47fc1dfa1b1f052b24efdf5290f071c7a91d0d82fd3/idna-2.6.tar.gz";
      md5 = "c706e2790b016bd0ed4edd2d4ba4d147";
    };
  };

  imagesize = buildPythonPackage {
    name = "imagesize-0.7.1";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/53/72/6c6f1e787d9cab2cc733cf042f125abec07209a58308831c9f292504e826/imagesize-0.7.1.tar.gz";
      md5 = "976148283286a6ba5f69b0f81aef8052";
    };
  };

  pytz = buildPythonPackage {
    name = "pytz-2017.3";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/60/88/d3152c234da4b2a1f7a989f89609ea488225eaea015bc16fbde2b3fdfefa/pytz-2017.3.zip";
      md5 = "7006b56c0d68a162d9fe57d4249c3171";
    };
  };

  requests = buildPythonPackage {
    name = "requests-2.18.4";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [chardet idna urllib3 certifi];
    src = fetchurl {
      url = "https://pypi.python.org/packages/b0/e1/eab4fc3752e3d240468a8c0b284607899d2fbfb236a56b7377a329aa8d09/requests-2.18.4.tar.gz";
      md5 = "081412b2ef79bdc48229891af13f4d82";
    };
  };

  six = buildPythonPackage {
    name = "six-1.11.0";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/16/d8/bc6316cf98419719bd59c91742194c111b6f2e85abac88e496adefaf7afe/six-1.11.0.tar.gz";
      md5 = "d12789f9baf7e9fb2524c0c64f1773f8";
    };
  };

  snowballstemmer = buildPythonPackage {
    name = "snowballstemmer-1.2.1";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/20/6b/d2a7cb176d4d664d94a6debf52cd8dbae1f7203c8e42426daa077051d59c/snowballstemmer-1.2.1.tar.gz";
      md5 = "643b019667a708a922172e33a99bf2fa";
    };
  };

  sphinx-rtd-theme = buildPythonPackage {
    name = "sphinx-rtd-theme-0.2.5b1";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/59/e4/9e3a74a3271e6734911d3f549e8439db53b8ac29adf10c8f698e6c86246b/sphinx_rtd_theme-0.2.5b1.tar.gz";
      md5 = "0923473a43bd2527f32151f195f2a521";
    };
  };

  sphinxcontrib-websupport = buildPythonPackage {
    name = "sphinxcontrib-websupport-1.0.1";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/c5/6b/f0630436b931ad4f8331a9399ca18a7d447f0fcc0c7178fb56b1aee68d01/sphinxcontrib-websupport-1.0.1.tar.gz";
      md5 = "84df26463b1ba65b07f926dbe2055665";
    };
  };

  typing = buildPythonPackage {
    name = "typing-3.6.2";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/ca/38/16ba8d542e609997fdcd0214628421c971f8c395084085354b11ff4ac9c3/typing-3.6.2.tar.gz";
      md5 = "143af0bf3afd1887622771f2f1ffe8e1";
    };
  };

  urllib3 = buildPythonPackage {
    name = "urllib3-1.22";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/ee/11/7c59620aceedcc1ef65e156cc5ce5a24ef87be4107c2b74458464e437a5d/urllib3-1.22.tar.gz";
      md5 = "0da7bed3fe94bf7dc59ae37885cc72f7";
    };
  };


  sphinx_rtd_theme = buildPythonPackage rec {
    name = "sphinx-rtd-theme-0.2.5b1";
    buildInputs = [];
    doCheck = false;
    propagatedBuildInputs = [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/59/e4/9e3a74a3271e6734911d3f549e8439db53b8ac29adf10c8f698e6c86246b/sphinx_rtd_theme-0.2.5b1.tar.gz";
      md5 = "0923473a43bd2527f32151f195f2a521";
    };


  };
  # Avoid that setuptools is replaced, this leads to trouble
  # with buildPythonPackage.
  setuptools = pkgs.python27Packages.setuptools;

in python.buildEnv.override {
  inherit python;
  extraLibs = [
    Sphinx
    sphinx_rtd_theme
  ];
}
