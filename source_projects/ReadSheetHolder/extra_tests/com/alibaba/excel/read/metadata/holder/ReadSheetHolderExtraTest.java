// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ReadSheetHolder 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.excel.read.metadata.holder;

import java.util.LinkedHashMap;
import java.util.Map;
import com.alibaba.excel.enums.HolderEnum;
import com.alibaba.excel.metadata.Cell;
import com.alibaba.excel.metadata.CellExtra;
import com.alibaba.excel.metadata.data.ReadCellData;
import com.alibaba.excel.read.metadata.ReadSheet;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.junit.Test;
public class ReadSheetHolderExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new ReadSheetHolder(new com.alibaba.excel.read.metadata.ReadSheet(), (ReadWorkbookHolder) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            ReadSheetHolder v = new ReadSheetHolder(new com.alibaba.excel.read.metadata.ReadSheet(), (ReadWorkbookHolder) null);
            v.getTotal();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ReadSheetHolder v = new ReadSheetHolder(new com.alibaba.excel.read.metadata.ReadSheet(), (ReadWorkbookHolder) null);
            v.holderType();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2
}
