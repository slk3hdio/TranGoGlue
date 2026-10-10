package org.java_websocket.drafts;

import static org.junit.Assert.assertEquals;

import java.lang.reflect.Constructor;
import org.junit.Test;

/**
 * Draft_6455 上游测试类的附加适配测试，覆盖原冒烟测试未执行的行为。
 */
public class Draft_6455AdditionalTest {
  private final Draft_6455Test upstream = new Draft_6455Test();

  /**
   * 验证协议集合、关闭握手类型以及字符串和对象契约。
   *
   * @throws Exception 上游测试执行失败时抛出
   */
  @Test
  public void verifiesMetadataAndObjectContracts() throws Exception {
    upstream.testGetKnownProtocols();
    upstream.testGetCloseHandshakeType();
    upstream.testToString();
    upstream.testEquals();
    upstream.testHashCode();
  }

  /**
   * 验证客户端与服务端的握手协商和握手后处理。
   *
   * @throws Exception 上游测试执行失败时抛出
   */
  @Test
  public void verifiesHandshakePaths() throws Exception {
    upstream.acceptHandshakeAsServer();
    upstream.acceptHandshakeAsClient();
    upstream.postProcessHandshakeRequestAsClient();
    upstream.postProcessHandshakeResponseAsServer();
  }

  /**
   * 验证二进制与文本帧创建路径。
   *
   * @throws Exception 上游测试执行失败时抛出
   */
  @Test
  public void verifiesFrameCreationPaths() throws Exception {
    upstream.createFramesBinary();
    upstream.createFramesText();
  }

  /**
   * 验证上游测试专用扩展以运行时类型生成稳定的哈希值。
   *
   * @throws Exception 反射创建私有测试扩展失败时抛出
   */
  @Test
  public void verifiesTestExtensionHashCode() throws Exception {
    Class<?> extensionClass = Class.forName(Draft_6455Test.class.getName() + "$TestExtension");
    Constructor<?> constructor = extensionClass.getDeclaredConstructor();
    constructor.setAccessible(true);
    Object extension = constructor.newInstance();

    assertEquals(extensionClass.hashCode(), extension.hashCode());
  }
}
