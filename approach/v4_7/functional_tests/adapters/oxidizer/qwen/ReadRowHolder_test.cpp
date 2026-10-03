// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ReadRowHolder.h"

#include <any>
#include <cstdint>
#include <map>
#include <vector>

/** 创建 Qwen Oxidizer 的行上下文；该模型使用命名空间类型和裸指针单元格。 */
ReadRowHolder makeHolder() {
    return ReadRowHolder(
        std::int32_t{3},
        com_alibaba_easyexcel::RowTypeEnum{},
        com_alibaba_easyexcel::GlobalConfiguration{},
        std::map<std::int32_t, Cell*>{}
    );
}

/** 验证行号可以读取并往返修改。 */
void testRowIndexRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_EQ(std::int32_t{3}, holder.getRowIndex());
    holder.setRowIndex(std::int32_t{9});
    SITP_ASSERT_EQ(std::int32_t{9}, holder.getRowIndex());
}

/** 验证单元格映射初始化为空并可整体替换。 */
void testCellMapRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_TRUE(holder.getCellMap().empty());
    std::map<std::int32_t, Cell*> cells;
    holder.setCellMap(cells);
    SITP_ASSERT_TRUE(holder.getCellMap().empty());
}

/** 验证 any 类型的当前行分析结果可以保存值。 */
void testAnalysisResultRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_FALSE(holder.getCurrentRowAnalysisResult().has_value());
    holder.setCurrentRowAnalysisResult(std::any{7});
    SITP_ASSERT_TRUE(holder.getCurrentRowAnalysisResult().has_value());
}

/** 验证配置对象和行类型经过 setter 后仍可读取。 */
void testMetadataRoundTrip() {
    ReadRowHolder holder = makeHolder();
    holder.setGlobalConfiguration(com_alibaba_easyexcel::GlobalConfiguration{});
    holder.setRowType(com_alibaba_easyexcel::RowTypeEnum{});
    (void)holder.getGlobalConfiguration();
    (void)holder.getRowType();
    (void)holder.holderType();
    SITP_ASSERT_EQ(std::int32_t{3}, holder.getRowIndex());
}

/** 组装并执行 Qwen Oxidizer 的行上下文适配测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"row_index_round_trip", testRowIndexRoundTrip},
        {"cell_map_round_trip", testCellMapRoundTrip},
        {"analysis_result_round_trip", testAnalysisResultRoundTrip},
        {"metadata_round_trip", testMetadataRoundTrip},
    };
    return sitp_test::runAll(tests);
}
