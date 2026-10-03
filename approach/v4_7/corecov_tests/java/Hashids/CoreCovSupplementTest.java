import cn.hutool.core.codec.Hashids;
import org.junit.Test;
import static org.junit.Assert.*;

/** Hashids核心行为补充测试；仅验证Java语义，不吞掉异常、不修改生产代码。 */
public class CoreCovSupplementTest {
    /** 验证十六进制转换及前缀等价；无参数，异常使测试失败。 */
    @Test public void hexRoundTrip() throws Exception { Hashids h = Hashids.create("salt".toCharArray()); assertEquals("deadbeef", h.decodeToHex(h.encodeFromHex("0xdeadbeef"))); assertEquals(h.encodeFromHex("deadbeef"), h.encodeFromHex("0Xdeadbeef")); }
    /** 验证零值和大整数序列往返；无参数，异常使测试失败。 */
    @Test public void zeroAndLarge() throws Exception { Hashids h = Hashids.create("salt".toCharArray()); long[] values = {0, 2147483648L, 9007199254740991L}; assertArrayEquals(values, h.decode(h.encode(values))); }
}
