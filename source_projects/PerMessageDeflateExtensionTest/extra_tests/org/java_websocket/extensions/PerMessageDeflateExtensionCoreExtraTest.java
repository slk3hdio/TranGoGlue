// 针对性补充测试(手工编写): PerMessageDeflateExtensionTest 的核心文件本身是上游
// JUnit 测试类, 其 public 方法即上游测试方法。本类通过包装直接调用合并基线未覆盖的
// 那些方法, 使其获得执行级覆盖; 断言失败会正常传播, 保留回归信号。
package org.java_websocket.extensions;

import org.junit.Test;

/**
 * PerMessageDeflateExtensionTest 上游测试方法的包装补充测试。
 * 上游为无状态测试类, 每个用例内自建被测 extension 实例。
 */
public class PerMessageDeflateExtensionCoreExtraTest {

  /** 被调用的上游测试类实例。 */
  private final PerMessageDeflateExtensionTest delegate = new PerMessageDeflateExtensionTest();

  /** 覆盖上游 testDecodeFrameIfRSVIsNotSet。 */
  @Test
  public void testDecodeFrameIfRSVIsNotSet() throws Exception {
    delegate.testDecodeFrameIfRSVIsNotSet();
  }

  /** 覆盖上游 testDecodeFrameNoCompression。 */
  @Test
  public void testDecodeFrameNoCompression() throws Exception {
    delegate.testDecodeFrameNoCompression();
  }

  /** 覆盖上游 testDecodeFrameBestSpeedCompression。 */
  @Test
  public void testDecodeFrameBestSpeedCompression() throws Exception {
    delegate.testDecodeFrameBestSpeedCompression();
  }

  /** 覆盖上游 testDecodeFrameBestCompression。 */
  @Test
  public void testDecodeFrameBestCompression() throws Exception {
    delegate.testDecodeFrameBestCompression();
  }

  /** 覆盖上游 testEncodeFrame。 */
  @Test
  public void testEncodeFrame() {
    delegate.testEncodeFrame();
  }

  /** 覆盖上游 testEncodeFrameBelowThreshold。 */
  @Test
  public void testEncodeFrameBelowThreshold() {
    delegate.testEncodeFrameBelowThreshold();
  }

  /** 覆盖上游 testAcceptProvidedExtensionAsClient。 */
  @Test
  public void testAcceptProvidedExtensionAsClient() {
    delegate.testAcceptProvidedExtensionAsClient();
  }

  /** 覆盖上游 testGetProvidedExtensionAsClient。 */
  @Test
  public void testGetProvidedExtensionAsClient() {
    delegate.testGetProvidedExtensionAsClient();
  }

  /** 覆盖上游 testGetProvidedExtensionAsServer。 */
  @Test
  public void testGetProvidedExtensionAsServer() {
    delegate.testGetProvidedExtensionAsServer();
  }

  /** 覆盖上游 testIsServerNoContextTakeover。 */
  @Test
  public void testIsServerNoContextTakeover() {
    delegate.testIsServerNoContextTakeover();
  }

  /** 覆盖上游 testSetServerNoContextTakeover。 */
  @Test
  public void testSetServerNoContextTakeover() {
    delegate.testSetServerNoContextTakeover();
  }

  /** 覆盖上游 testIsClientNoContextTakeover。 */
  @Test
  public void testIsClientNoContextTakeover() {
    delegate.testIsClientNoContextTakeover();
  }

  /** 覆盖上游 testSetClientNoContextTakeover。 */
  @Test
  public void testSetClientNoContextTakeover() {
    delegate.testSetClientNoContextTakeover();
  }
}
