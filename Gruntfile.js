var gruntConfig = require('./grunt_config.json');
var webpackConfig = require('./webpack.config');
gruntConfig["webpack"] = {
    options: {
        stats: !process.env.NODE_ENV || process.env.NODE_ENV === 'development'
    },
    prod: webpackConfig,
    dev: Object.assign({ watch: false }, webpackConfig)
};

module.exports = function(grunt) {
  grunt.initConfig(gruntConfig);

  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-webpack');
  grunt.registerTask('default', ['less:production', 'less:components',  'concat:polymercss', 'copy', 'webpack', 'concat:dist']);
};
