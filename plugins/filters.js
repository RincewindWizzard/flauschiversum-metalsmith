/**
 * Adds filters for the jade templates.
 */

var moment = require('moment')

module.exports = function() {
  return function(files, metalsmith, done) {
    for (var file in files) {
      if(file.match(/\.html$/)) {
        files[file]['moment'] = moment
      }
    }
    done();
  };
}

