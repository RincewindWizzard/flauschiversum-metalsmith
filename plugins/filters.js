/**
 * Adds filters for the jade templates.
 */

var moment = require('moment'),
    slugify = require('slug')

module.exports = function() {
  return function(files, metalsmith, done) {
    for (var file in files) {
      if(file.match(/\.html$/)) {
        files[file]['moment'] = moment
        files[file]['slugify'] = slugify
      }
    }
    done();
  };
}

