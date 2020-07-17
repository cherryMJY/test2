/* ====================================================================
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 * ====================================================================
 */

package org.apache.pylucene.store;

import java.io.IOException;
import java.util.Collection;
import java.util.Set;

import org.apache.lucene.store.Directory;
import org.apache.lucene.store.IOContext;
import org.apache.lucene.store.IndexInput;
import org.apache.lucene.store.IndexOutput;
import org.apache.lucene.store.LockFactory;
import org.apache.lucene.store.Lock;


public class PythonDirectory extends Directory {

    private long pythonObject;

    public PythonDirectory()
    {
    }

    public void pythonExtension(long pythonObject)
    {
        this.pythonObject = pythonObject;
    }
    public long pythonExtension()
    {
        return this.pythonObject;
    }

    public void finalize()
        throws Throwable
    {
        pythonDecRef();
    }

    @Override
    public void sync(Collection<String> names)
        throws IOException
    {
        for (String name : names)
            sync(name);
    }

    public native void sync(String name)
        throws IOException;

    public native void pythonDecRef();

    @Override
    public native void close()
        throws IOException;
    @Override
    public native IndexOutput createOutput(String name, IOContext context)
        throws IOException;
    @Override
    public native IndexOutput createTempOutput(String prefix, String suffix,
                                               IOContext context)
        throws IOException;
    @Override
    public native void deleteFile(String name)
        throws IOException;
    @Override
    public native long fileLength(String name)
        throws IOException;
    @Override
    public native String[] listAll()
        throws IOException;
    @Override
    public native IndexInput openInput(String name, IOContext context)
        throws IOException;
    @Override
    public native void rename(String source, String dest)
        throws IOException;
    @Override
    public native void syncMetaData()
        throws IOException;
    @Override
    public native Lock obtainLock(String name);

    @Override
    public native Set<String> getPendingDeletions()
        throws IOException;
}
