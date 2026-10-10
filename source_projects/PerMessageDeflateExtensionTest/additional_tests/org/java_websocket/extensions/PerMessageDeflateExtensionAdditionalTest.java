package org.java_websocket.extensions;

import org.junit.Test;

/**
 * PerMessageDeflateExtension 上游测试类的附加适配测试，覆盖压缩参数和协商分支。
 */
public class PerMessageDeflateExtensionAdditionalTest {
  private final PerMessageDeflateExtensionTest upstream = new PerMessageDeflateExtensionTest();

  /**
   * 验证不同压缩级别和未设置 RSV 标志时的解码行为。
   *
   * @throws Exception 上游测试执行失败时抛出
   */
  @Test
  public void verifiesDecodeVariants() throws Exception {
    upstream.testDecodeFrameIfRSVIsNotSet();
    upstream.testDecodeFrameNoCompression();
    upstream.testDecodeFrameBestSpeedCompression();
    upstream.testDecodeFrameBestCompression();
  }

  /**
   * 验证帧编码和压缩阈值行为。
   */
  @Test
  public void verifiesEncodeVariants() {
    upstream.testEncodeFrame();
    upstream.testEncodeFrameBelowThreshold();
  }

  /**
   * 验证客户端协商以及客户端和服务端扩展声明。
   */
  @Test
  public void verifiesNegotiationPaths() {
    upstream.testAcceptProvidedExtensionAsClient();
    upstream.testGetProvidedExtensionAsClient();
    upstream.testGetProvidedExtensionAsServer();
  }

  /**
   * 验证客户端和服务端上下文接管配置的读写行为。
   */
  @Test
  public void verifiesContextTakeoverConfiguration() {
    upstream.testIsServerNoContextTakeover();
    upstream.testSetServerNoContextTakeover();
    upstream.testIsClientNoContextTakeover();
    upstream.testSetClientNoContextTakeover();
  }
}
