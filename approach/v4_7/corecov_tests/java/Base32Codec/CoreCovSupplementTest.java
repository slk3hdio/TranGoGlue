import cn.hutool.core.codec.Base32Codec;
import org.junit.Test;
import static org.junit.Assert.*;

/** Base32Codec核心行为补充测试；仅验证Java语义，不吞掉异常、不修改生产代码。 */
public class CoreCovSupplementTest {
    /** 验证空输入编解码保持空值；无参数，异常使测试失败。 */
    @Test public void emptyInput() throws Exception { assertEquals("", Base32Codec.INSTANCE.encode(new byte[0])); assertArrayEquals(new byte[0], Base32Codec.INSTANCE.decode("")); }
    /** 验证小写字母表仍可解码；无参数，异常使测试失败。 */
    @Test public void lowercaseDecode() throws Exception { assertArrayEquals("foo".getBytes("US-ASCII"), Base32Codec.INSTANCE.decode("mzxw6===")); }
}
