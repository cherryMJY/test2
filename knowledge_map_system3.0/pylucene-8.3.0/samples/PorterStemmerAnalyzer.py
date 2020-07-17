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

# This sample illustrates how to write an Analyzer 'extension' in Python.
#
#   What is happening behind the scenes ?
#
# The PorterStemmerAnalyzer python class does not in fact extend Analyzer,
# it merely provides an implementation for Analyzer's abstract tokenStream()
# method. When an instance of PorterStemmerAnalyzer is passed to PyLucene,
# with a call to IndexWriter(store, PorterStemmerAnalyzer(), True) for
# example, the PyLucene glue code wraps it into an instance of PythonAnalyzer,
# a proper java extension of Analyzer which implements a native
# createComponents() method whose job is to call the tokenStream() method on
# the python instance it wraps. The PythonAnalyzer instance is the Analyzer
# extension bridge to PorterStemmerAnalyzer.

import sys, os, lucene
from datetime import datetime
from IndexFiles import IndexFiles

from org.apache.lucene.analysis import LowerCaseFilter, StopFilter
from org.apache.lucene.analysis.en import PorterStemFilter, EnglishAnalyzer
from org.apache.lucene.analysis.standard import StandardTokenizer
from org.apache.pylucene.analysis import PythonAnalyzer


class PorterStemmerAnalyzer(PythonAnalyzer):

    def createComponents(self, fieldName):

        source = StandardTokenizer()
        filter = LowerCaseFilter(source)
        filter = PorterStemFilter(filter)
        filter = StopFilter(filter, EnglishAnalyzer.ENGLISH_STOP_WORDS_SET)

        return self.TokenStreamComponents(source, filter)

    def initReader(self, fieldName, reader):
        return reader


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print IndexFiles.__doc__
        sys.exit(1)
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    print 'lucene', lucene.VERSION
    start = datetime.now()
    try:
        IndexFiles(sys.argv[1], "index", PorterStemmerAnalyzer())
        end = datetime.now()
        print end - start
    except Exception, e:
        print "Failed: ", e
