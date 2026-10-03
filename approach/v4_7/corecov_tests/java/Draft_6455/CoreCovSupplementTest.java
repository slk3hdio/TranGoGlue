import org.java_websocket.drafts.Draft_6455;
import org.java_websocket.enums.CloseHandshakeType;
import org.junit.Test;
import static org.junit.Assert.*;

/** Draft_6455核心行为补充测试；仅验证Java语义，不吞掉异常、不修改生产代码。 */
public class CoreCovSupplementTest {
    /** 验证关闭握手必须是双向而非任意枚举；无参数，异常使测试失败。 */
    @Test public void twoWayClose() throws Exception { assertEquals(CloseHandshakeType.TWOWAY, new Draft_6455().getCloseHandshakeType()); }
    /** 验证重置保留帧大小并保持复制握手策略；无参数，异常使测试失败。 */
    @Test public void resetConfiguration() throws Exception { Draft_6455 d = new Draft_6455(); int limit = d.getMaxFrameSize(); d.reset(); assertEquals(limit, d.getMaxFrameSize()); assertEquals(CloseHandshakeType.TWOWAY, d.copyInstance().getCloseHandshakeType()); }
}
