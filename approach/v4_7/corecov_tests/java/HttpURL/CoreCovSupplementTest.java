import org.apache.commons.httpclient.HttpURL;
import org.junit.Test;
import static org.junit.Assert.*;

/** HttpURL核心行为补充测试；仅验证Java语义，不吞掉异常、不修改生产代码。 */
public class CoreCovSupplementTest {
    /** 验证用户信息及密码更新；无参数，异常使测试失败。 */
    @Test public void credentials() throws Exception { HttpURL u = new HttpURL("http://example.com/"); u.setUserinfo("alice", "secret"); assertEquals("alice", u.getUser()); assertEquals("secret", u.getPassword()); u.setPassword("changed"); assertEquals("changed", u.getPassword()); }
    /** 验证查询参数转义；无参数，异常使测试失败。 */
    @Test public void namedQuery() throws Exception { HttpURL u = new HttpURL("http://example.com/"); u.setQuery("key", "two words"); assertEquals("key=two%20words", u.getEscapedQuery()); }
}
