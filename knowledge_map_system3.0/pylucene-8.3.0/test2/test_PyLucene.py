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
import os, shutil

from java.io import StringReader
from java.nio.file import Path, Paths
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import \
    Document, Field, StoredField, StringField, TextField
from org.apache.lucene.index import \
    IndexOptions, IndexWriter, IndexWriterConfig, DirectoryReader, \
    FieldInfos, MultiFields, MultiTerms, Term
from org.apache.lucene.queryparser.classic import \
    MultiFieldQueryParser, QueryParser
from org.apache.lucene.search import BooleanClause, IndexSearcher, TermQuery
from org.apache.lucene.store import MMapDirectory, SimpleFSDirectory
from org.apache.lucene.util import BytesRefIterator


class Test_PyLuceneBase(object):

    def getAnalyzer(self):
        return StandardAnalyzer()

    def openStore(self):
        raise NotImplemented

    def closeStore(self, store, *args):
        pass

    def getWriter(self, store, analyzer=None, create=False):

        if analyzer is None:
            analyzer = WhitespaceAnalyzer()
        analyzer = LimitTokenCountAnalyzer(analyzer, 10000)
        config = IndexWriterConfig(analyzer)
        if create:
            config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
        writer = IndexWriter(store, config)

        return writer

    def getReader(self, store, analyzer):
        pass

    def getSearcher(self, store):
        return IndexSearcher(DirectoryReader.open(store))

    def test_indexDocument(self):

        store = self.openStore()
        writer = None
        try:
            analyzer = self.getAnalyzer()
            writer = self.getWriter(store, analyzer, True)

            doc = Document()
            doc.add(Field("title", "value of testing",
                          TextField.TYPE_STORED))
            doc.add(Field("docid", str(1),
                          StringField.TYPE_NOT_STORED))
            doc.add(Field("owner", "unittester",
                          StringField.TYPE_STORED))
            doc.add(Field("search_name", "wisdom",
                          StoredField.TYPE))
            doc.add(Field("meta_words", "rabbits are beautiful",
                          TextField.TYPE_NOT_STORED))

            writer.addDocument(doc)
        finally:
            self.closeStore(store, writer)

    def test_indexDocumentWithText(self):

        store = self.openStore()
        writer = None
        try:
            analyzer = self.getAnalyzer()
            writer = self.getWriter(store, analyzer, True)

            doc = Document()
            doc.add(Field("title", "value of testing",
                          TextField.TYPE_STORED))
            doc.add(Field("docid", str(1),
                          StringField.TYPE_NOT_STORED))
            doc.add(Field("owner", "unittester",
                          StringField.TYPE_STORED))
            doc.add(Field("search_name", "wisdom",
                          StoredField.TYPE))
            doc.add(Field("meta_words", "rabbits are beautiful",
                          TextField.TYPE_NOT_STORED))

            body_text = "hello world" * 20
            body_reader = StringReader(body_text)
            doc.add(Field("content", body_reader, TextField.TYPE_NOT_STORED))

            writer.addDocument(doc)
        finally:
            self.closeStore(store, writer)

    def test_indexDocumentWithUnicodeText(self):

        store = self.openStore()
        writer = None
        try:
            analyzer = self.getAnalyzer()
            writer = self.getWriter(store, analyzer, True)

            doc = Document()
            doc.add(Field("title", "value of testing",
                          TextField.TYPE_STORED))
            doc.add(Field("docid", str(1),
                          StringField.TYPE_NOT_STORED))
            doc.add(Field("owner", "unittester",
                          StringField.TYPE_STORED))
            doc.add(Field("search_name", "wisdom",
                          StoredField.TYPE))
            doc.add(Field("meta_words", "rabbits are beautiful",
                          TextField.TYPE_NOT_STORED))

            # using a unicode body cause problems, which seems very odd
            # since the python type is the same regardless affter doing
            # the encode
            body_text = u"hello world"*20
            body_reader = StringReader(body_text)
            doc.add(Field("content", body_reader, TextField.TYPE_NOT_STORED))

            writer.addDocument(doc)
        finally:
            self.closeStore(store, writer)

    def test_searchDocuments(self):

        self.test_indexDocument()

        store = self.openStore()
        searcher = None
        try:
            searcher = self.getSearcher(store)
            query = QueryParser("title", self.getAnalyzer()).parse("value")
            topDocs = searcher.search(query, 50)
            self.assertEqual(topDocs.totalHits.value, 1)
        finally:
            self.closeStore(store)

    def test_searchDocumentsWithMultiField(self):
        """
        Tests searching with MultiFieldQueryParser
        """

        self.test_indexDocument()
        store = self.openStore()
        searcher = None
        try:
            searcher = self.getSearcher(store)
            SHOULD = BooleanClause.Occur.SHOULD
            query = MultiFieldQueryParser.parse("value", ["title", "docid"],
                                                [SHOULD, SHOULD],
                                                self.getAnalyzer())
            topDocs = searcher.search(query, 50)
            self.assertEquals(1, topDocs.totalHits.value)
        finally:
            self.closeStore(store)
        
    def test_removeDocument(self):

        self.test_indexDocument()

        store = self.openStore()
        searcher = None
        writer = None

        try:
            searcher = self.getSearcher(store)
            query = TermQuery(Term("docid", str(1)))
            topDocs = searcher.search(query, 50)
            self.assertEqual(topDocs.totalHits.value, 1)
            # be careful with ids they are ephemeral
            docid = topDocs.scoreDocs[0].doc
        
            writer = self.getWriter(store)
            writer.deleteDocuments(Term("docid", str(1)))
        finally:
            self.closeStore(store, writer)

        store = self.openStore()
        searcher = None
        try:
            searcher = self.getSearcher(store)
            query = TermQuery(Term("docid", str(1)))
            topDocs = searcher.search(query, 50)
            self.assertEqual(topDocs.totalHits.value, 0)
        finally:
            self.closeStore(store)

    def test_removeDocuments(self):

        self.test_indexDocument()

        store = self.openStore()
        writer = None
        try:
            writer = self.getWriter(store)
            writer.deleteDocuments(Term('docid', str(1)))
        finally:
            self.closeStore(store, writer)

        store = self.openStore()
        searcher = None
        try:
            searcher = self.getSearcher(store)
            query = QueryParser("title", self.getAnalyzer()).parse("value")
            topDocs = searcher.search(query, 50)
            self.assertEqual(topDocs.totalHits.value, 0)
        finally:
            self.closeStore(store)

    def test_FieldEnumeration(self):
        self.test_indexDocument()

        store = self.openStore()
        writer = None
        try:
            analyzer = self.getAnalyzer()

            writer = self.getWriter(store, analyzer, False)
            doc = Document()
            doc.add(Field("title", "value of testing",
                          TextField.TYPE_STORED))
            doc.add(Field("docid", str(2),
                          StringField.TYPE_NOT_STORED))
            doc.add(Field("owner", "unittester",
                          StringField.TYPE_STORED))
            doc.add(Field("search_name", "wisdom",
                          StoredField.TYPE))
            doc.add(Field("meta_words", "rabbits are beautiful",
                          TextField.TYPE_NOT_STORED))

            writer.addDocument(doc)

            doc = Document()
            doc.add(Field("owner", "unittester",
                          StringField.TYPE_NOT_STORED))
            doc.add(Field("search_name", "wisdom",
                          StoredField.TYPE))
            doc.add(Field("meta_words", "rabbits are beautiful",
                          TextField.TYPE_NOT_STORED))
            writer.addDocument(doc)
        finally:
            self.closeStore(store, writer)

        store = self.openStore()
        reader = None
        try:
            reader = DirectoryReader.open(store)
            term_enum = MultiTerms.getTerms(reader, "docid").iterator()
            docids = [term.utf8ToString()
                      for term in BytesRefIterator.cast_(term_enum)]
            self.assertEqual(len(docids), 2)
        finally:
            self.closeStore(store, reader)

    def test_getFieldInfos(self):

        self.test_indexDocument()

        store = self.openStore()
        reader = None
        try:
            reader = DirectoryReader.open(store)
            fieldInfos = FieldInfos.getMergedFieldInfos(reader)
            for fieldInfo in fieldInfos.iterator():
                self.assert_(fieldInfo.name in ['owner', 'search_name',
                                                'meta_words', 'docid', 'title'])

                if fieldInfo.getIndexOptions() != IndexOptions.NONE:
                    self.assert_(fieldInfo.name in ['owner', 'meta_words',
                                                    'docid', 'title'])

                if (fieldInfo.getIndexOptions() != IndexOptions.NONE and
                    not fieldInfo.hasVectors()):
                    self.assert_(fieldInfo.name in ['owner', 'meta_words',
                                                    'docid', 'title'])
        finally:
            store = self.closeStore(store, reader)


class Test_PyLuceneWithFSStore(unittest.TestCase, Test_PyLuceneBase):

    STORE_DIR = "testrepo"

    def setUp(self):

        if not os.path.exists(self.STORE_DIR):
            os.mkdir(self.STORE_DIR)

    def tearDown(self):

        if os.path.exists(self.STORE_DIR):
            try:
                shutil.rmtree(self.STORE_DIR)
            except Exception, e:
                # maybe leaking file handles in closing stores
                # does not affect other tests
                if type(e).__name__ == 'WindowsError':
                    pass
                else:
                    raise

    def openStore(self):

        return SimpleFSDirectory(Paths.get(self.STORE_DIR))

    def closeStore(self, store, *args):

        for arg in args:
            if arg is not None:
                arg.close()

        store.close()


class Test_PyLuceneWithMMapStore(Test_PyLuceneWithFSStore):

    def openStore(self):

        return MMapDirectory(Paths.get(self.STORE_DIR))



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
