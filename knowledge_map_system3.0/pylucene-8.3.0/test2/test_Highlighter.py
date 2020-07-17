# ====================================================================
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ====================================================================

import sys, lucene, unittest
from PyLuceneTestCase import PyLuceneTestCase

from java.io import StringReader
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, TextField
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search.highlight import \
    Highlighter, QueryScorer, SimpleFragmenter
from org.apache.pylucene.search.highlight import PythonFormatter


class TestFormatter(PythonFormatter):

    def __init__(self, testCase):
        super(TestFormatter, self).__init__()
        self.testCase = testCase

    def highlightTerm(self, originalText, group):
        if group.getTotalScore() <= 0:
            return originalText;

        self.testCase.countHighlightTerm()

        return "<b>" + originalText + "</b>"


class HighlighterTestCase(PyLuceneTestCase):
    """
    Unit tests ported from Java Lucene.
    2004 by Yura Smolsky ;)
    """

    FIELD_NAME = "contents"
    texts = [ "A wicked problem is one for which each attempt to create a solution changes the understanding of the problem.  Wicked problems cannot be solved in a traditional linear fashion, because the problem definition evolves as new possible solutions are considered and/or implemented."
              "Wicked problems always occur in a social context -- the wickedness of the problem reflects the diversity among the stakeholders in the problem."
              "From http://cognexus.org/id42.htm"
              "Most projects in organizations -- and virtually all technology-related projects these days -- are about wicked problems.  Indeed, it is the social complexity of these problems, not their technical complexity, that overwhelms most current problem solving and project management approaches."
              "This text has a typo in referring to whicked problems" ];

    def __init__(self, *args):
        super(HighlighterTestCase, self).__init__(*args)

        self.parser = QueryParser(self.FIELD_NAME, StandardAnalyzer())

    def setUp(self):
        super(HighlighterTestCase, self).setUp()

        self.analyzer = StandardAnalyzer()

        writer = self.getWriter(analyzer=self.analyzer)
        for text in self.texts:
            self.addDoc(writer, text)

        writer.commit()
        writer.close()
        self.reader = self.getReader()
        self.numHighlights = 0;

    def testSimpleHighlighter(self):

        self.doSearching("Wicked")
        highlighter = Highlighter(QueryScorer(self.query))
        highlighter.setTextFragmenter(SimpleFragmenter(40))
        maxNumFragmentsRequired = 2

        for scoreDoc in self.scoreDocs:
            text = self.searcher.doc(scoreDoc.doc).get(self.FIELD_NAME)
            tokenStream = self.analyzer.tokenStream(self.FIELD_NAME,
                                                    StringReader(text))

            result = highlighter.getBestFragments(tokenStream, text,
                                                  maxNumFragmentsRequired,
                                                  "...")
            print "\t", result

        # Not sure we can assert anything here - just running to check we don't
        # throw any exceptions

    def testGetBestFragmentsSimpleQuery(self):

        self.doSearching("Wicked")
        self.doStandardHighlights()
        self.assert_(self.numHighlights == 3,
                     ("Failed to find correct number of highlights, %d found"
                      %(self.numHighlights)))

    def doSearching(self, queryString):

        self.searcher = self.getSearcher()
        self.query = self.parser.parse(queryString)
        # for any multi-term queries to work (prefix, wildcard, range,
        # fuzzy etc) you must use a rewritten query!
        self.query = self.query.rewrite(self.reader)

        print "Searching for:", self.query.toString(self.FIELD_NAME)
        self.scoreDocs = self.searcher.search(self.query, 100).scoreDocs
        self.numHighlights = 0

    def doStandardHighlights(self):

        formatter = TestFormatter(self)

        highlighter = Highlighter(formatter, QueryScorer(self.query))
        highlighter.setTextFragmenter(SimpleFragmenter(20))
        for scoreDoc in self.scoreDocs:
            text = self.searcher.doc(scoreDoc.doc).get(self.FIELD_NAME)
            maxNumFragmentsRequired = 2
            fragmentSeparator = "..."
            tokenStream = self.analyzer.tokenStream(self.FIELD_NAME,
                                                    StringReader(text))

            result = highlighter.getBestFragments(tokenStream,
                                                  text,
                                                  maxNumFragmentsRequired,
                                                  fragmentSeparator)
            print "\t", result

    def countHighlightTerm(self):

        self.numHighlights += 1 # update stats used in assertions

    def addDoc(self, writer, text):

        d = Document()
        f = Field(self.FIELD_NAME, text, TextField.TYPE_STORED)

        d.add(f)
        writer.addDocument(d)


if __name__ == "__main__":
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    if '-loop' in sys.argv:
        sys.argv.remove('-loop')
        while True:
            try:
                unittest.main()
            except:
                pass
    else:
         unittest.main()
