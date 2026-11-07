/**
 * Word splitting for Chinese and Japanese search, part of MkDocs NG.
 *
 * These languages are written without spaces between words, so lunr sees a
 * whole sentence as one word and a search for a word in it finds nothing.
 * This splits such text into words with the browser's built-in
 * `Intl.Segmenter`, or into single characters where that is missing. It is
 * used both when the index is built and for the search query, so the two
 * always split text the same way.
 */
;(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(factory);
  } else if (typeof exports === 'object') {
    module.exports = factory();
  } else {
    factory()(root.lunr);
  }
}(this, function () {
  return function (lunr) {
    // Han, kana and half-width kana.
    var CJK_RE = /[぀-ヿ㐀-䶿一-鿿豈-﫿ｦ-ﾟ]/;
    var WORD_CHAR_RE = /[\wÀ-ɏͰ-ϿЀ-ӿ]/;
    var segmenters = {};

    function getSegmenter(locale) {
      if (!(locale in segmenters)) {
        segmenters[locale] = null;
        if (typeof Intl !== 'undefined' && Intl.Segmenter) {
          try {
            segmenters[locale] = new Intl.Segmenter(locale, {granularity: 'word'});
          } catch (e) {
            // Keep the fallback below.
          }
        }
      }
      return segmenters[locale];
    }

    /* Split `text` into words: a list of `{str, index}`. */
    function segment(text, locale) {
      var words = [];
      var segmenter = getSegmenter(locale);
      if (segmenter) {
        Array.from(segmenter.segment(text)).forEach(function (seg) {
          if (seg.isWordLike) {
            words.push({str: seg.segment, index: seg.index});
          }
        });
        return words;
      }
      // Without Intl.Segmenter: every Chinese or Japanese character is a
      // word, other letters and digits are kept together.
      var start = -1;
      for (var i = 0; i <= text.length; i++) {
        var ch = text.charAt(i);
        var isCJK = ch && CJK_RE.test(ch);
        var isWord = ch && !isCJK && WORD_CHAR_RE.test(ch);
        if (start >= 0 && !isWord) {
          words.push({str: text.slice(start, i), index: start});
          start = -1;
        }
        if (isCJK) {
          words.push({str: ch, index: i});
        } else if (isWord && start < 0) {
          start = i;
        }
      }
      return words;
    }

    /* Wrap a lunr tokenizer so that tokens with Chinese or Japanese text are split into words. */
    function tokenizer(base, locale) {
      var fn = function (obj, metadata) {
        var tokens = base(obj, metadata);
        if (Array.isArray(obj) || !tokens) {
          return tokens;
        }
        var out = [];
        tokens.forEach(function (token) {
          var str = token.toString();
          if (!CJK_RE.test(str)) {
            out.push(token);
            return;
          }
          var position = token.metadata && token.metadata.position;
          var start = position ? position[0] : 0;
          segment(str, locale).forEach(function (word) {
            var meta = lunr.utils.clone(token.metadata) || {};
            meta.position = [start + word.index, word.str.length];
            meta.index = out.length;
            out.push(new lunr.Token(word.str, meta));
          });
        });
        return out;
      };
      return fn;
    }

    /*
     * Split the Chinese or Japanese parts of a search query into words, like
     * the indexed text. A `+` or `-` in front, or a field such as `title:`,
     * applies to each of the words.
     */
    function query(text, tokenize) {
      return text.split(/\s+/).map(function (part) {
        if (!CJK_RE.test(part)) {
          return part;
        }
        var m = /^([+-]?)((?:title|text):)?(.*)$/.exec(part);
        return tokenize(m[3]).map(function (token) {
          return m[1] + (m[2] || '') + token.toString();
        }).join(' ');
      }).join(' ');
    }

    lunr.cjk = {
      test: function (text) { return CJK_RE.test(text); },
      segment: segment,
      tokenizer: tokenizer,
      query: query
    };
  };
}));
