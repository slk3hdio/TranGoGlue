package dev.failsafe.internal;

import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import dev.failsafe.RateLimitExceededException;
import dev.failsafe.RateLimiter;
import dev.failsafe.spi.ExecutionResult;
import dev.failsafe.spi.FailsafeFuture;
import dev.failsafe.spi.PolicyExecutor;
import dev.failsafe.spi.Scheduler;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import java.util.function.BiConsumer;
import org.junit.Test;

/**
 * RateLimiterExecutor 的附加行为测试，覆盖同步与异步的许可获取结果。
 */
public class RateLimiterExecutorAdditionalTest {

  /**
   * 记录策略取消回调的 future，用于验证异步许可等待的取消传播。
   */
  private static class RecordingFuture extends FailsafeFuture<Object> {
    private BiConsumer<Boolean, ExecutionResult<Object>> cancelFunction;

    /**
     * 创建不执行完成副作用的记录 future。
     */
    RecordingFuture() {
      super((result, context) -> { });
    }

    /**
     * 保存策略注册的取消回调。
     *
     * @param policyExecutor 注册回调的策略执行器
     * @param cancelFunction 取消时应执行的回调
     */
    @Override
    public synchronized void setCancelFn(PolicyExecutor<Object> policyExecutor,
      BiConsumer<Boolean, ExecutionResult<Object>> cancelFunction) {
      this.cancelFunction = cancelFunction;
      super.setCancelFn(policyExecutor, cancelFunction);
    }
  }

  /**
   * 创建零等待时间的平滑限流器。
   *
   * @return 首个许可立即可用的限流器实现
   */
  @SuppressWarnings("unchecked")
  private RateLimiterImpl<Object> newLimiter() {
    return (RateLimiterImpl<Object>) RateLimiter.<Object>smoothBuilder(Duration.ofSeconds(1)).build();
  }

  /**
   * 验证首个同步许可成功，而紧邻的第二次请求被拒绝。
   */
  @Test
  public void preExecuteReturnsRateLimitFailureAfterPermitIsConsumed() {
    RateLimiterExecutor<Object> executor = new RateLimiterExecutor<>(newLimiter(), 0);

    assertNull(executor.preExecute());
    ExecutionResult<Object> rejected = executor.preExecute();

    assertTrue(rejected.getException() instanceof RateLimitExceededException);
  }

  /**
   * 验证异步预执行在无可用许可时立即返回限流异常。
   *
   * @throws Exception 异步结果未能正常完成时抛出
   */
  @Test
  public void preExecuteAsyncReturnsRateLimitFailure() throws Exception {
    RateLimiterImpl<Object> limiter = newLimiter();
    assertTrue(limiter.tryAcquirePermit());
    RateLimiterExecutor<Object> executor = new RateLimiterExecutor<>(limiter, 0);
    FailsafeFuture<Object> future = new FailsafeFuture<>((result, context) -> { });

    ExecutionResult<Object> rejected = executor.preExecuteAsync(Scheduler.DEFAULT, future)
      .get(5, TimeUnit.SECONDS);

    assertTrue(rejected.getException() instanceof RateLimitExceededException);
  }

  /**
   * 验证异步许可成功信号以及取消回调都能完成等待 promise。
   *
   * @throws Exception 异步结果未能正常完成时抛出
   */
  @Test
  public void preExecuteAsyncCompletesAndPropagatesCancellation() throws Exception {
    RateLimiterExecutor<Object> executor = new RateLimiterExecutor<>(newLimiter(), 0);
    RecordingFuture future = new RecordingFuture();

    ExecutionResult<Object> result = executor.preExecuteAsync(Scheduler.DEFAULT, future)
      .get(5, TimeUnit.SECONDS);
    assertTrue(result.isNonResult());
    assertTrue(future.cancelFunction != null);

    future.cancelFunction.accept(false, ExecutionResult.none());
  }
}
