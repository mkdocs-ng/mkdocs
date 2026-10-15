var in_worker = 'function' === typeof importScripts;
// Outside a Web Worker, this script runs in the page (see main.js), which
// defines `base_url` for the site root.
var base_path = in_worker ? '.' : base_url.replace(/\/?$/, '/') + 'search/';
var allowSearch = false;
var index;
var documents = {};
var lang = ['en'];
var data;

// Send a message to the search UI. From a Web Worker that's `postMessage`.
// When running in the page, call main.js's handler directly instead, leaving
// the page's own `window.postMessage` alone.
function sendMessage(msg) {
  if (in_worker) {
    postMessage(msg);
  } else {
    onWorkerMessage({data: msg});
  }
}

function getScript(script, callback) {
  console.log('Loading script: ' + script);
  var element = document.createElement('script');
  element.src = base_path + script;
  element.onload = callback;
  element.onerror = function () {
    console.log('Error loading script: ' + script);
  };
  document.head.appendChild(element);
}

function getScriptsInOrder(scripts, callback) {
  if (scripts.length === 0) {
    callback();
    return;
  }
  getScript(scripts[0], function() {
    getScriptsInOrder(scripts.slice(1), callback);
  });
}

function loadScripts(urls, callback) {
  if (in_worker) {
    importScripts.apply(null, urls);
    callback();
  } else {
    getScriptsInOrder(urls, callback);
  }
}

function onJSONLoaded () {
  data = JSON.parse(this.responseText);
  var scriptsToLoad = ['lunr.js'];
  if (data.config && data.config.lang && data.config.lang.length) {
    lang = data.config.lang;
  }
  if (lang.length > 1 || lang[0] !== "en") {
    scriptsToLoad.push('lunr.stemmer.support.js');
    if (lang.length > 1) {
      scriptsToLoad.push('lunr.multi.js');
    }
    if (lang.includes("ja") || lang.includes("jp")) {
      scriptsToLoad.push('tinyseg.js');
    }
    for (var i=0; i < lang.length; i++) {
      if (lang[i] != 'en') {
        scriptsToLoad.push(['lunr', lang[i], 'js'].join('.'));
      }
    }
  }
  loadScripts(scriptsToLoad, onScriptsLoaded);
}

function onScriptsLoaded () {
  console.log('All search scripts loaded, building Lunr index...');
  if (data.config && data.config.separator && data.config.separator.length) {
    lunr.tokenizer.separator = new RegExp(data.config.separator);
  }

  if (data.index) {
    index = lunr.Index.load(data.index);
    data.docs.forEach(function (doc) {
      documents[doc.location] = doc;
    });
    console.log('Lunr pre-built index loaded, search ready');
  } else {
    index = lunr(function () {
      if (lang.length === 1 && lang[0] !== "en" && lunr[lang[0]]) {
        this.use(lunr[lang[0]]);
      } else if (lang.length > 1) {
        this.use(lunr.multiLanguage.apply(null, lang));  // spread operator not supported in all browsers: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_operator#Browser_compatibility
      }
      if (!data.config || !data.config.stop_words) {
        // Stop word filtering is disabled: keep words like 'while', 'if',
        // 'for' or 'from' searchable, which lunr would otherwise drop from
        // the index. See https://github.com/mkdocs/mkdocs/issues/4167
        this.pipeline.remove(lunr.stopWordFilter);
        for (var j=0; j < lang.length; j++) {
          if (lang[j] !== 'en' && lunr[lang[j]] && lunr[lang[j]].stopWordFilter) {
            this.pipeline.remove(lunr[lang[j]].stopWordFilter);
          }
        }
      }
      this.field('title');
      this.field('text');
      this.ref('location');

      for (var i=0; i < data.docs.length; i++) {
        var doc = data.docs[i];
        this.add(doc);
        documents[doc.location] = doc;
      }
    });
    console.log('Lunr index built, search ready');
  }
  allowSearch = true;
  sendMessage({config: data.config});
  sendMessage({allowSearch: allowSearch});
}

function init () {
  var oReq = new XMLHttpRequest();
  oReq.addEventListener("load", onJSONLoaded);
  oReq.open("GET", in_worker ? 'search_index.json' : base_path + 'search_index.json');
  oReq.send();
}

function search (query) {
  if (!allowSearch) {
    console.error('Assets for search still loading');
    return;
  }

  var resultDocuments = [];
  var results = index.search(query);
  for (var i=0; i < results.length; i++){
    var result = results[i];
    doc = documents[result.ref];
    doc.summary = doc.text.substring(0, 200);
    resultDocuments.push(doc);
  }
  return resultDocuments;
}

if (in_worker) {
  onmessage = function (e) {
    if (e.data.init) {
      init();
    } else if (e.data.query) {
      postMessage({ results: search(e.data.query) });
    } else {
      console.error("Worker - Unrecognized message: " + e);
    }
  };
}
