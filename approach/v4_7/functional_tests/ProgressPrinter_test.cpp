// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ProgressPrinter.h"

#include <chrono>
#include <string>
#include <vector>

/** 记录 ProgressPrinter 对 Printer 的可观察调用。 */
class RecordingPrinter final : public Printer {
public:
    std::string output;
    int flushCount = 0;
    bool brokenState = false;

    /** 追加不换行文本并返回当前打印器。 */
    Printer& print(const std::string& value) override {
        output += value;
        return *this;
    }

    /** 追加一行文本并返回当前打印器。 */
    Printer& println(const std::string& value) override {
        output += value + "\n";
        return *this;
    }

    /** 记录刷新操作并返回当前打印器。 */
    Printer& flush() override {
        ++flushCount;
        return *this;
    }

    /** 保持链式等待接口。 */
    Printer& waitingForBroken() override {
        return *this;
    }

    /** 返回当前是否已中断。 */
    bool waitingForBroken(long long, std::chrono::nanoseconds) override {
        return brokenState;
    }

    /** 标记打印器中断并返回当前实例。 */
    Printer& broken() override {
        brokenState = true;
        return *this;
    }

    /** 查询打印器中断状态。 */
    bool isBroken() override {
        return brokenState;
    }

    /** 关闭记录型打印器。 */
    void close() override {}
};

/** 统计输出中的进度标记数量。 */
int countHashes(const std::string& value) {
    int count = 0;
    for (char character : value) {
        if (character == '#') {
            ++count;
        }
    }
    return count;
}

/** 验证成功进度按比例输出并刷新。 */
void testProgressAndFlush() {
    RecordingPrinter printer;
    ProgressPrinter progress(&printer);
    progress.begin(10);
    progress.progressOnSuccess(nullptr, 5);
    SITP_ASSERT_EQ(25, countHashes(printer.output));
    SITP_ASSERT_EQ(1, printer.flushCount);
}

/** 验证自定义前缀和宽度参与进度条格式化。 */
void testPrefixAndWidth() {
    RecordingPrinter printer;
    ProgressPrinter progress("P>", 10, &printer);
    progress.begin(100);
    progress.progressOnSuccess(nullptr, 10);
    SITP_ASSERT_TRUE(printer.output.find("P>[") != std::string::npos);
    SITP_ASSERT_EQ(1, countHashes(printer.output));
}

/** 验证结束信息包含类和方法计数。 */
void testFinishMessage() {
    RecordingPrinter printer;
    ProgressPrinter(&printer).finish(3, 7);
    SITP_ASSERT_TRUE(printer.output.find("FINISH(cCnt=3,mCnt=7)") != std::string::npos);
}

/** 验证打印器中断后不再输出或刷新进度。 */
void testBrokenPrinterSkipsProgress() {
    RecordingPrinter printer;
    ProgressPrinter progress(&printer);
    printer.broken();
    progress.begin(10);
    const std::string before = printer.output;
    progress.progressOnSuccess(nullptr, 5);
    SITP_ASSERT_EQ(before, printer.output);
    SITP_ASSERT_EQ(0, printer.flushCount);
}

/** 组装并执行进度打印功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"progress_and_flush", testProgressAndFlush},
        {"prefix_and_width", testPrefixAndWidth},
        {"finish_message", testFinishMessage},
        {"broken_skips_progress", testBrokenPrinterSkipsProgress},
    };
    return sitp_test::runAll(tests);
}
