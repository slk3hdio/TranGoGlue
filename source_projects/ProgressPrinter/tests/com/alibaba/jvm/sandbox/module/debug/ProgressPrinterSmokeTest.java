package com.alibaba.jvm.sandbox.module.debug;

import com.alibaba.jvm.sandbox.api.http.printer.Printer;
import org.junit.Test;

import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/**
 * ProgressPrinter 冒烟测试: 用记录型匿名 Printer 捕获输出,
 * 验证 begin/progressOnSuccess/progressOnFailed/finish 都调用了 Printer。
 */
public class ProgressPrinterSmokeTest {

    /**
     * 记录型 Printer: 捕获 print/println 输出并记录 flush 次数。
     */
    static class RecordingPrinter implements Printer {

        final StringBuilder out = new StringBuilder();
        int flushCount = 0;
        boolean broken = false;

        @Override
        public Printer print(String string) {
            out.append(string);
            return this;
        }

        @Override
        public Printer println(String string) {
            out.append(string).append("\n");
            return this;
        }

        @Override
        public Printer flush() {
            flushCount++;
            return this;
        }

        @Override
        public Printer waitingForBroken() {
            return this;
        }

        @Override
        public boolean waitingForBroken(long time, TimeUnit unit) {
            return false;
        }

        @Override
        public Printer broken() {
            broken = true;
            return this;
        }

        @Override
        public boolean isBroken() {
            return broken;
        }

        @Override
        public void close() {
        }
    }

    /**
     * 统计输出中 '#' 字符的数量(进度条宽度)。
     */
    private static int countHashes(final String s) {
        int count = 0;
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == '#') {
                count++;
            }
        }
        return count;
    }

    @Test
    public void begin_callsPrinterPrint() {
        final RecordingPrinter printer = new RecordingPrinter();
        new ProgressPrinter(printer).begin(10);
        assertTrue(printer.out.toString().contains("%s["));
    }

    @Test
    public void progressOnSuccess_callsPrinterPrintAndFlush() {
        final RecordingPrinter printer = new RecordingPrinter();
        final ProgressPrinter progressPrinter = new ProgressPrinter(printer);

        progressPrinter.begin(10);
        progressPrinter.progressOnSuccess(String.class, 5);

        // rate = (int)(5 * 50 * 1f / 10) = 25
        assertEquals(25, countHashes(printer.out.toString()));
        assertEquals(1, printer.flushCount);
    }

    @Test
    public void progressOnFailed_callsPrinterPrintAndFlush() {
        final RecordingPrinter printer = new RecordingPrinter();
        final ProgressPrinter progressPrinter = new ProgressPrinter(printer);

        progressPrinter.begin(10);
        progressPrinter.progressOnFailed(String.class, 5, new IllegalStateException("boom"));

        assertEquals(25, countHashes(printer.out.toString()));
        assertEquals(1, printer.flushCount);
    }

    @Test
    public void finish_callsPrinterPrintln() {
        final RecordingPrinter printer = new RecordingPrinter();
        new ProgressPrinter(printer).finish(3, 7);
        assertTrue(printer.out.toString().contains("FINISH(cCnt=3,mCnt=7)"));
    }

    @Test
    public void progress_whenBroken_skipsOutput() {
        final RecordingPrinter printer = new RecordingPrinter();
        final ProgressPrinter progressPrinter = new ProgressPrinter(printer);

        printer.broken();
        progressPrinter.begin(10);
        progressPrinter.progressOnSuccess(String.class, 5);

        // isBroken() 后 progress() 直接返回: 只有 begin 的输出, 没有 flush
        assertEquals("%s[", printer.out.toString());
        assertEquals(0, printer.flushCount);
    }

    @Test
    public void ctorWithPrefixAndWidth_formatsProgressBar() {
        final RecordingPrinter printer = new RecordingPrinter();
        final ProgressPrinter progressPrinter = new ProgressPrinter("P>", 10, printer);

        progressPrinter.begin(100);
        progressPrinter.progressOnSuccess(String.class, 10);

        // rate = (int)(10 * 10 * 1f / 100) = 1
        final String out = printer.out.toString();
        assertTrue(out.contains("P>["));
        assertEquals(1, countHashes(out));
    }

}
