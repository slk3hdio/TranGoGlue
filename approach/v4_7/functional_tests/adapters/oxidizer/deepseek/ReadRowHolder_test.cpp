// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ReadRowHolder.h"

#include <cstdint>
#include <map>
#include <memory>
#include <optional>

/** 创建 DeepSeek Oxidizer 的行上下文；该模型使用 optional、值类型配置和 shared_ptr 单元格。 */
ReadRowHolder makeHolder() {
    return ReadRowHolder(
        std::optional<std::int32_t>{3},
        RowTypeEnum{},
        GlobalConfiguration{},
        std::map<std::int32_t, std::shared_ptr<Cell>>{}
    );
}

/** 验证行号可以读取并往返修改。 */
void testRowIndexRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_EQ(3, holder.getRowIndex().value());
    holder.setRowIndex(std::optional<std::int32_t>{9});
    SITP_ASSERT_EQ(9, holder.getRowIndex().value());
}

/** 验证单元格映射初始化为空并可整体替换。 */
void testCellMapRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_TRUE(holder.getCellMap().empty());
    std::map<std::int32_t, std::shared_ptr<Cell>> cells;
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
    holder.setGlobalConfiguration(GlobalConfiguration{});
    holder.setRowType(RowTypeEnum{});
    (void)holder.getGlobalConfiguration();
    (void)holder.getRowType();
    (void)holder.holderType();
    SITP_ASSERT_EQ(3, holder.getRowIndex().value());
}

/** 组装并执行 DeepSeek Oxidizer 的行上下文适配测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"row_index_round_trip", testRowIndexRoundTrip},
        {"cell_map_round_trip", testCellMapRoundTrip},
        {"analysis_result_round_trip", testAnalysisResultRoundTrip},
        {"metadata_round_trip", testMetadataRoundTrip},
    };
    return sitp_test::runAll(tests);
}
