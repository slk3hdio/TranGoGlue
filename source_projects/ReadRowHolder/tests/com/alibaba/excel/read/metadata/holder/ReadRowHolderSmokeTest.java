package com.alibaba.excel.read.metadata.holder;

import java.util.HashMap;
import java.util.Map;

import com.alibaba.excel.enums.HolderEnum;
import com.alibaba.excel.enums.RowTypeEnum;
import com.alibaba.excel.metadata.Cell;
import com.alibaba.excel.metadata.GlobalConfiguration;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

/**
 * JUnit 4 smoke test for the fragment class {@link ReadRowHolder}.
 *
 * <p>Tests the public constructor and the getter/setter round trips plus {@code holderType()}.
 */
public class ReadRowHolderSmokeTest {

    private static ReadRowHolder newHolder() {
        return new ReadRowHolder(3, RowTypeEnum.DATA, new GlobalConfiguration(),
            new HashMap<Integer, Cell>());
    }

    @Test
    public void holderTypeIsRow() {
        assertEquals(HolderEnum.ROW, newHolder().holderType());
    }

    @Test
    public void rowIndexRoundTrip() {
        ReadRowHolder holder = newHolder();
        assertEquals(Integer.valueOf(3), holder.getRowIndex());
        holder.setRowIndex(9);
        assertEquals(Integer.valueOf(9), holder.getRowIndex());
    }

    @Test
    public void rowTypeRoundTrip() {
        ReadRowHolder holder = newHolder();
        assertEquals(RowTypeEnum.DATA, holder.getRowType());
        holder.setRowType(RowTypeEnum.EMPTY);
        assertEquals(RowTypeEnum.EMPTY, holder.getRowType());
    }

    @Test
    public void cellMapRoundTrip() {
        ReadRowHolder holder = newHolder();
        assertNotNull(holder.getCellMap());
        assertTrue(holder.getCellMap().isEmpty());

        Map<Integer, Cell> cells = new HashMap<Integer, Cell>();
        cells.put(0, new Cell() {
            @Override
            public Integer getRowIndex() {
                return 3;
            }

            @Override
            public Integer getColumnIndex() {
                return 0;
            }
        });
        holder.setCellMap(cells);
        assertSame(cells, holder.getCellMap());
        assertEquals(Integer.valueOf(0), holder.getCellMap().get(0).getColumnIndex());
    }

    @Test
    public void globalConfigurationAndAnalysisResultRoundTrip() {
        ReadRowHolder holder = newHolder();
        assertNotNull(holder.getGlobalConfiguration());
        assertNull(holder.getCurrentRowAnalysisResult());

        GlobalConfiguration config = new GlobalConfiguration();
        config.setAutoTrim(Boolean.FALSE);
        holder.setGlobalConfiguration(config);
        assertSame(config, holder.getGlobalConfiguration());
        assertEquals(Boolean.FALSE, holder.getGlobalConfiguration().getAutoTrim());

        Object result = new Object();
        holder.setCurrentRowAnalysisResult(result);
        assertSame(result, holder.getCurrentRowAnalysisResult());
    }
}
