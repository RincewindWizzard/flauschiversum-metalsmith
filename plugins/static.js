/**
 * Move static files to the root
 */


module.exports = function() {
  return function(files, metalsmith, done) {
    for (var file in files) {
      if(file.match(/^static\//)) {
        var dst = file.replace('static/', '')
        //console.log(dst) 
        files[dst] = files[file]
        delete files[file]
      }
    }
    done();
  };
}

