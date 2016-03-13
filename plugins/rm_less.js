/**
 * Removes *.less files from source tree, so only css files persist building.
 */

module.exports = function() {
  return function(files, metalsmith, done) {
    for (var file in files) {
      if(file.match(/\.less$/)) delete files[file]
    }
    done();
  };
}

