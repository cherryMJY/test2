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

from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, StoredField, TextField
from org.apache.lucene.queryparser.classic import QueryParser


class Test_Bug1564(PyLuceneTestCase):

    def setUp(self):
        super(Test_Bug1564, self).setUp()

        self.analyzer = StandardAnalyzer()
        writer = self.getWriter(analyzer=self.analyzer)

        doc = Document()
        doc.add(Field('all', u'windowpane beplaster rapacious \
        catatonia gauntlet wynn depressible swede pick dressmake supreme \
        jeremy plumb theoretic bureaucracy causation chartres equipoise \
        dispersible careen heard', TextField.TYPE_NOT_STORED))
        doc.add(Field('id', '1', StoredField.TYPE))

        writer.addDocument(doc)
        writer.commit()
        writer.close()

    def test_bug1564(self):

        searcher = self.getSearcher()
        query = QueryParser('all', self.analyzer).parse('supreme')
        topDocs = searcher.search(query, 50)
        self.assertEqual(topDocs.totalHits.value, 1)


if __name__ == '__main__':
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    unittest.main()
