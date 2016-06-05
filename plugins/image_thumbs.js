/**
 * Resizes all Images to thumb, medium and large.
 */

var gm = require('gm'),
    path = require('path'),
    imageMagick = gm.subClass({ imageMagick: true }),
    async = require('async'),
    mkdirp = require('mkdirp'),
    fs = require('fs');

var debug = true;

function createThumbnail(file, files, width, done) {
  var src = path.join('src', files[file].src_filename)
  var thumb_file = file.replace(path.basename(file), path.join(width + 'x', path.basename(file)))
  var cache = path.join('./.cache/', thumb_file)

  fs.readFile(cache, (err, data) => {
    if (err) {
      if(debug) console.log('Resizing ' + src)
      imageMagick(src)
        .resize(width)
        .autoOrient()
        .toBuffer('JPG', function (err, buffer) {
          if (err) console.log(err);
          else {
            mkdirp(path.dirname(cache), function (err) {
              if (err) console.error(err)
              else {
                fs.writeFile(cache, buffer, function(err) {
                    if(err) console.log(err);
                    else if(debug) console.log('Cached ' + cache)
                }); 
              }
            });
            files[thumb_file] = {
             'contents': buffer
            }
            done()
         }
       })
    }
    else {
      if(debug) console.log('Load from cache ' + cache)
      files[thumb_file] = {
        'contents': data
      }
      done()      
    }
  });
}


module.exports = function(dbg) {
  //if(dbg) debug = dbg

  return function(files, metalsmith, done) {
    var batch = []

    for(var file in files) {
      if(file.match(/\.jpg$/) || file.match(/\.JPG$/) || file.match(/\.png$/)) {
        if(files[file].src_filename) {
          batch.push(function(f) { return (cb) => createThumbnail(f, files, 300, cb) }(file))
          batch.push(function(f) { return (cb) => createThumbnail(f, files, 500, cb) }(file))
        }
      }
    }
    async.parallelLimit(batch, 1, done)
   
  };
}

