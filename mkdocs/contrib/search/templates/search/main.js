function getSearchTermFromLocation() {
  var sPageURL = window.location.search.substring(1);
  var sURLVariables = sPageURL.split('&');
  for (var i = 0; i < sURLVariables.length; i++) {
    var sParameterName = sURLVariables[i].split('=');
    if (sParameterName[0] == 'q') {
      return decodeURIComponent(sParameterName[1].replace(/\+/g, '%20'));
    }
  }
}

function joinUrl (base, path) {
  if (path.substring(0, 1) === "/") {
    // path starts with `/`. Thus it is absolute.
    return path;
  }
  if (base.substring(base.length-1) === "/") {
    // base ends with `/`
    return base + path;
  }
  return base + "/" + path;
}

function escapeHtml (value) {
  return value.replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Titles in the index are HTML (`Tom &amp; Jerry`), the text is plain.
function htmlToText (value) {
  return value ? new DOMParser().parseFromString(value, 'text/html').documentElement.textContent : '';
}

function formatResult (location, title, summary) {
  return '<article><h3><a href="' + joinUrl(base_url, location) + '">'+ escapeHtml(htmlToText(title)) + '</a></h3><p>' + escapeHtml(summary) +'</p></article>';
}

// A Chinese or Japanese character counts as two towards min_search_length,
// so a two-character word such as 搜索 can be searched for.
function queryLength (query) {
  var cjk = query.match(/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]/g);
  return query.length + (cjk ? cjk.length : 0);
}

function displayResults (results) {
  var search_results = document.getElementById("mkdocs-search-results");
  while (search_results.firstChild) {
    search_results.removeChild(search_results.firstChild);
  }
  if (results.length > 0){
    for (var i=0; i < results.length; i++){
      var result = results[i];
      var html = formatResult(result.location, result.title, result.summary);
      search_results.insertAdjacentHTML('beforeend', html);
    }
  } else {
    var noResultsText = search_results.getAttribute('data-no-results-text');
    if (!noResultsText) {
      noResultsText = "No results found";
    }
    search_results.insertAdjacentHTML('beforeend', '<p>' + noResultsText + '</p>');
  }
}

function doSearch () {
  var query = document.getElementById('mkdocs-search-query').value;
  if (queryLength(query) > min_search_length) {
    if (!window.Worker) {
      displayResults(search(query));
    } else {
      searchWorker.postMessage({query: query});
    }
  } else {
    // Clear results for short queries
    displayResults([]);
  }
}

function initSearch () {
  var search_input = document.getElementById('mkdocs-search-query');
  if (search_input) {
    search_input.addEventListener("keyup", doSearch);
  }
  var term = getSearchTermFromLocation();
  if (term) {
    search_input.value = term;
    doSearch();
  }
}

function onWorkerMessage (e) {
  if (e.data.allowSearch) {
    initSearch();
  } else if (e.data.results) {
    var results = e.data.results;
    displayResults(results);
  } else if (e.data.config) {
    min_search_length = e.data.config.min_search_length-1;
  }
}

if (!window.Worker) {
  console.log('Web Worker API not supported');
  // Load the search code into the page itself. It reports back by calling
  // onWorkerMessage directly (see sendMessage in worker.js).
  var script = document.createElement('script');
  script.src = joinUrl(base_url, "search/worker.js");
  script.onload = function () {
    console.log('Loaded worker');
    init();
  };
  script.onerror = function () {
    console.error('Could not load worker.js');
  };
  document.head.appendChild(script);
} else {
  // Wrap search in a web worker
  var searchWorker = new Worker(joinUrl(base_url, "search/worker.js"));
  searchWorker.postMessage({init: true});
  searchWorker.onmessage = onWorkerMessage;
}
