import com.alibaba.excel.metadata.Head;
import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;

/** Head核心行为补充测试；仅验证Java语义，不吞掉异常、不修改生产代码。 */
public class CoreCovSupplementTest {
    /** 验证保留多层表头和构造标志；无参数，异常使测试失败。 */
    @Test public void retainsNames() throws Exception { Head h = new Head(4, null, "field", Arrays.asList("parent", "child"), true, true); assertEquals(Arrays.asList("parent", "child"), h.getHeadNameList()); assertEquals("field", h.getFieldName()); assertTrue(h.getForceIndex()); assertTrue(h.getForceName()); }
    /** 验证空字符串合法，不等同于Java null；无参数，异常使测试失败。 */
    @Test public void emptyNameAllowed() throws Exception { Head h = new Head(0, null, "", Arrays.asList(""), false, false); assertEquals("", h.getHeadNameList().get(0)); }
}
