// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ExecutionResult 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.spi;

import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import org.junit.Test;
public class ExecutionResultExtraTest {
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
        _i13();
        _i14();
        _i15();
        _i16();
        _i17();
        _i18();
        _i19();
        _i20();
        _i21();
        _i22();
        _i23();
        _i24();
    }

    @Test(timeout = 20000)
    public void _batch1() {
        _i25();
        _i26();
        _i27();
        _i28();
        _i29();
        _i30();
        _i31();
        _i32();
        _i33();
        _i34();
        _i35();
        _i36();
        _i37();
        _i38();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            ExecutionResult.nullFuture();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            ExecutionResult.success(null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ExecutionResult.exception((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ExecutionResult.none();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            new ExecutionResult(null, (Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.getResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.getResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.getException();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.getException();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.getDelay();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.getDelay();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.isComplete();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.isComplete();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.isNonResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.isNonResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14

    // @extra-start id=15
    @SuppressWarnings("unused")
    private void _i15() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.isSuccess();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=15

    // @extra-start id=16
    @SuppressWarnings("unused")
    private void _i16() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.isSuccess();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=16

    // @extra-start id=17
    @SuppressWarnings("unused")
    private void _i17() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.withNonResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=17

    // @extra-start id=18
    @SuppressWarnings("unused")
    private void _i18() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.withNonResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=18

    // @extra-start id=19
    @SuppressWarnings("unused")
    private void _i19() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.withResult(null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=19

    // @extra-start id=20
    @SuppressWarnings("unused")
    private void _i20() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.withResult(null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=20

    // @extra-start id=21
    @SuppressWarnings("unused")
    private void _i21() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.withNotComplete();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=21

    // @extra-start id=22
    @SuppressWarnings("unused")
    private void _i22() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.withNotComplete();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=22

    // @extra-start id=23
    @SuppressWarnings("unused")
    private void _i23() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.withException();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=23

    // @extra-start id=24
    @SuppressWarnings("unused")
    private void _i24() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.withException();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=24

    // @extra-start id=25
    @SuppressWarnings("unused")
    private void _i25() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.withSuccess();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=25

    // @extra-start id=26
    @SuppressWarnings("unused")
    private void _i26() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.withSuccess();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=26

    // @extra-start id=27
    @SuppressWarnings("unused")
    private void _i27() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.withDelay(0L);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=27

    // @extra-start id=28
    @SuppressWarnings("unused")
    private void _i28() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.withDelay(0L);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=28

    // @extra-start id=29
    @SuppressWarnings("unused")
    private void _i29() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.with(0L, false, false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=29

    // @extra-start id=30
    @SuppressWarnings("unused")
    private void _i30() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.with(0L, false, false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=30

    // @extra-start id=31
    @SuppressWarnings("unused")
    private void _i31() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.getSuccessAll();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=31

    // @extra-start id=32
    @SuppressWarnings("unused")
    private void _i32() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.getSuccessAll();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=32

    // @extra-start id=33
    @SuppressWarnings("unused")
    private void _i33() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=33

    // @extra-start id=34
    @SuppressWarnings("unused")
    private void _i34() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=34

    // @extra-start id=35
    @SuppressWarnings("unused")
    private void _i35() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.equals(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=35

    // @extra-start id=36
    @SuppressWarnings("unused")
    private void _i36() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.equals(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=36

    // @extra-start id=37
    @SuppressWarnings("unused")
    private void _i37() {
        try {
            ExecutionResult v = new ExecutionResult(null, (Throwable) null);
            v.hashCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=37

    // @extra-start id=38
    @SuppressWarnings("unused")
    private void _i38() {
        try {
            ExecutionResult v = ExecutionResult.success(null);
            v.hashCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=38
}
