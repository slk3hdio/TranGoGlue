// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ReadRowHolder.h"

#include <map>
#include <vector>

/** 创建具有确定初始状态的行上下文。 */
ReadRowHolder makeHolder() {
    return ReadRowHolder(3, RowTypeEnum{}, GlobalConfiguration{}, std::map<int, Cell>{});
}

/** 验证行号可以读取并往返修改。 */
void testRowIndexRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_EQ(3, holder.getRowIndex());
    holder.setRowIndex(9);
    SITP_ASSERT_EQ(9, holder.getRowIndex());
}

/** 验证单元格映射初始化为空并可整体替换。 */
void testCellMapRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_TRUE(holder.getCellMap().empty());
    std::map<int, Cell> cells;
    cells.emplace(2, Cell{});
    holder.setCellMap(cells);
    SITP_ASSERT_EQ(std::size_t{1}, holder.getCellMap().size());
    SITP_ASSERT_TRUE(holder.getCellMap().find(2) != holder.getCellMap().end());
}

/** 验证当前行分析结果默认为空且保持指针身份。 */
void testAnalysisResultRoundTrip() {
    ReadRowHolder holder = makeHolder();
    SITP_ASSERT_TRUE(holder.getCurrentRowAnalysisResult() == nullptr);
    int marker = 7;
    holder.setCurrentRowAnalysisResult(&marker);
    SITP_ASSERT_TRUE(holder.getCurrentRowAnalysisResult() == &marker);
}

/** 验证配置对象和行类型经过 setter 后仍可读回。 */
void testMetadataRoundTrip() {
    ReadRowHolder holder = makeHolder();
    holder.setGlobalConfiguration(GlobalConfiguration{});
    holder.setRowType(RowTypeEnum{});
    (void)holder.getGlobalConfiguration();
    (void)holder.getRowType();
    (void)holder.holderType();
    SITP_ASSERT_EQ(3, holder.getRowIndex());
}

/** 组装并执行行上下文功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"row_index_round_trip", testRowIndexRoundTrip},
        {"cell_map_round_trip", testCellMapRoundTrip},
        {"analysis_result_round_trip", testAnalysisResultRoundTrip},
        {"metadata_round_trip", testMetadataRoundTrip},
    };
    return sitp_test::runAll(tests);
}
