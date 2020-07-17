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

from java.io import StringReader
from org.apache.lucene.analysis.core import StopAnalyzer
from org.apache.lucene.analysis.en import EnglishAnalyzer
from org.apache.lucene.analysis import StopFilter
from org.apache.lucene.analysis.tokenattributes import \
    CharTermAttribute, PositionIncrementAttribute


class StopAnalyzerTestCase(unittest.TestCase):
    """
    Unit tests ported from Java Lucene
    """

    def setUp(self):

        self.stop = StopAnalyzer(EnglishAnalyzer.ENGLISH_STOP_WORDS_SET)
        self.invalidTokens = EnglishAnalyzer.ENGLISH_STOP_WORDS_SET

    def testDefaults(self):

        self.assertTrue(self.stop is not None)
        reader = StringReader("This is a test of the english stop analyzer")
        stream = self.stop.tokenStream("test", reader)
        self.assertTrue(stream is not None)
        stream.reset()

        termAtt = stream.getAttribute(CharTermAttribute.class_)

        while stream.incrementToken():
            self.assertTrue(termAtt.toString() not in self.invalidTokens)

    def testStopList(self):

        stopWords = ["good", "test", "analyzer"]
        stopWordsSet = StopFilter.makeStopSet(stopWords)

        newStop = StopAnalyzer(stopWordsSet)
        reader = StringReader("This is a good test of the english stop analyzer")
        stream = newStop.tokenStream("test", reader)
        self.assertTrue(stream is not None)
        stream.reset()

        termAtt = stream.getAttribute(CharTermAttribute.class_)

        while stream.incrementToken():
            text = termAtt.toString()
            self.assertTrue(text not in stopWordsSet)

    def testStopListPositions(self):

        stopWords = ["good", "test", "analyzer"]
        stopWordsSet = StopFilter.makeStopSet(stopWords)

        newStop = StopAnalyzer(stopWordsSet)
        reader = StringReader("This is a good test of the english stop analyzer with positions")
        expectedIncr = [ 1,   1, 1,          3, 1,  1,      1,            2,   1]
        stream = newStop.tokenStream("test", reader)
        self.assertTrue(stream is not None)
        stream.reset()

        i = 0
        termAtt = stream.getAttribute(CharTermAttribute.class_)
        posIncrAtt = stream.addAttribute(PositionIncrementAttribute.class_)

        while stream.incrementToken():
            text = termAtt.toString()
            self.assertTrue(text not in stopWordsSet)
            self.assertEqual(expectedIncr[i],
                             posIncrAtt.getPositionIncrement())
            i += 1


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
