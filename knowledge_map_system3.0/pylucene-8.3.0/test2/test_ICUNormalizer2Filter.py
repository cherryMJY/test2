# -*- coding: utf-8 -*-
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
#
#  Port of java/org/apache/lucene/analysis/icu/ICUNormalizer2Filter.java
#  using IBM's C++ ICU wrapped by PyICU (http://pyicu.osafoundation.org)

try:
    from icu import Normalizer2, UNormalizationMode2
except ImportError, e:
    pass

import sys, lucene, unittest
from BaseTokenStreamTestCase import BaseTokenStreamTestCase

from org.apache.lucene.analysis import Analyzer
from org.apache.lucene.analysis.core import WhitespaceTokenizer
from org.apache.pylucene.analysis import PythonAnalyzer


class TestICUNormalizer2Filter(BaseTokenStreamTestCase):

    def testDefaults(self):

        from lucene.ICUNormalizer2Filter import ICUNormalizer2Filter

        class _analyzer(PythonAnalyzer):
            def createComponents(_self, fieldName):
                source = WhitespaceTokenizer()
                return Analyzer.TokenStreamComponents(source, ICUNormalizer2Filter(source))
            def initReader(_self, fieldName, reader):
                return reader

        a = _analyzer()

        # case folding
        self._assertAnalyzesTo(a, "This is a test",
                               [ "this", "is", "a", "test" ])

        # case folding
        self._assertAnalyzesTo(a, "Ruß", [ "russ" ])

        # case folding
        self._assertAnalyzesTo(a, u"ΜΆΪΟΣ", [ u"μάϊοσ" ])
        self._assertAnalyzesTo(a, u"Μάϊος", [ u"μάϊοσ" ])

        # supplementary case folding
        self._assertAnalyzesTo(a, u"𐐖", [ u"𐐾" ])

        # normalization
        self._assertAnalyzesTo(a, u"ﴳﴺﰧ", [ u"طمطمطم" ])

        # removal of default ignorables
        self._assertAnalyzesTo(a, u"क्‍ष", [ u"क्ष" ])

    def testAlternate(self):

        from lucene.ICUNormalizer2Filter import ICUNormalizer2Filter

        class analyzer(PythonAnalyzer):
            # specify nfc with decompose to get nfd
            def createComponents(_self, fieldName):
                source = WhitespaceTokenizer()
                return Analyzer.TokenStreamComponents(
                    source, ICUNormalizer2Filter(
                        source,
                        Normalizer2.getInstance(None, "nfc", UNormalizationMode2.DECOMPOSE)))
            def initReader(_self, fieldName, reader):
                return reader

        a = analyzer()
        # decompose EAcute into E + combining Acute
        self._assertAnalyzesTo(a, u"\u00E9", [ u"\u0065\u0301" ])


if __name__ == "__main__":
    try:
        import icu
    except ImportError:
        pass
    else:
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
