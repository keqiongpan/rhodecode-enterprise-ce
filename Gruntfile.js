var gruntConfig = require('./grunt_config.json');

module.exports = function(grunt) {
  grunt.initConfig(gruntConfig);

  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-vulcanize');
  grunt.loadNpmTasks('grunt-crisper');
  grunt.loadNpmTasks('grunt-contrib-copy');

  grunt.registerTask('default', ['less:production', 'less:components', 'concat:polymercss', 'copy', 'concat:dist', 'vulcanize', 'crisper']);
};
