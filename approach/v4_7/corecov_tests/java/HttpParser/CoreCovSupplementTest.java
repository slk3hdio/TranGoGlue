import org.apache.commons.httpclient.HttpParser;
import org.apache.commons.httpclient.Header;
import java.io.ByteArrayInputStream;
import org.junit.Test;
import static org.junit.Assert.*;

/** HttpParser核心行为补充测试；仅验证Java语义，不吞掉异常、不修改生产代码。 */
public class CoreCovSupplementTest {
    /** 验证LF以及无终止符末行；无参数，异常使测试失败。 */
    @Test public void lineEndings() throws Exception { ByteArrayInputStream in = new ByteArrayInputStream("first\nlast".getBytes("US-ASCII")); assertEquals("first", HttpParser.readLine(in)); assertEquals("last", HttpParser.readLine(in)); assertNull(HttpParser.readLine(in)); }
    /** 验证同名请求头不合并且保留顺序；无参数，异常使测试失败。 */
    @Test public void duplicateHeaders() throws Exception { Header[] h = HttpParser.parseHeaders(new ByteArrayInputStream("X-A: one\r\nX-A: two\r\n\r\n".getBytes("US-ASCII"))); assertEquals(2, h.length); assertEquals("one", h[0].getValue()); assertEquals("two", h[1].getValue()); }
}
