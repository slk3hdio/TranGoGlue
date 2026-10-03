// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ReadSheetHolder.h"

#include <string>
#include <vector>

/** 创建最小可用的工作表上下文。 */
ReadSheetHolder makeSheetHolder() {
    return ReadSheetHolder(ReadSheet(0, "Sheet1"), ReadWorkbookHolder(ReadWorkbook{}));
}

/** 验证构造函数复制工作表编号和名称。 */
void testConstructorCopiesMetadata() {
    ReadSheetHolder holder = makeSheetHolder();
    SITP_ASSERT_EQ(0, holder.getSheetNo());
    SITP_ASSERT_EQ(std::string("Sheet1"), holder.getSheetName());
    SITP_ASSERT_EQ(-1, holder.getRowIndex());
    SITP_ASSERT_TRUE(holder.getCellMap().empty());
}

/** 验证估算总行数同时驱动 getTotal。 */
void testTotalTracksApproximateRows() {
    ReadSheetHolder holder = makeSheetHolder();
    holder.setApproximateTotalRowNumber(42);
    SITP_ASSERT_EQ(42, holder.getApproximateTotalRowNumber());
    SITP_ASSERT_EQ(42, holder.getTotal());
}

/** 验证工作表自身字段可以往返修改。 */
void testOwnFieldRoundTrip() {
    ReadSheetHolder holder = makeSheetHolder();
    holder.setSheetNo(7);
    holder.setSheetName("Renamed");
    holder.setRowIndex(5);
    SITP_ASSERT_EQ(7, holder.getSheetNo());
    SITP_ASSERT_EQ(std::string("Renamed"), holder.getSheetName());
    SITP_ASSERT_EQ(5, holder.getRowIndex());
}

/** 验证构造后继承的读取状态已经初始化。 */
void testInheritedStateInitialized() {
    ReadSheetHolder holder = makeSheetHolder();
    SITP_ASSERT_EQ(1, holder.getHeadRowNumber());
    SITP_ASSERT_TRUE(holder.isNew());
    (void)holder.holderType();
}

/** 组装并执行工作表上下文功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"constructor_copies_metadata", testConstructorCopiesMetadata},
        {"total_tracks_approximate_rows", testTotalTracksApproximateRows},
        {"own_field_round_trip", testOwnFieldRoundTrip},
        {"inherited_state_initialized", testInheritedStateInitialized},
    };
    return sitp_test::runAll(tests);
}
