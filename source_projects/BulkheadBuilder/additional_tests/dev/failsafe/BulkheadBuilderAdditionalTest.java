package dev.failsafe;

import static org.junit.Assert.assertEquals;

import java.time.Duration;
import org.junit.Test;

/**
 * BulkheadBuilder 的附加行为测试，验证从已有配置创建构建器时的防御性复制。
 */
public class BulkheadBuilderAdditionalTest {

  /**
   * 验证构造器复制配置，后续修改源配置不会污染构建结果。
   */
  @Test
  public void constructorCopiesExistingConfig() {
    BulkheadConfig<Object> source = new BulkheadConfig<>(2);
    source.maxWaitTime = Duration.ofSeconds(3);

    BulkheadBuilder<Object> builder = new BulkheadBuilder<>(source);
    source.maxConcurrency = 9;
    source.maxWaitTime = Duration.ZERO;

    BulkheadConfig<Object> actual = builder.build().getConfig();
    assertEquals(2, actual.getMaxConcurrency());
    assertEquals(Duration.ofSeconds(3), actual.getMaxWaitTime());
  }
}
