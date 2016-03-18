/**
 * Sets layout to post.jade and replaces images with their 500px wide thumbnails.
 * Also adds html for slideshows.
 */

var jade = require('jade'),
    slugify = require('slug')
var slideshow_template = './templates/lib/slideshow.jade'

module.exports = function() {
  return function(files, metalsmith, done) {
    // Post content
    for (var file in files) {
      if(file.match(/^posts\/.*index.md$/)) {
        var post = files[file]       
        post['layout'] = 'post.jade'
        post.contents = post.contents.toString('utf8')

        var slideshows = post.contents.match(/!\[[^\]]*\]\([^\)]*\)(\n*!\[[^\]]*\]\([^\)]*\))+/g)
        if(slideshows) slideshows.forEach((slideshow) => {
          var img_list = []
          var images = slideshow.match(/!\[([^\]]*)\]\(([^\)]*)\)/g)
          images.forEach((img) => {
            var img_obj = {}
            img_obj.alt = img.match(/\[([^\]]*)\]/)[1]
            img_obj.src = img.match(/\(([^\)]*)\)/)[1]
            img_obj.full_src = img_obj.src

            // add resized image for lokal assets
            img_obj.id = slugify(img_obj.src)
            img_obj.src = img_obj.src.search('/') > -1 ? img_obj.src : '500x/' + img_obj.src

            img_list.push(img_obj)
          })
          post.contents = post.contents.replace(
            slideshow,
            jade.renderFile(slideshow_template, { 'images': img_list, 'slugify': slugify })
          ).replace(/!\[([^\]]*)\]\(([^\)]*)\)/g, '<div class="center">$&</div>')
        })

          //'\n<div class="slideshow">\n$&\n</div>'
          //'<div class="slide"><div class="description"><p>$1</p></div>![$1](500x/$2)</div>'

      }
    }
    done();
  };
}

