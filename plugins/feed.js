/**
 * Creates an RSS feed of the posts.
 */

var RSS = require('rss'),
    moment = require('moment'),
    slugify = require('slug'),
    path = require('path')

module.exports = function() {
  return function(files, metalsmith, done) {
    var feed = new RSS({
      title: 'Flauschiversum',
      description: 'Mehr als nur eine Masche! Jeden Sonntag neue Basteltipps von Ermeline Wollknoll!',
      feed_url: 'https://flauschiversum.de/rss.xml',
      site_url: 'https://flauschiversum.de/',
      copyright: moment().format('YYYY ') + 'Ermeline Wollknoll',
      language: 'de',
      categories: ['Basteln', 'Brandings', 'Filzen', 'Malen', 'Nähen', 'Wolle'],
      pubDate: new Date(),
      ttl: 60 * 24 // Caches for max one day
    })

    var posts = []
    for (var file in files) {
      var path = file.split('/')
      // check if it is a post
      if(path[0] == 'posts') {
        var category = path[1]
        // only the article is interesting, keep images untouched
        if(path[3] == "index.md") {
          files[file].src = file
          posts.push(files[file])
        }
      }
    }
    posts.sort((a,b) => b.date - a.date)
    posts.forEach((post, i) => {
      if(!post.title) {
        console.log("[WARNING] Post hat keinen Titel")
	throw "title undefined!"
      }
      feed.item({
        title:  post.title,
        description: post.description,
        url: 'https://flauschiversum.de/' + moment(post.date).format('YYYY/MM/') + slugify(post.title.replace(/&/g, '')).replace(/\./g, '') + '/',
        categories: [post.category],
        author: post.author,
        date: post.date
      })
    })

    files['rss.xml'] = {
      'contents': feed.xml({indent: true})
    }

    
    done();
  };
}

