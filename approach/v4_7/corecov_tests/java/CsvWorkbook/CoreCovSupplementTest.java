import com.alibaba.excel.metadata.csv.CsvWorkbook;
import org.apache.poi.ss.usermodel.Sheet;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import org.junit.Test;
import static org.junit.Assert.*;

/** CsvWorkbook核心行为补充测试；仅验证Java语义，不吞掉异常、不修改生产代码。 */
public class CoreCovSupplementTest {
    /** 验证命名创建和工作表检索；无参数，异常使测试失败。 */
    @Test public void namedSheetLookup() throws Exception { CsvWorkbook w = new CsvWorkbook(new StringBuilder(), Locale.ROOT, false, false, StandardCharsets.UTF_8, false); Sheet s = w.createSheet("name"); assertSame(s, w.getSheet("name")); assertSame(s, w.getSheetAt(0)); }
    /** 验证CSV单表接口的固定索引行为；无参数，异常使测试失败。 */
    @Test public void fixedIndices() throws Exception { CsvWorkbook w = new CsvWorkbook(new StringBuilder(), Locale.ROOT, false, false, StandardCharsets.UTF_8, false); w.setActiveSheet(3); w.setFirstVisibleTab(2); assertEquals(0, w.getActiveSheetIndex()); assertEquals(0, w.getFirstVisibleTab()); }
}
