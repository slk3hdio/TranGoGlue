// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ProgressPrinter 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.module.debug;

import com.alibaba.jvm.sandbox.api.http.printer.Printer;
import com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher;
import org.apache.commons.lang3.StringUtils;
import org.junit.Test;
public class ProgressPrinterExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
        _i5();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new ProgressPrinter((com.alibaba.jvm.sandbox.api.http.printer.Printer) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            new ProgressPrinter("", 0, (com.alibaba.jvm.sandbox.api.http.printer.Printer) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ProgressPrinter v = new ProgressPrinter((com.alibaba.jvm.sandbox.api.http.printer.Printer) null);
            v.begin(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ProgressPrinter v = new ProgressPrinter((com.alibaba.jvm.sandbox.api.http.printer.Printer) null);
            v.progressOnSuccess(Object.class, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            ProgressPrinter v = new ProgressPrinter((com.alibaba.jvm.sandbox.api.http.printer.Printer) null);
            v.progressOnFailed(Object.class, 0, (Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            ProgressPrinter v = new ProgressPrinter((com.alibaba.jvm.sandbox.api.http.printer.Printer) null);
            v.finish(0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5
}
