// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"

#include "Appendable.h"
#include "Cell.h"
#include "Charset.h"
#include "CsvWorkbook.h"
#include "CsvSheet.h"
#include "Locale.h"
#include "Row.h"
#include "String.h"

#include <memory>
#include <string>

/**
 * Java StringBuilder 的薄适配：实现 Appendable 接口，把内容追加到内部 std::string。
 * 仅用于满足 CsvWorkbook 构造参数的 shared_ptr<Appendable> 形态。
 */
class StringBuilderAdapter : public Appendable {
private:
    std::string buffer;

public:
    Appendable& append(const char* str) override {
        if (str != nullptr) {
            buffer += str;
        }
        return *this;
    }

    Appendable& append(const char* str, size_t start, size_t end) override {
        if (str != nullptr && end >= start) {
            buffer.append(str + start, end - start);
        }
        return *this;
    }

    Appendable& append(char c) override {
        buffer += c;
        return *this;
    }

    const std::string& str() const { return buffer; }
};

/**
 * 构造与 Java 测试一致的 CsvWorkbook（Locale.ROOT、UTF-8、无 BOM、无 1904 窗口）。
 * @param out 输出目标。
 * @return 构造完成的工作簿。
 */
static std::shared_ptr<CsvWorkbook> makeWorkbook(const std::shared_ptr<Appendable>& out) {
    Locale rootLocale(String(""));
    Charset utf8 = Charset::forName(String("UTF-8"));
    return std::make_shared<CsvWorkbook>(out, rootLocale, false, false, utf8, false);
}

/** 验证创建工作表返回非空对象。 */
void testCreateSheetNotNull() {
    auto output = std::make_shared<StringBuilderAdapter>();
    auto workbook = makeWorkbook(output);
    SITP_ASSERT_TRUE(workbook->createSheet() != nullptr);
}

/** 验证工作簿保留输出目标并持有已创建的工作表。 */
void testWorkbookRetainsOutAndSheet() {
    auto output = std::make_shared<StringBuilderAdapter>();
    auto workbook = makeWorkbook(output);
    workbook->createSheet();
    SITP_ASSERT_TRUE(workbook->getOut().get() == output.get());
    SITP_ASSERT_TRUE(workbook->getCsvSheet() != nullptr);
}

/** 验证行和单元格记录索引及字符串值。 */
void testRowAndCellRetainIndicesAndValue() {
    auto workbook = makeWorkbook(std::make_shared<StringBuilderAdapter>());
    Row* row = workbook->createSheet()->createRow(0);
    SITP_ASSERT_TRUE(row != nullptr);
    Cell* cell = row->createCell(0);
    SITP_ASSERT_TRUE(cell != nullptr);
    String value("value");
    cell->setCellValue(&value);
    SITP_ASSERT_EQ(0, row->getRowNum());
    SITP_ASSERT_EQ(0, cell->getColumnIndex());
    SITP_ASSERT_EQ(std::string("value"), cell->getStringCellValue().std_str());
}

/** 组装并运行 CsvWorkbook 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"create_sheet_not_null", testCreateSheetNotNull},
        {"workbook_retains_out_and_sheet", testWorkbookRetainsOutAndSheet},
        {"row_and_cell_retain_indices_and_value", testRowAndCellRetainIndicesAndValue},
    };
    return sitp_test::runAll(tests);
}
