package com.ruoyi.framework.config;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.ruoyi.common.core.domain.entity.SysDictData;
import com.ruoyi.common.utils.poi.ExcelUtil;
import java.io.ByteArrayInputStream;
import java.util.List;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.ss.usermodel.WorkbookFactory;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletResponse;

class ExcelPoiCompatibilityTest
{
    @Test
    void exportsReadableXlsxUsingUpgradedPoi() throws Exception
    {
        SysDictData item = new SysDictData();
        item.setDictCode(42L);
        item.setDictLabel("Synthetic label");
        item.setDictValue("synthetic-value");
        item.setDictType("disposable-test");
        item.setStatus("0");
        MockHttpServletResponse response = new MockHttpServletResponse();

        new ExcelUtil<>(SysDictData.class).exportExcel(response, List.of(item), "dictionary");
        byte[] bytes = response.getContentAsByteArray();
        assertTrue(bytes.length > 1000, "A real XLSX workbook should be written");
        try (Workbook workbook = WorkbookFactory.create(new ByteArrayInputStream(bytes)))
        {
            assertEquals("dictionary", workbook.getSheetAt(0).getSheetName());
            boolean found = false;
            for (var row : workbook.getSheetAt(0))
            {
                for (var cell : row)
                {
                    if ("Synthetic label".equals(cell.toString())) found = true;
                }
            }
            assertTrue(found, "Exported row must survive POI parsing");
        }
    }
}
