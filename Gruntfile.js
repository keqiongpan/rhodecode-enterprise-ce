module.exports = function(grunt) {
  grunt.initConfig({

    dirs: {
      css: "rhodecode/public/css",
      js: {
        "src": "rhodecode/public/js/src",
        "dest": "rhodecode/public/js"
      }
    },
    copy: {
      main: {
        expand: true,
        cwd: 'bower_components',
        src: 'webcomponentsjs/**',
        dest: '<%= dirs.js.dest %>/vendors',
      },
    },
    concat: {
      polymercss:{
        src: [
          // Base libraries
          '<%= dirs.js.src %>/components/shared-styles-prefix.html',
          '<%= dirs.css %>/style-polymer.css',
          '<%= dirs.js.src %>/components/shared-styles-suffix.html'
        ],
        dest: '<%= dirs.js.dest %>/src/components/shared-styles.html',
        nonull: true
      },
      dist: {
        src: [
          // Base libraries
          '<%= dirs.js.src %>/jquery-1.11.1.min.js',
          '<%= dirs.js.src %>/logging.js',
          '<%= dirs.js.src %>/bootstrap.js',
          '<%= dirs.js.src %>/mousetrap.js',
          '<%= dirs.js.src %>/moment.js',
          '<%= dirs.js.src %>/appenlight-client-0.4.1.min.js',
          '<%= dirs.js.src %>/i18n_utils.js',
          '<%= dirs.js.src %>/deform.js',

          // Plugins
          '<%= dirs.js.src %>/plugins/jquery.pjax.js',
          '<%= dirs.js.src %>/plugins/jquery.dataTables.js',
          '<%= dirs.js.src %>/plugins/flavoured_checkbox.js',
          '<%= dirs.js.src %>/plugins/jquery.auto-grow-input.js',
          '<%= dirs.js.src %>/plugins/jquery.autocomplete.js',
          '<%= dirs.js.src %>/plugins/jquery.debounce.js',
          '<%= dirs.js.src %>/plugins/jquery.mark.js',
          '<%= dirs.js.src %>/plugins/jquery.timeago.js',
          '<%= dirs.js.src %>/plugins/jquery.timeago-extension.js',

          // Select2
          '<%= dirs.js.src %>/select2/select2.js',

          // Code-mirror
          '<%= dirs.js.src %>/codemirror/codemirror.js',
          '<%= dirs.js.src %>/codemirror/codemirror_loadmode.js',
          '<%= dirs.js.src %>/codemirror/codemirror_hint.js',
          '<%= dirs.js.src %>/codemirror/codemirror_overlay.js',
          '<%= dirs.js.src %>/codemirror/codemirror_placeholder.js',
          // TODO: mikhail: this is an exception. Since the code mirror modes
          // are loaded "on the fly", we need to keep them in a public folder
          '<%= dirs.js.dest %>/mode/meta.js',
          '<%= dirs.js.dest %>/mode/meta_ext.js',
          '<%= dirs.js.dest %>/rhodecode/i18n/select2/translations.js',

          // Rhodecode utilities
          '<%= dirs.js.src %>/rhodecode/utils/array.js',
          '<%= dirs.js.src %>/rhodecode/utils/string.js',
          '<%= dirs.js.src %>/rhodecode/utils/pyroutes.js',
          '<%= dirs.js.src %>/rhodecode/utils/ajax.js',
          '<%= dirs.js.src %>/rhodecode/utils/autocomplete.js',
          '<%= dirs.js.src %>/rhodecode/utils/colorgenerator.js',
          '<%= dirs.js.src %>/rhodecode/utils/ie.js',
          '<%= dirs.js.src %>/rhodecode/utils/os.js',
          '<%= dirs.js.src %>/rhodecode/utils/topics.js',

          // Rhodecode widgets
          '<%= dirs.js.src %>/rhodecode/widgets/multiselect.js',

          // Rhodecode components
          '<%= dirs.js.src %>/rhodecode/init.js',
          '<%= dirs.js.src %>/rhodecode/connection_controller.js',
          '<%= dirs.js.src %>/rhodecode/codemirror.js',
          '<%= dirs.js.src %>/rhodecode/comments.js',
          '<%= dirs.js.src %>/rhodecode/constants.js',
          '<%= dirs.js.src %>/rhodecode/files.js',
          '<%= dirs.js.src %>/rhodecode/followers.js',
          '<%= dirs.js.src %>/rhodecode/menus.js',
          '<%= dirs.js.src %>/rhodecode/notifications.js',
          '<%= dirs.js.src %>/rhodecode/permissions.js',
          '<%= dirs.js.src %>/rhodecode/pjax.js',
          '<%= dirs.js.src %>/rhodecode/pullrequests.js',
          '<%= dirs.js.src %>/rhodecode/settings.js',
          '<%= dirs.js.src %>/rhodecode/select2_widgets.js',
          '<%= dirs.js.src %>/rhodecode/tooltips.js',
          '<%= dirs.js.src %>/rhodecode/users.js',
          '<%= dirs.js.src %>/rhodecode/utils/notifications.js',
          '<%= dirs.js.src %>/rhodecode/appenlight.js',

          // Rhodecode main module
          '<%= dirs.js.src %>/rhodecode.js'
        ],
        dest: '<%= dirs.js.dest %>/scripts.js',
        nonull: true
      }
    },

    less: {
      development: {
        options: {
          compress: false,
          yuicompress: false,
          optimization: 0
        },
        files: {
          "<%= dirs.css %>/style.css": "<%= dirs.css %>/main.less",
          "<%= dirs.css %>/style-polymer.css": "<%= dirs.css %>/polymer.less"
        }
      },
      production: {
        options: {
          compress: true,
          yuicompress: true,
          optimization: 2
        },
        files: {
          "<%= dirs.css %>/style.css": "<%= dirs.css %>/main.less",
          "<%= dirs.css %>/style-polymer.css": "<%= dirs.css %>/polymer.less"
        }
      }
    },

    watch: {
      less: {
        files: ["<%= dirs.css %>/*.less"],
        tasks: ["less:development", 'concat:polymercss', "vulcanize"]
      },
      js: {
        files: ["<%= dirs.js.src %>/**/*.js", "<%= dirs.js.src %>/components/*.*"],
        tasks: ["vulcanize", "concat:dist"]
      }
    },

    jshint: {
      rhodecode: {
        src: '<%= dirs.js.src %>/rhodecode/**/*.js',
        options: {
          jshintrc: '.jshintrc'
        }
      }
    },
    vulcanize: {
      default: {
        options: {
          abspath: '',
          inlineScripts: true,
          inlineCss: true,
          stripComments: true
        },
        files: {
          '<%= dirs.js.dest %>/rhodecode-components.html': '<%= dirs.js.src %>/components/shared-components.html'
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-vulcanize');
  grunt.loadNpmTasks('grunt-crisper');
  grunt.loadNpmTasks('grunt-contrib-copy');

  grunt.registerTask('default', ['less:production', 'concat:polymercss', 'copy','vulcanize', 'concat:dist']);
};
