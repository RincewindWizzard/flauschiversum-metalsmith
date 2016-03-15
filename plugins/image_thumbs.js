/**
 * Resizes all Images to thumb, medium and large.
 */

var gm = require('gm'),
    path = require('path'),
    imageMagick = gm.subClass({ imageMagick: true }),
    async = require('async'),
    mkdirp = require('mkdirp'),
    fs = require('fs');

function createThumbnail(file, files, width, done) {
  var src = path.join('src', files[file].src_filename)
  var thumb_file = file.replace(path.basename(file), path.join(width + 'x', path.basename(file)))
  var cache = path.join('/tmp/flauschiversum-metalsmith/', thumb_file)

  fs.readFile(cache, (err, data) => {
    if (err) {
      console.log('Resizing ' + src)
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
                    else console.log('Cached ' + cache)
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
      console.log('Load from cache ' + cache)
      files[thumb_file] = {
        'contents': data
      }
      done()      
    }
  });
}


module.exports = function() {
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
    async.parallel(batch, done)
   
  };
}

