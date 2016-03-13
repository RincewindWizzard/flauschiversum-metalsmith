/**
 * Shows a list of latest posts for each category
 */
var path = require('path')


function posts_by_category(files) {
  var categories = { '': [] }
  for (var file in files) {
    var path = file.split('/')

    // check if it is a post
    if(path[0] == 'posts') {
      var category = path[1]
      // only the article is interesting, keep images untouched
      if(path[3] == "index.html") {
        if(!(category in categories)) categories[category] = []

        // add post to category
        categories[category].push(files[file])
        categories[''].push(files[file])
      }
    }
  }

  // sort posts in their categories
  for(var cat in categories) {
    categories[cat].sort((a,b) => a.date < b.date)
  }
  return categories
}

function add_index_pages(files) {
  var categories = posts_by_category(files)
  for(var cat in categories) {
    files[path.join(cat, 'index.html')] = {
      'layout': 'index.jade',
      'category': cat,
      'posts': categories[cat],
      'contents': ''
    }
  }
}

module.exports = function() {
  return function(files, metalsmith, done) {
    add_index_pages(files)
    done();
  };
}

