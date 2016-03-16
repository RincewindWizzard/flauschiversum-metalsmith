/**
 * Sets layout to post.jade and replaces images with their 500px wide thumbnails.
 * Also adds html for slideshows.
 */

module.exports = function() {
  return function(files, metalsmith, done) {
    // Post content
    for (var file in files) {
      if(file.match(/^posts\/.*index.md$/)) {
        var post = files[file]       
        post['layout'] = 'post.jade'
        post.contents = post.contents.toString('utf8')
          .replace(/!\[([^\]]*)\]\(([^\)]*)\)/g, '<div class="slide">![$1](500x/$2)<span>$1</span></div>') // Images to thumbnails
          .replace(/!\[[^\]]*\]\([^\)]*\)(\n*!\[[^\]]*\]\([^\)]*\))+/g, '\n<div class="slideshow">\n$&\n</div>')

      }
    }
    done();
  };
}

