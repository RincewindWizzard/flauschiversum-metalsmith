/**
 * Moves posts to pretty permalinks.
 * filename: /:year/:month/:title/index.html
 */

var moment = require('moment'),
    slugify = require('slug')
    path = require('path')

slugify.defaults.mode ='rfc3986'


module.exports = function() {
  return function(files, metalsmith, done) {

    var mv = {}
    // Post content
    for (var file in files) {
      if(file.match(/^posts\/.*index.html$/)) {
        var post = files[file]       
        var dst = moment(post.date).format('YYYY/MM/') + slugify(post.title)
        post.url = '/' + dst + '/'
        if(post.image) post.image = path.join(post.url, '300x', post.image)
        mv[path.dirname(file)] = dst
      }
    }

    // Post images
    for (var file in files) {
      if(file.match(/^posts\//)) {
        files[file].src_filename = file
        files[path.join(mv[path.dirname(file)], path.basename(file))] = files[file]
        delete files[file]
      }
    }

    done();
  };
}

