// 针对性补充测试(手工编写): Draft_6455Test 的核心文件本身是上游 JUnit 测试类,
// 其 public 方法即上游测试方法。本类通过包装直接调用合并基线未覆盖的那些方法,
// 使其获得执行级覆盖; 断言失败会正常传播, 保留回归信号。
package org.java_websocket.drafts;

import org.junit.Test;

/**
 * Draft_6455Test 上游测试方法的包装补充测试。
 * 委托实例在字段初始化时完成握手数据的构造(上游逻辑在构造器内)。
 */
public class Draft_6455CoreExtraTest {

  /** 被调用的上游测试类实例。 */
  private final Draft_6455Test delegate = new Draft_6455Test();

  /** 覆盖上游 testGetKnownProtocols。 */
  @Test
  public void testGetKnownProtocols() throws Exception {
    delegate.testGetKnownProtocols();
  }

  /** 覆盖上游 testGetCloseHandshakeType。 */
  @Test
  public void testGetCloseHandshakeType() throws Exception {
    delegate.testGetCloseHandshakeType();
  }

  /** 覆盖上游 testToString。 */
  @Test
  public void testToString() throws Exception {
    delegate.testToString();
  }

  /** 覆盖上游 testEquals。 */
  @Test
  public void testEquals() throws Exception {
    delegate.testEquals();
  }

  /** 覆盖上游 testHashCode。 */
  @Test
  public void testHashCode() throws Exception {
    delegate.testHashCode();
  }

  /** 覆盖上游 acceptHandshakeAsServer。 */
  @Test
  public void acceptHandshakeAsServer() throws Exception {
    delegate.acceptHandshakeAsServer();
  }

  /** 覆盖上游 acceptHandshakeAsClient。 */
  @Test
  public void acceptHandshakeAsClient() throws Exception {
    delegate.acceptHandshakeAsClient();
  }

  /** 覆盖上游 postProcessHandshakeRequestAsClient。 */
  @Test
  public void postProcessHandshakeRequestAsClient() throws Exception {
    delegate.postProcessHandshakeRequestAsClient();
  }

  /** 覆盖上游 postProcessHandshakeResponseAsServer。 */
  @Test
  public void postProcessHandshakeResponseAsServer() throws Exception {
    delegate.postProcessHandshakeResponseAsServer();
  }

  /** 覆盖上游 createFramesBinary。 */
  @Test
  public void createFramesBinary() throws Exception {
    delegate.createFramesBinary();
  }

  /** 覆盖上游 createFramesText。 */
  @Test
  public void createFramesText() throws Exception {
    delegate.createFramesText();
  }
}
