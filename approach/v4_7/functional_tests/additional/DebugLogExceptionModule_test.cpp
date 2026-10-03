// SITP_TEST_COUNT: 1

#include <memory>
#include <string>
#include <vector>

#define private public
#include "DebugLogExceptionModule.h"
#undef private

#include "cpp_test_harness.h"

/** 记录模块注册参数的事件观察器。 */
class RecordingWatcher : public ModuleEventWatcher {
public:
    int watchCount = 0;
    EventListener* listener = nullptr;
    std::vector<Event::Type> eventTypes;

    /** 记录普通过滤器和进度形式的注册。 */
    int watch(Filter*, EventListener* eventListener, Progress*,
              const std::vector<Event::Type>& types) override {
        listener = eventListener;
        eventTypes = types;
        ++watchCount;
        return 1;
    }

    /** 记录普通过滤器形式的注册。 */
    int watch(Filter*, EventListener* eventListener,
              const std::vector<Event::Type>& types) override {
        listener = eventListener;
        eventTypes = types;
        ++watchCount;
        return 1;
    }

    /** 记录扩展条件形式的注册。 */
    int watch(EventWatchCondition*, EventListener* eventListener, Progress*,
              const std::vector<Event::Type>& types) override {
        listener = eventListener;
        eventTypes = types;
        ++watchCount;
        return 1;
    }

    /** 删除带进度的观察任务。 */
    void deleteWatcher(int, Progress*) override {}

    /** 删除观察任务。 */
    void deleteWatcher(int) override {}

    /** 执行带进度的临时观察。 */
    void watching(Filter*, EventListener*, Progress*, WatchCallback*, Progress*,
                  const std::vector<Event::Type>&) override {}

    /** 执行普通临时观察。 */
    void watching(Filter*, EventListener*, WatchCallback*,
                  const std::vector<Event::Type>&) override {}
};

/** 验证加载完成时注册 BEFORE 事件监听器。 */
void testRegistersBeforeListener() {
    RecordingWatcher watcher;
    DebugLogExceptionModule module;
    module.moduleEventWatcher = &watcher;

    module.loadCompleted();

    SITP_ASSERT_EQ(1, watcher.watchCount);
    SITP_ASSERT_TRUE(watcher.listener != nullptr);
    SITP_ASSERT_EQ(static_cast<std::size_t>(1), watcher.eventTypes.size());
    SITP_ASSERT_EQ(Event::Type::BEFORE, watcher.eventTypes.front());
}

/** 组装并执行异常日志模块附加测试。 */
int main() {
    return sitp_test::runAll({
        {"registers_before_listener", testRegistersBeforeListener},
    });
}
