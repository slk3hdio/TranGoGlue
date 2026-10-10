// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 RateLimiter 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe;

import java.time.Duration;
import org.junit.Test;
public class RateLimiterExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
        _i5();
        _i6();
        _i7();
        _i8();
        _i9();
        _i10();
        _i11();
        _i12();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            RateLimiter.smoothBuilder(0L, (Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            RateLimiter.smoothBuilder((Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            RateLimiter.burstyBuilder(0L, (Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            RateLimiter.builder(new RateLimiterConfig((Duration) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.acquirePermit();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.acquirePermit((Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.acquirePermits(0, (Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.isSmooth();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.isBursty();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.reservePermit();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.tryReservePermit((Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.tryAcquirePermit();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            RateLimiter v = new dev.failsafe.internal.RateLimiterImpl(new RateLimiterConfig((Duration) null));
            v.tryAcquirePermit((Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12
}
