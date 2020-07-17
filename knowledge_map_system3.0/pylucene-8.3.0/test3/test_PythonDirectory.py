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
import test_PyLucene
from binascii import crc32
from threading import RLock
from lucene import JavaError, JArray

from java.lang import String
from java.io import IOException
from java.util import Collections
from org.apache.pylucene.store import \
    PythonLock, PythonLockFactory, \
    PythonIndexInput, PythonIndexOutput, PythonDirectory

"""
The Directory Implementation here is for testing purposes only, not meant
as an example of writing one, the implementation here suffers from a lack
of safety when dealing with concurrent modifications as it does away with
the file locking in the default lucene fsdirectory implementation.
"""

DEBUG = False

class DebugWrapper(object):

    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, name):
        print(self.obj.__class__.__name__, self.obj.name, name)
        sys.stdout.flush()
        return getattr(self.obj, name)

class DebugFactory(object):

    def __init__(self, klass):
        self.klass = klass

    def __call__(self, *args, **kw):
        instance = self.klass(*args, **kw)
        return DebugWrapper(instance)


class PythonFileStreamInput(PythonIndexInput):

    def __init__(self, name, fh, size, clone=False):
        if not clone:
            super(PythonFileStreamInput, self).__init__(name, size)
        self.name = name
        self.fh = fh
        self._length = size
        self.isOpen = True
        self.isClone = clone

    def length(self):
        return int(self._length)

    def clone(self):
        clone = PythonFileStreamInput(self.name, self.fh, self._length, True)
        return super(PythonFileStreamInput, self).clone(clone)

    def close(self):
        if self.isOpen:
            self.isOpen = False
            if not self.isClone:
                self.fh.close()

    def readInternal(self, length, pos):
        self.fh.seek(pos)
        return JArray('byte')(self.fh.read(length))

    def seekInternal(self, pos):
        self.fh.seek(pos)


class PythonFileStreamOutput(PythonIndexOutput):

    def __init__(self, name, fh):
        super(PythonFileStreamOutput, self).__init__("python: %s" %(name), name)
        self.fh = fh
        self.isOpen = True
        self._length = 0
        self.crc = None

    def close(self):
        if self.isOpen:
            self.isOpen = False
            self.fh.flush()
            self.fh.close()

    def getFilePointer(self):
        return int(self._length)

    def getChecksum(self):
        return int(self.crc & 0xffffffff)

    def writeByte(self, b):
        if b < 0:
            data = bytes([b + 256])
        else:
            data = bytes([b])
        self.fh.write(data)
        self._length += 1

        if self.crc is None:
            self.crc = crc32(data)
        else:
            self.crc = crc32(data, self.crc)

    def writeBytes(self, bytes):
        data = bytes.bytes_
        self.fh.write(data)
        self.fh.flush()
        self._length += len(data)

        if self.crc is None:
            self.crc = crc32(data)
        else:
            self.crc = crc32(data, self.crc)


class PythonFileDirectory(PythonDirectory):

    def __init__(self, path):
        super(PythonFileDirectory, self).__init__()

        class _lock_factory(PythonLockFactory):

            def __init__(_self):
                super(_lock_factory, _self).__init__()
                _self._locks = {}

            def obtainLock(_self, directory, name):

                # only safe for a single process
                class _lock(PythonLock):

                    def __init__(__self, path):
                        super(_lock, __self).__init__()

                        __self.lock_file = path
                        __self.lock = RLock()

                    def ensureValid(__self):
                        __self.lock.acquire()

                    def close(__self):
                        if hasattr(__self.lock, 'close'):
                            __self.lock.close()

                lock = _self._locks.get(name)
                if lock is None:
                    lock = _lock(os.path.join(directory.name, name))
                    _self._locks[name] = lock

                return lock

        self._lockFactory = _lock_factory()
        self.name = path
        assert os.path.isdir(path)
        self.path = path
        self._streams = []
        self.temp_count = 0

    def close(self):
        for stream in self._streams:
            stream.close()
        del self._streams[:]

    def createOutput(self, name, context):
        file_path = os.path.join(self.path, name)
        fh = open(file_path, "wb")
        stream = PythonFileStreamOutput(name, fh)
        self._streams.append(stream)
        return stream

    def createTempOutput(self, prefix, suffix, context):
        self.temp_count += 1
        name = "%s_%d_%s.tmp" %(prefix, self.temp_count, suffix)
        return self.createOutput(name, context)

    def deleteFile(self, name):
        os.unlink(os.path.join(self.path, name))

    def fileLength(self, name):
        file_path = os.path.join(self.path, name)
        return int(os.path.getsize(file_path))

    def listAll(self):
        return os.listdir(self.path)

    def sync(self, name):
        pass
    def syncMetaData(self):
        pass

    def rename(self, source, dest):
        shutil.move(os.path.join(self.path, source),
                    os.path.join(self.path, dest))

    def openInput(self, name, context):
        file_path = os.path.join(self.path, name)
        try:
            fh = open(file_path, "rb")
        except IOError:
            raise JavaError(IOException(name))
        stream = PythonFileStreamInput(name, fh, os.path.getsize(file_path))
        self._streams.append(stream)
        return stream

    def obtainLock(self, name):
        return self._lockFactory.obtainLock(self, name)

    def getPendingDeletions(self):
        return Collections.EMPTY_SET


if DEBUG:
    _globals = globals()
    _globals['PythonFileDirectory'] = DebugFactory(PythonFileDirectory)
    _globals['PythonFileStreamInput'] = DebugFactory(PythonFileStreamInput)
    _globals['PythonFileStreamOutput'] = DebugFactory(PythonFileStreamOutput)
    del _globals

class PythonDirectoryTests(unittest.TestCase, test_PyLucene.Test_PyLuceneBase):

    STORE_DIR = "testpyrepo"

    def setUp(self):
        if not os.path.exists(self.STORE_DIR):
            os.mkdir(self.STORE_DIR)

    def tearDown(self):
        if os.path.exists(self.STORE_DIR):
            shutil.rmtree(self.STORE_DIR)

    def openStore(self):
        return PythonFileDirectory(self.STORE_DIR)

    def closeStore(self, store, *args):
        for arg in args:
            if arg is not None:
                arg.close()
        store.close()

    def test_IncrementalLoop(self):
        print("Testing Indexing Incremental Looping")
        for i in range(100):
            print("indexing ", i)
            sys.stdout.flush()
            self.test_indexDocument()


if __name__ == "__main__":
    env = lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    if '-loop' in sys.argv:
        sys.argv.remove('-loop')
        while True:
            try:
                unittest.main()
            except:
                pass
            print('inputs', env._dumpRefs(True).get('class org.osafoundation.lucene.store.PythonIndexOutput', 0))
            print('outputs', env._dumpRefs(True).get('class org.osafoundation.lucene.store.PythonIndexInput', 0))
            print('locks', env._dumpRefs(True).get('class org.osafoundation.lucene.store.PythonLock', 0))
            print('dirs', env._dumpRefs(True).get('class org.osafoundation.lucene.store.PythonLock', 0))
    else:
        unittest.main()
