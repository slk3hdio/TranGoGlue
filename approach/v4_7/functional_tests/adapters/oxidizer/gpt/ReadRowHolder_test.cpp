// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ReadRowHolder.h"
#include "GlobalConfiguration.h"

#include <cstddef>
#include <map>
#include <memory>
#include <vector>

/** 创建 GPT Oxidizer 的行上下文；该模型使用 size_t 和 GlobalConfiguration 智能指针。 */
ReadRowHolder makeHolder() {
    return ReadRowHolder(
        std::size_t{3},
        RowTypeEnum{},
        std::make_shared<GlobalConfiguration>(),
        std::map<std::size_t, std::shared_ptr<Cell>>{}
    );
}

/** 验证行号可以读取并往返修改。 */
void testRowIndexRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_EQ(std::size_t{3}, holder.getRowIndex());
    holder.setRowIndex(std::size_t{9});
    SITP_ASSERT_EQ(std::size_t{9}, holder.getRowIndex());
}

/** 验证单元格映射初始化为空并可整体替换。 */
void testCellMapRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_TRUE(holder.getCellMap().empty());
    std::map<std::size_t, std::shared_ptr<Cell>> cells;
    holder.setCellMap(cells);
    SITP_ASSERT_TRUE(holder.getCellMap().empty());
}

/** 验证当前行分析结果默认为空且可以保存共享对象。 */
void testAnalysisResultRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_TRUE(holder.getCurrentRowAnalysisResult() == nullptr);
    auto marker = std::make_shared<int>(7);
    holder.setCurrentRowAnalysisResult(marker);
    SITP_ASSERT_TRUE(holder.getCurrentRowAnalysisResult().get() == marker.get());
}

/** 验证配置对象和行类型经过 setter 后仍可读取。 */
void testMetadataRoundTrip() {
    ReadRowHolder holder = makeHolder();
    holder.setGlobalConfiguration(std::make_shared<GlobalConfiguration>());
    holder.setRowType(RowTypeEnum{});
    (void)holder.getGlobalConfiguration();
    (void)holder.getRowType();
    (void)holder.holderType();
    SITP_ASSERT_EQ(std::size_t{3}, holder.getRowIndex());
}

/** 组装并执行 GPT Oxidizer 的行上下文适配测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"row_index_round_trip", testRowIndexRoundTrip},
        {"cell_map_round_trip", testCellMapRoundTrip},
        {"analysis_result_round_trip", testAnalysisResultRoundTrip},
        {"metadata_round_trip", testMetadataRoundTrip},
    };
    return sitp_test::runAll(tests);
}
